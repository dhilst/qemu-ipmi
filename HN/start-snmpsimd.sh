#!/bin/bash

if [ ! -d .snmpsim-env ]; then
	echo run init-snmpsim before
	exit
fi
source .snmpsim-env/bin/activate
sudo $PWD/.snmpsim-env/bin/snmpsimd.py --data-dir .data/ --agent-udpv4-endpoint=192.168.123.1:161 --process-user=$(whoami) --process-group=$(whoami) --log-level=error --v3-user=xcat --v3-auth-key=passw0rd --v3-priv-key=passw0rd
