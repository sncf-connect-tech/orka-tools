#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'Script producing some statistics on logs frequency, based on a logs.json file extraced with dump_logs.py'

# USAGE example:
# $ ./dump_logs.py && ./logs_stats.py --since 2021-05-20
#     #logs: 119894
#     "Requested CPU is not available in the cluster":
#     runner-xcode-12-5-0 27
#     "Successfully deployed VM":
#     runner-xcode-12-5-0 107
#     runner-xcode-12-4-0 18
#     "Successfully deleted VM(s)":
#     runner-xcode-12-5-0 107
#     runner-xcode-12-4-0 15

import argparse, json, sys
import re
from collections import defaultdict
from datetime import datetime


TARGET_MESSAGES = (
    'Requested CPU is not available in the cluster',
    'Successfully deployed VM',
    'Successfully deleted VM(s)',
)


def main(argv=None):
    args = parse_args(argv)

    with open(args.logs_filename) as logs_file:
        logs = json.load(logs_file)['logs']
    print('#logs:', len(logs))

    if args.for_vm:
        for log in logs:
            log_date = datetime.strptime(log['createdAt'][:-5], '%Y-%m-%dT%H:%M:%S')
            if args.since and log_date < args.since:
                continue
            if log['request']['body'].get('orka_vm_name') == args.for_vm:
                print(json.dumps(log, indent=4))
        return

    for vm_deploy_msg in TARGET_MESSAGES:
        vms = defaultdict(int)
        for log in logs:
            log_date = datetime.strptime(log['createdAt'][:-5], '%Y-%m-%dT%H:%M:%S')
            if args.since and log_date < args.since:
                continue
            body = log['response']['body']
            if isinstance(body, dict):
                ok_msg_match = body.get('message') == vm_deploy_msg
                error_msg_match = any(re.match(vm_deploy_msg, error['message']) for error in body.get('errors', []))
                if ok_msg_match or error_msg_match:
                    orka_vm_name = body.get('help', {}).get('required_request_data_for_deploy', {}).get('orka_vm_name') or log['request']['body']['orka_vm_name']
                    vms[orka_vm_name] += 1
        print(f'"{vm_deploy_msg}":')
        for vm_name, count in sorted(vms.items(), key=lambda vm: vm[1], reverse=True):
            print(vm_name, count)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                     description=sys.modules[__name__].__doc__, allow_abbrev=False)
    parser.add_argument('--for-vm', help='Display all logs matching this VM name & exit')
    parser.add_argument('--logs-filename', default='logs.json', help=' ')
    parser.add_argument('--since', help='Date must be specified with this format: YYYY-MM-DD')
    args = parser.parse_args(argv)
    if args.since:
        args.since = datetime.strptime(args.since, '%Y-%m-%d')
    return args


if __name__ == '__main__':
    main(sys.argv[1:])
