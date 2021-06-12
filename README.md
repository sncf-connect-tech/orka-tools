# orka-tools

[![build status](https://github.com/voyages-sncf-technologies/orka-tools/workflows/build/badge.svg)](https://github.com/voyages-sncf-technologies/orka-tools/actions?query=branch%3Amaster)

Orka documentation: https://orkadocs.macstadium.com/docs

## Scripts

* `audit_vms.py`: look for "suspicious" VMs that have been running for several hours on an Orka cluster
* `dump_logs.py` & `logs_stats.py`: retrieve & analyse Orka cluster logs
* `orka.py`: an alternate implementation of the Orka CLI that better suits our needs

## Installation

    pip install -r requirements.txt

## Usage

First, you need to define some environment variables:

    export ORKA_CONTROLLER_URL=
    export ORKA_USER_EMAIL=...
    export ORKA_LICENSE_KEY=
    export ORKA_PASSWORD=

You can pass `--help` to any of the scripts to get a detailed description of the arguments & sub-commands it supports.
