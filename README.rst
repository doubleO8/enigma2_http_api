enigma2_http_api
================

**enigma2_http_api**'s main goal is providing a thin wrapper library for the `Enigma2:WebInterface <https://dream.reichholf.net/wiki/Enigma2:WebInterface>`_.
Using the library may help controlling enigma2 based STBs either from the enigma2 device itself or from a remote host.

Documentation
-------------

The latest online documentation is available `here <http://enigma2-http-api.readthedocs.io/en/latest/>`_.

Installation on enigma2 devices using pip
-----------------------------------------

In order to install **enigma2_http_api** using pip one might take the following steps::

    cd /tmp
    opkg install python-distutils python-xmlrpc python-compile python-unittest python-doctest
    wget https://bootstrap.pypa.io/get-pip.py
    python ./get-pip.py
    pip install enigma2_http_api

