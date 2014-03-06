# coding: utf-8
import sys

from setuptools import setup, find_packages

install_requires = [
    'Flask',
    'cairocffi',
    'pyparsing',
    'pytz',
    'pyyaml',
    'six',
    'whisper',
]

if sys.version_info < (2, 7):
    install_requires.append('importlib')

setup(
    name='graphite-api',
    version='0.1.0',
    url='https://github.com/brutasse/graphite-api',
    author="Bruno Renié, based on Chris Davis's graphite-web",
    author_email='bruno@renie.fr',
    license='Apache Software License 2.0',
    description=('Graphite-web, without the interface. '
                 'Just the rendering HTTP API.'),
    long_description=open('README.rst').read(),
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    install_requires=install_requires,
    zip_safe=False,
    platforms='any',
    classifiers=(
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
        'Topic :: System :: Monitoring',
    ),
    test_suite='tests',
)
