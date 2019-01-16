#!/bin/bash

if [ ! -d .snmpsim-env ]; then
	echo run init-snmpsim before
	exit
fi
source .snmpsim-env/bin/activate
sudo $PWD/.snmpsim-env/bin/snmpsimd.py --data-dir .data/ --agent-udpv4-endpoint=192.168.123.2:161 --process-user=nobody --process-group=nobody --log-level=error 
