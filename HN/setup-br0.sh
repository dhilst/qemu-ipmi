#!/bin/bash
ip link add name br0 type bridge
ip link set br0 up
ip addr add 192.168.123.1/24 dev br0

# Not working 
# firewall-cmd --zone=external --add-masquerade --permanent
# firewall-cmd --reload
#
systemctl stop firewalld
iptables -t nat -A POSTROUTING -o wlp0s20u2 -j MASQUERADE
iptables -A FORWARD -i tap0 -o wlp0s20u2 -j ACCEPT
sysctl net.ipv4.ip_forward=1

## on the vm
# nmcli con mod enp0s2 ipv4.method manual ipv4.address 192.168.123.2/24 ipv4.gateway 192.168.123.1
# nmcli con mod enp0s2 ipv4.dns 192.168.0.1
# nmcli con down enp0s2
# nmcli con up enp0s2

