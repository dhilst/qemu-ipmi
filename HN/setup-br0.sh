#!/bin/bash

: ${BR:=br0}
: ${IP:=192.168.123.1/24}
: ${WLAN:=wlp9s0f3u2}
: ${TAP:=tap0}



ip link add name $BR type bridge
ip link set $BR up
ip addr add $IP dev $BR

# Not working 
# firewall-cmd --zone=external --add-masquerade --permanent
# firewall-cmd --reload
#
systemctl stop firewalld
iptables -t nat -A POSTROUTING -o $WLAN -j MASQUERADE
iptables -A FORWARD -i $TAP -o $WLAN -j ACCEPT
sysctl net.ipv4.ip_forward=1

## on the vm
# nmcli con mod enp0s2 ipv4.method manual ipv4.address 192.168.123.2/24 ipv4.gateway 192.168.123.1
# nmcli con mod enp0s2 ipv4.dns 192.168.0.1
# nmcli con down enp0s2
# nmcli con up enp0s2

