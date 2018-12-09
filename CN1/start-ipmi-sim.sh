#!/bin/sh

ip addr add 192.168.123.4/24 dev br0  # BMC ip
test ! -d run/bmc-stat-dir && mkdir -p run/bmc-stat-dir
ipmi_sim -c lan.conf -s run/bmc-stat-dir/ -f ipmisim1.emu -n -d
