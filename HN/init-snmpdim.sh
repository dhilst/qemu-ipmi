#!/bin/bash
if [ "$1" = "clean" ]; then
	echo cleaning
	rm -rf .data
fi
source .snmpsim-env/bin/activate
pip show snmpsim || pip install git+https://github.com/etingof/snmpsim.git@fix-drop-privileges
if [ ! -d .data ]; then
	mkdir .data
	echo running snmprec, this may take some seconds...
	snmprec.py --agent-udpv4-endpoint=demo.snmplabs.com --output-file=./.data/public.snmprec
fi

