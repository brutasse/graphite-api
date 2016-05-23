# coding: utf-8
import sys

from setuptools import setup, find_packages

install_requires = [
    'Flask',
    'PyYAML',
    'cairocffi',
    'pyparsing>=1.5.7',
    'pytz',
    'six',
    'structlog',
    'tzlocal',
]

if sys.version_info < (2, 7):
    install_requires.append('importlib')
    install_requires.append('logutils')
    install_requires.append('ordereddict')

with open('README.rst') as f:
    long_description = f.read()

setup(
    name='graphite-api',
    version='1.1.3',
    url='https://github.com/brutasse/graphite-api',
    author="Bruno Renié, based on Chris Davis's graphite-web",
    author_email='bruno@renie.fr',
    license='Apache Software License 2.0',
    description=('Graphite-web, without the interface. '
                 'Just the rendering HTTP API.'),
    long_description=long_description,
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    install_requires=install_requires,
    extras_require={
        'sentry': ['raven[flask]'],
        'cyanite': ['cyanite'],
        'cache': ['Flask-Cache'],
        'statsd': ['statsd'],
    },
    zip_safe=False,
    platforms='any',
    classifiers=(
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Flask',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'Topic :: Scientific/Engineering :: Visualization',
        'Topic :: System :: Monitoring',
    ),
    test_suite='tests',
)
