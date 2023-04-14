#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Orka API reference: https://documenter.getpostman.com/view/6574930/S1ETRGzt

import argparse, os
from contextlib import contextmanager
from getpass import getpass
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


USER_AGENT = "voyages-sncf-technologies/orka-tools/orka.py"


@contextmanager
def orka_session(orka_controller, user_email, password, license_key, retries=3, backoff_factor=.3, **_):
    'Setup a session with retry adapters, perform login and configure HTTP auth headers'
    session = SessionWithPrefixUrl(orka_controller)
    adapter = HTTPAdapter(max_retries=Retry(total=retries, read=retries, connect=retries, backoff_factor=backoff_factor))
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    resp = check_http_status(session.post('/token', data={
        'email': user_email,
        'password': password,
    }))
    # print('Token 1 : ' + resp.json()['token'])
    # session.headers.update({
    #     'User-Agent': "UA test token",
    # })
    # resp = check_http_status(session.post('/token', data={
    #     'email': user_email,
    #     'password': password,
    # }))
    # print('Token 2 : ' + resp.json()['token'])
    session.headers.update({
        'Authorization': 'Bearer ' + resp.json()['token'],
        'orka-licensekey': license_key,
        'User-Agent': USER_AGENT,
    })
    # resp = check_http_status(session.get('/token'))
    # print('Token Get : ' + resp.text)
    yield session
    #check_http_status(session.delete('/token'))


def check_http_status(response):
    # Very useful to understand errors -> display the HTTP body in case of a non-200 status:
    if response.status_code not in (200, 201):
        print(response.text)
    response.raise_for_status()
    return response


class SessionWithPrefixUrl(requests.Session):
    # Recipe from: https://github.com/psf/requests/issues/2554#issuecomment-109341010
    def __init__(self, prefix_url):
        self.prefix_url = prefix_url
        super().__init__()

    def request(self, method, url, *args, **kwargs):
        url = urljoin(self.prefix_url, url)
        return super().request(method, url, *args, **kwargs)


def add_common_opts_and_parse_args(parser, argv=None):
    parser.add_argument('--orka-controller', help='Default to $ORKA_CONTROLLER_URL')
    parser.add_argument('--license-key', help='Default to $ORKA_LICENSE_KEY')
    parser.add_argument('--user-email', help='Default to $ORKA_USER_EMAIL')
    args = parser.parse_args(argv)
    if not args.orka_controller:
        args.orka_controller = os.environ.get('ORKA_CONTROLLER_URL')
        if not args.orka_controller:
            parser.error('Neither --orka-controller provided nor $ORKA_CONTROLLER_URL set: aborting')
    if not args.license_key:
        args.license_key = os.environ.get('ORKA_LICENSE_KEY')
        if not args.license_key:
            parser.error('Neither --license-key provided nor $ORKA_LICENSE_KEY set: aborting')
    if not args.user_email:
        args.user_email = os.environ.get('ORKA_USER_EMAIL')
        if not args.user_email:
            parser.error('Neither --user-email provided nor $ORKA_USER_EMAIL set: aborting')
    args.password = os.environ.get('ORKA_PASSWORD') or getpass('$ORKA_PASSWORD not found, please provide it: ')
    return args


class ArgparseHelpFormatter(argparse.RawTextHelpFormatter, argparse.ArgumentDefaultsHelpFormatter):
    pass
