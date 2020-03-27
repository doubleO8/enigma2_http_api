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
    description='enigma2 HTTP API client library',
    long_description="enigma2_http_api's main goal is providing a thin wrapper"
                     " library for the Enigma2 WebInterface. Using the library"
                     " may help controlling enigma2 based STBs either from "
                     "the enigma2 device itself or from a remote host.",
    url="https://github.com/doubleO8/enigma2_http_api",
    packages=['enigma2_http_api'],
    install_requires=[
        'pytz',
        'requests',
        'future==0.18.2',
        'six==1.14.0'
    ],
    scripts=[
        'eha-movie-list.py',
        'eha-timer-list.py',
        'eha-service-list.py',
        'eha-epg-search.py',
        'eha-utility-belt.py',
    ]
)
