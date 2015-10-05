import logging
import os
import structlog
import traceback
import warnings
import yaml

from flask import make_response
from tzlocal import get_localzone
from importlib import import_module
from structlog.processors import (format_exc_info, JSONRenderer,
                                  KeyValueRenderer)

from .middleware import CORS, TrailingSlash
from .search import IndexSearcher
from .storage import Store
from . import DEBUG

try:
    from logging.config import dictConfig
except ImportError:
    from logutils.dictconfig import dictConfig

if DEBUG:
    processors = (format_exc_info, KeyValueRenderer())
else:
    processors = (format_exc_info, JSONRenderer())

logger = structlog.get_logger()

default_conf = {
    'search_index': '/srv/graphite/index',
    'finders': [
        'graphite_api.finders.whisper.WhisperFinder',
    ],
    'functions': [
        'graphite_api.functions.SeriesFunctions',
        'graphite_api.functions.PieFunctions',
    ],
    'whisper': {
        'directories': [
            '/srv/graphite/whisper',
        ],
    },
    'time_zone': get_localzone().zone,
}
if default_conf['time_zone'] == 'local':  # tzlocal didn't find anything
    default_conf['time_zone'] = 'UTC'


# attributes of a classical log record
NON_EXTRA = set(['module', 'filename', 'levelno', 'exc_text', 'pathname',
                 'lineno', 'msg', 'funcName', 'relativeCreated',
                 'levelname', 'msecs', 'threadName', 'name', 'created',
                 'process', 'processName', 'thread'])


class StructlogFormatter(logging.Formatter):
    def __init__(self, *args, **kwargs):
        self._bound = structlog.BoundLoggerBase(None, processors, {})

    def format(self, record):
        if not record.name.startswith('graphite_api'):
            kw = dict(((k, v) for k, v in record.__dict__.items()
                       if k not in NON_EXTRA))
            kw['logger'] = record.name
            return self._bound._process_event(
                record.levelname.lower(), record.getMessage(), kw)[0]
        return record.getMessage()


def load_by_path(path):
    module, klass = path.rsplit('.', 1)
    finder = import_module(module)
    return getattr(finder, klass)


def error_handler(e):
    return make_response(traceback.format_exc(), 500,
                         {'Content-Type': 'text/plain'})


def configure(app):
    config_file = os.environ.get('GRAPHITE_API_CONFIG',
                                 '/etc/graphite-api.yaml')
    if os.path.exists(config_file):
        with open(config_file) as f:
            config = yaml.safe_load(f)
            config['path'] = config_file
    else:
        warnings.warn("Unable to find configuration file at {0}, using "
                      "default config.".format(config_file))
        config = {}

    configure_logging(config)

    for key, value in list(default_conf.items()):
        config.setdefault(key, value)

    app.statsd = None
    if 'statsd' in config:
        try:
            from statsd import StatsClient
        except ImportError:
            warnings.warn("'statsd' is provided in the configuration but "
                          "the statsd client is not installed. Please `pip "
                          "install statsd`.")
        else:
            c = config['statsd']
            app.statsd = StatsClient(c['host'], c.get('port', 8125))

    app.cache = None
    if 'cache' in config:
        try:
            from flask.ext.cache import Cache
        except ImportError:
            warnings.warn("'cache' is provided in the configuration but "
                          "Flask-Cache is not installed. Please `pip install "
                          "Flask-Cache`.")
        else:
            cache_conf = {'CACHE_DEFAULT_TIMEOUT': 60,
                          'CACHE_KEY_PREFIX': 'graphite-api:'}
            for key, value in config['cache'].items():
                cache_conf['CACHE_{0}'.format(key.upper())] = value
            app.cache = Cache(app, config=cache_conf)

    loaded_config = {'functions': {}}
    for functions in config['functions']:
        loaded_config['functions'].update(load_by_path(functions))

    if 'carbon' in config:
        if 'hashing_keyfunc' in config['carbon']:
            config['carbon']['hashing_keyfunc'] = load_by_path(
                config['carbon']['hashing_keyfunc'])
        else:
            config['carbon']['hashing_keyfunc'] = lambda x: x
    loaded_config['carbon'] = config.get('carbon', None)

    finders = []
    for finder in config['finders']:
        finders.append(load_by_path(finder)(config))
    loaded_config['store'] = Store(finders)
    loaded_config['searcher'] = IndexSearcher(config['search_index'])
    app.config['GRAPHITE'] = loaded_config
    app.config['TIME_ZONE'] = config['time_zone']
    logger.info("configured timezone", timezone=app.config['TIME_ZONE'])

    if 'sentry_dsn' in config:
        try:
            from raven.contrib.flask import Sentry
        except ImportError:
            warnings.warn("'sentry_dsn' is provided in the configuration but "
                          "the sentry client is not installed. Please `pip "
                          "install raven[flask]`.")
        else:
            Sentry(app, dsn=config['sentry_dsn'])

    app.wsgi_app = TrailingSlash(CORS(app.wsgi_app,
                                      config.get('allowed_origins')))
    if config.get('render_errors', True):
        app.errorhandler(500)(error_handler)


def configure_logging(config):
    structlog.configure(processors=processors,
                        logger_factory=structlog.stdlib.LoggerFactory(),
                        wrapper_class=structlog.stdlib.BoundLogger,
                        cache_logger_on_first_use=True)
    config.setdefault('logging', {})
    config['logging'].setdefault('version', 1)
    config['logging'].setdefault('handlers', {})
    config['logging'].setdefault('formatters', {})
    config['logging'].setdefault('loggers', {})
    config['logging']['handlers'].setdefault('raw', {
        'level': 'DEBUG',
        'class': 'logging.StreamHandler',
        'formatter': 'raw',
    })
    config['logging']['loggers'].setdefault('root', {
        'handlers': ['raw'],
        'level': 'DEBUG',
        'propagate': False,
    })
    config['logging']['loggers'].setdefault('graphite_api', {
        'handlers': ['raw'],
        'level': 'DEBUG',
    })
    config['logging']['formatters']['raw'] = {'()': StructlogFormatter}
    dictConfig(config['logging'])
    if 'path' in config:
        logger.info("loading configuration", path=config['path'])
    else:
        logger.info("loading default configuration")
