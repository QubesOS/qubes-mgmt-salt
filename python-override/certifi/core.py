"""
certifi.py
~~~~~~~~~~

This module returns the installation location of cacert.pem or its contents.
"""

import os.path

DEBIAN_CA_CERTS_PATH = '/etc/ssl/certs/ca-certificates.crt'

# The RPM-packaged certifi always uses the system certificates
def where() -> str:
    if os.path.exists(DEBIAN_CA_CERTS_PATH):
        return DEBIAN_CA_CERTS_PATH
    return '/etc/pki/tls/certs/ca-bundle.crt'

def contents() -> str:
    with open(where(), encoding='utf=8') as data:
        return data.read()

