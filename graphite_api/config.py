import os
import warnings
import yaml

from importlib import import_module

from .middleware import CORS, TrailingSlash
from .search import IndexSearcher
from .storage import Store


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
    'time_zone': 'Europe/Berlin',
}


def load_by_path(path):
    module, klass = path.rsplit('.', 1)
    finder = import_module(module)
    return getattr(finder, klass)


def configure(app):
    config_file = os.environ.get('GRAPHITE_API_CONFIG',
                                 '/etc/graphite-api.conf')
    if os.path.exists(config_file):
        with open(config_file) as f:
            config = yaml.safe_load(f)
    else:
        warnings.warn("Unable to find configuration file at {0}, using "
                      "default config.".format(config_file))
        config = {}

    for key, value in default_conf.items():
        config.setdefault(key, value)

    loaded_config = {'functions': {}, 'finders': []}
    for functions in config['functions']:
        loaded_config['functions'].update(load_by_path(functions))

    finders = []
    for finder in config['finders']:
        finders.append(load_by_path(finder)(config))
    loaded_config['store'] = Store(finders)
    loaded_config['searcher'] = IndexSearcher(config['search_index'])
    app.config['GRAPHITE'] = loaded_config
    app.config['TIME_ZONE'] = config['time_zone']

    if 'sentry_dsn' in config:
        try:
            from raven.contrib.flask import Sentry
        except ImportError:
            warnings.warn("'sentry_dsn' is provided in the configuration the "
                          "sentry client is not installed. Please `pip "
                          "install raven[flask]`.")
        else:
            Sentry(app, dsn=config['sentry_dsn'])
    app.wsgi_app = TrailingSlash(CORS(app.wsgi_app,
                                      config.get('allowed_origins')))
