#!/bin/sh

test ! -d run/bmc-stat-dir && mkdir -p run/bmc-stat-dir
ipmi_sim -c lan.conf -s run/bmc-stat-dir/ -f ipmisim1.emu -n &
