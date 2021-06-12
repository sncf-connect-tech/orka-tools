#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
This script is an alternate implementation of the Orka CLI:
https://orkadocs.macstadium.com/docs/quick-start

It alleviates the following limitations of the official Orka CLI:
* the official Orka CLI always return a ZERO error code;
  this CLI return a non-ZERO error code in case of failure.
* a large majority of the official Orka CLI require a TTY to be used correctly,  making it difficult to use in scripts; this CLI does not require a TTY.
* the official Orka CLI produces ASCII coloring control sequences,  making its output difficult to parse; this CLI only produces plain text.

All the sub-commands of this CLI are similar to the ones of the official Orka CLI.However, this CLi it does not implement ALL sub-commands of the official Orka CLI so far,
as we only required a subset of them in our Ansible playbook.
'''

# USAGE: ./orka.py --help
# Orka API reference: https://documenter.getpostman.com/view/6574930/S1ETRGzt

import argparse, json, sys

from commons import add_common_opts_and_parse_args, check_http_status, orka_session, ArgparseHelpFormatter


def main(argv):
    args = parse_args(argv)
    with orka_session(**vars(args)) as session:
        args.func(args, session)


def vm_list(_, session):
    resp = check_http_status(session.get('/resources/vm/list/all'))
    deployed_vms = [vm for vm in resp.json()["virtual_machine_resources"] if "status" in vm]
    print(f"Deployed: {len(deployed_vms)}")
    if deployed_vms:
        print('        Name        │      ID       │       Owner       │     Node      │      IP       │ VNC  │ SSH  │ vCPU/CPU │ RAM │          Base image           │ Status  │ Deploy Date')
    for vm in deployed_vms:
        status = vm["status"][0]
        print(f"{vm['virtual_machine_name']:<19} | {status['virtual_machine_id']:<13} | {status['owner']:<17} | {status['node_location']:<8} ({status['node_status']:<2}) | {status['virtual_machine_ip']:<13} | {status['vnc_port']} | {status['ssh_port']} | {status['cpu']}/{status['vcpu']}      | {status['RAM']:<3} | {status['base_image']:<29} | {status['vm_status']:<7} | {status['creation_timestamp']}")
    print()
    not_deployed_vms = [vm for vm in resp.json()["virtual_machine_resources"] if "status" not in vm]
    print(f"Not Deployed: {len(not_deployed_vms)}")
    if not_deployed_vms:
        print('        Name        │       Owner       │ vCPU/CPU │ Base image')
    for vm in not_deployed_vms:
        print(f"{vm['virtual_machine_name']:<19} | {vm['owner']:<17} | {vm['cpu']}/{vm['vcpu']}      | {vm['base_image']}")


def vm_status(args, session):
    resp = check_http_status(session.get(f'/resources/vm/status/{args.vm}'))
    vms = resp.json()["virtual_machine_resources"]
    if not vms:
        print("No VMs found matching this name")
        sys.exit(1)
    if args.id_only:
        if "status" not in vms[0]:
            raise RuntimeError(f"VM {args.vm} not deployed")
        status = vms[0]["status"][0]
        print(status["virtual_machine_id"])
    else:
        print(json.dumps(vms, indent=4))


def vm_create_config(args, session):
    resp = check_http_status(session.post('/resources/vm/create',
                                          json={
                                            "orka_base_image": args.base_image,
                                            "orka_vm_name": args.vm,
                                            "orka_image": args.vm,
                                            "orka_cpu_core": args.cpu,
                                            "vcpu_count": args.vcpu,
                                          }))
    print(json.dumps(resp.json(), indent=4))


def vm_deploy(args, session):
    resp = check_http_status(session.post('/resources/vm/deploy',
                                          json={"orka_vm_name": args.vm}))
    print(json.dumps(resp.json(), indent=4))


def vm_create(args, session):
    vm_create_config(args, session)
    vm_deploy(args, session)


def vm_suspend(args, session):
    resp = check_http_status(session.post('/resources/vm/exec/suspend',
                                          json={"orka_vm_name": args.vm}))
    print(json.dumps(resp.json(), indent=4))


def vm_delete(args, session):
    resp = check_http_status(session.delete('/resources/vm/delete',
                                            json={"orka_vm_name": args.vm}))
    print(json.dumps(resp.json(), indent=4))


def vm_purge(args, session):
    resp = check_http_status(session.delete('/resources/vm/purge',
                                            json={"orka_vm_name": args.vm}))
    print(json.dumps(resp.json(), indent=4))


def image_list(_, session):
    resp = check_http_status(session.get('/resources/image/list'))
    images = resp.json()["image_attributes"]
    if images:
        print("             image             │ image_size │         modified         │        date_added        │ owner")
    for img in images:
        print(f"{img['image']:<30} | {img['image_size']:<3}        │ {img['modified']:<24} | {img['date_added']:<24} | {img['owner']}")


def image_save(args, session):
    resp = check_http_status(session.post('/resources/image/save',
                                          json={
                                            "orka_vm_name": args.vm,
                                            "new_name": args.new_base_image_name
                                          }))
    print(json.dumps(resp.json(), indent=4))


def parse_args(argv=None):
    parser = argparse.ArgumentParser(formatter_class=ArgparseHelpFormatter,
                                     description=sys.modules[__name__].__doc__, allow_abbrev=False)
    parser.add_argument('--retries', type=int, default=3, help='Max HTTP retries')
    parser.add_argument('--backoff-factor', type=float, default=.3, help='Backup factor for HTTP retries')
    subparsers = parser.add_subparsers(required=True)

    vm_cmd = subparsers.add_parser('vm')
    vm_subparsers = vm_cmd.add_subparsers(dest='vm', required=True)
    vm_list_cmd = vm_subparsers.add_parser('list')
    vm_list_cmd.set_defaults(func=vm_list)
    vm_status_cmd = vm_subparsers.add_parser('status')
    vm_status_cmd.set_defaults(func=vm_status)
    vm_status_cmd.add_argument('--vm', '-v', required=True)
    vm_status_cmd.add_argument('--id-only', action='store_true')
    vm_create_config_cmd = vm_subparsers.add_parser('create-config')
    vm_create_config_cmd.set_defaults(func=vm_create_config)
    vm_create_config_cmd.add_argument('--vm', '-v', required=True)
    vm_create_config_cmd.add_argument('--base-image', '-b', required=True)
    vm_create_config_cmd.add_argument('--cpu', '-c', type=int, required=True)
    vm_create_config_cmd.add_argument('--vcpu', '-C', type=int, required=True)
    vm_deploy_cmd = vm_subparsers.add_parser('deploy')
    vm_deploy_cmd.set_defaults(func=vm_deploy)
    vm_deploy_cmd.add_argument('--vm', '-v', required=True)
    vm_create_cmd = vm_subparsers.add_parser('create')
    vm_create_cmd.set_defaults(func=vm_create)
    vm_create_cmd.add_argument('--vm', '-v', required=True)
    vm_create_cmd.add_argument('--base-image', '-b', required=True)
    vm_create_cmd.add_argument('--cpu', '-c', type=int, required=True)
    vm_create_cmd.add_argument('--vcpu', '-C', type=int, required=True)
    vm_suspend_cmd = vm_subparsers.add_parser('suspend')
    vm_suspend_cmd.set_defaults(func=vm_suspend)
    vm_suspend_cmd.add_argument('--vm', '-v', required=True)
    vm_delete_cmd = vm_subparsers.add_parser('delete')
    vm_delete_cmd.set_defaults(func=vm_delete)
    vm_delete_cmd.add_argument('--vm', '-v', required=True)
    vm_purge_cmd = vm_subparsers.add_parser('purge')
    vm_purge_cmd.set_defaults(func=vm_purge)
    vm_purge_cmd.add_argument('--vm', '-v', required=True)

    img_cmd = subparsers.add_parser('image')
    img_subparsers = img_cmd.add_subparsers(dest='image', required=True)
    img_list_cmd = img_subparsers.add_parser('list')
    img_list_cmd.set_defaults(func=image_list)
    img_save_cmd = img_subparsers.add_parser('save')
    img_save_cmd.set_defaults(func=image_save)
    img_save_cmd.add_argument('--vm', '-v', required=True)
    img_save_cmd.add_argument('--new-base-image-name', '-b', required=True)

    return add_common_opts_and_parse_args(parser, argv)


if __name__ == '__main__':
    main(sys.argv[1:])
