#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Retrieve all Orka logs from a cluster and dump them into a large JSON file.
It takes a few minutes to complete.
'''

# USAGE: time ./dump_logs.py
# Orka API reference: https://documenter.getpostman.com/view/6574930/S1ETRGzt

import argparse, json, sys

from commons import add_common_opts_and_parse_args, check_http_status, orka_session


def main(argv):
    args = parse_args(argv)
    with orka_session(**vars(args)) as session:
        resp = check_http_status(session.post('/logs/query'))
        with open(args.out_file, 'w', encoding='utf-8') as logs_file:
            json.dump(resp.json(), logs_file, indent=4)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                     description=__doc__, allow_abbrev=False)
    parser.add_argument('--out-file', default='logs.json', help=' ')
    return add_common_opts_and_parse_args(parser, argv)


if __name__ == '__main__':
    main(sys.argv[1:])
