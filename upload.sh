#!/usr/bin/env bash
python setup.py bdist_wheel
python setup.py sdist
twine upload --skip-existing dist/*
