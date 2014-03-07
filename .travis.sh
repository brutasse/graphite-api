#! /usr/bin/env bash
set -xe

if [ $TOXENV == "coverage" ]
then
	pip install -r requirements-dev.txt coverage coveralls
	coverage run unittest_main.py
	coveralls
else
	tox -e $TOXENV
fi
