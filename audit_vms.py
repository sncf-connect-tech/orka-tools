#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Look for VMs that have been running for several hours on an Orka cluster,
which is suspicious when used as Gitlab CI runners.

Additionally, it can delete those "ghost" VMs.
'''

# USAGE example: ./audit_vms.py --list-running-for-hours 6
# Orka API reference: https://documenter.getpostman.com/view/6574930/S1ETRGzt

import argparse, sys
from datetime import datetime

from commons import add_common_opts_and_parse_args, check_http_status, orka_session, ArgparseHelpFormatter


def main(argv):
    args = parse_args(argv)
    ghost_vms_ids = []
    print(" All the times are in UTC timezone")
    print("//-------------------------//")
    present = datetime.utcnow()
    with orka_session(**vars(args)) as session:
        resp = check_http_status(session.get('/resources/vm/list/all'))
        for vm in resp.json()['virtual_machine_resources']:
            if vm['vm_deployment_status'] == 'Not Deployed':
                print(vm["virtual_machine_name"].ljust(22), ':', vm['vm_deployment_status'].ljust(14), " | owner : ", vm['owner'])
                continue
            print(vm["virtual_machine_name"].ljust(22), ':', vm['vm_deployment_status'].ljust(14), " | owner : ", vm['status'][0]['owner'])
            for status in vm['status']:
                print(f'\t{status["virtual_machine_id"]} │ {status["node_location"]} │ {status["virtual_machine_ip"]} │ cpu={status["cpu"]}/{status["vcpu"]} │ {status["RAM"]} │ {status["vm_status"]} │ {status["creation_timestamp"]} │ {status["base_image"]}')
                vm_creation_date = datetime.strptime(status['creation_timestamp'], '%Y-%m-%dT%H:%M:%SZ')
                vm_uptime_in_days = (present - vm_creation_date).days
                vm_uptime_in_hours = (present - vm_creation_date).seconds/3600
                if args.list_running_for_hours and vm_uptime_in_hours >= args.list_running_for_hours:
                    ghost_vms_ids.append((status['virtual_machine_id'], vm_uptime_in_days, vm_uptime_in_hours))
            print()
        print()
        if ghost_vms_ids:
            print(f'"ghost" VMs detected, running for at least {args.list_running_for_hours} hours:')
            print('\n'.join('{} - uptime: {}d and {:.1f}h'.format(vm_id, uptime_in_days, uptime_in_hours) for vm_id, uptime_in_days, uptime_in_hours in ghost_vms_ids))
            if args.delete_ghost_vms:
                print('You are about to delete all those VMs.')
                if not ask_for_confirmation():
                    print('Aborting')
                    return
                for ghost_vm_id, _, _ in ghost_vms_ids:
                    print('Deleting:', ghost_vm_id)
                    resp = check_http_status(session.delete('/resources/vm/delete',
                                             json={"orka_vm_name": ghost_vm_id}))
                    print(resp.json())
            else:
                sys.exit(2)


def ask_for_confirmation():
    print('Please confirm (y/n): ', end='')
    while True:
        choice = input().lower()
        if choice in ('yes', 'y'):
            return True
        if choice in ('no', 'n'):
            return False
        print("Please respond with 'yes' or 'no': ", end='')


def parse_args(argv=None):
    parser = argparse.ArgumentParser(formatter_class=ArgparseHelpFormatter,
                                     description=__doc__, allow_abbrev=False)
    parser.add_argument('--list-running-for-hours', type=float, help='List VMs running for at least X hours')
    parser.add_argument('--delete-ghost-vms', action='store_true', help='Require --list-running-for-hours')
    args = add_common_opts_and_parse_args(parser, argv)
    if args.delete_ghost_vms and not args.list_running_for_hours:
        parser.error('--delete-ghost-vms require --list-running-for-hours')
    return args


if __name__ == '__main__':
    main(sys.argv[1:])
