#!/usr/bin/env python
# -*- coding: utf-8 -*-
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

import versioneer

setup(
    name='enigma2_http_api',
    author="doubleO8",
    author_email="wb008@hdm-stuttgart.de",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description='enigma2 HTP API client library',
    long_description="",
    url="https://github.com/doubleO8/enigma2_http_api",
    packages=['enigma2_http_api'],
    install_requires=['pytz', 'requests'],
    scripts=[
        'eha-movie-list.py',
        'eha-timer-list.py',
        'eha-service-list.py',
    ]
)
