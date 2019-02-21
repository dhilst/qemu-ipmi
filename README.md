# qemu-ipmi

This is a set of scripts for running QEMU machines with IPMI support provided by OpenIPMI. I've been using this to successufuly
test xCAT commands `rpower` and `rcons` on virtualized machines. Also to test sequencial based discovery with no need for real hardware.

# Dependencies

To run this you need

* `QEMU`
* OpenIPMI and OpenIPMI-lanserv. This can be installed on Fedora with `dnf install -y OpenIPMI-lanserv`
* An OS ISO, I've been using Centos 7
* `iproute2`, for creating bridges

# Network Setup

* `br0` `192.168.123.1/24`
* Head node `192.168.123.2/24`
* Computing node 1 `192.168.123.3/24`, BMC `192.168.123.4/24`
* Computing node 2 `192.168.123.5/24`, BMC `192.168.123.6/24`

This IPs are hard coded in lan.conf (The ipmisim (OpenIPMI-lanserv)) configuration file.

# Setup the network

The first thing to do is to create the bridge and setup the gateway IP, for this `HN/setup-br0.sh` is being used.
It will create the bridge, add IP and setup iptable to route traffic through real network interface. Please edit
this file and replace `wlp0s20u1` by your network interface.

PS: I stopped firewalld here!!!

# Istalling Head node operating system

Create the Head node disk, this is hardcoded at `HN/HN-qemu.sh`, just run `qemu-img create -f qcow2 HN/HN.qcow2 40G`

At `HN/HN-qemu.sh` there is a comment at top of the file for installing the OS, download a ISO image, (I was using Centos7.5 x86_64)
and create a link named `iso` in `HN/` pointing to the ISO, or edit the command line.
Run the commented qemu command and it should start QEMU booting the ISO image, just install the image and follow up.

# Create the computing nodes

Here is exactly the configuration that I have today. Don't stick to it, I managed to get sequential discovery to work so the machines
can be partially defined and discovered. Just keep in mind that the BMC configuration has to match to the lan.conf files, more on
this bellow.

```
# <xCAT data object stanza file>

n1:
    objtype=node
    arch=x86_64
    bmc=192.168.123.4
    chain=runcmd=bmcsetup,osimage=centos7.5-x86_64-netboot-compute
    cpucount=2
    cputype=QEMU Virtual CPU version 2.5+
    currchain=osimage=centos7.5-x86_64-netboot-compute
    currstate=netboot centos7.5-x86_64-compute
    groups=all
    installnic=mac
    ip=192.168.123.3
    mac=00:00:00:00:00:02
    memory=991MB
    mgt=ipmi
    mtm=QEMU:Standard PC (Q35 + ICH9, 2009)
    netboot=xnba
    os=centos7.5
    profile=compute
    provmethod=centos7.5-x86_64-netboot-compute
    status=booted
    statustime=02-17-2019 18:26:59
    supportedarchs=x86,x86_64
    switch=switch1
    switchport=0

n2:
    objtype=node
    arch=x86_64
    bmc=192.168.123.6
    chain=osimage=centos7.5-x86_64-netboot-compute
    cpucount=2
    cputype=QEMU Virtual CPU version 2.5+
    currchain=standby
    currstate=netboot centos7.5-x86_64-compute
    groups=all
    installnic=mac
    ip=192.168.123.5
    mac=00:00:00:00:00:03
    memory=991MB
    mgt=ipmi
    mtm=QEMU:Standard PC (Q35 + ICH9, 2009)
    netboot=xnba
    os=centos7.5
    profile=compute
    provmethod=centos7.5-x86_64-netboot-compute
    status=powering-on
    statustime=02-17-2019 16:03:51
    supportedarchs=x86,x86_64
    switch=switch1
    switchport=0
```

# BMC: What is important to understand and how things tie together ...

For each VM there is a ipmsim process in the host machine. This process represents
the BMC for that machine. ipmisim, has two configuration files. `lan.conf`, this
is the most important one and holds IP configuration, SoL ports, IPMI users etc. And
`ipmisim1.emu`, this is about sensors and such things, I don't really use sensor features
of OpenIPMI but the file need to be there.

At CN1 and CN2 you will find the respectives `lan.conf`. There you will find

* `addr 192.168.123.X 623`. This is the address of the BCM. Here I have this problem: I have
a single machine (the host) and need multiple process (ipmisim's) to listen at the same UDP port, 623. To
solve this I listen at distinc IPs. I could create an alias interface or something like that for each
IP but I just put it on br0, and its okay.
* `lan_config_program "../scripts/ipmi_sim_lancontrol br0"` This is a script called every time that the
network is configured in BMC, this is done during the sequential discovery, while the machine is botting
for example. It also is achievable by `ipmitool lan set 1 ...` commands
* `serial 15 localhost 9102 codec VM`. This is directly coupled to `-chardev socket,id=ipmi0,host=localhost,port=9102,reconnect=10` argument at `CNx-qemu.sh` file.
Each VM need a distinct port for this.
* `startcmd "./CN1-qemu.sh"` This is the command the `ipmisim` fires at power on commands.
* `sol "telnet:192.168.123.1:9103" 115200` directly coupled to `sol "telnet:192.168.123.1:9103" 115200` at `CNx-qemu.sh` It control communication
between QEMU and ipmisim for SoL to work. To get login working with this you need to setup tty on the computing node.
* `startnow false` If this is true, `startcmd` will run at ipmisim start.

So, summing up xCAT configuration (BCM IP), CNx-qemu.sh and lan.conf are closed tied together. If everything is lined up
you should be able to discovery computing nodes and use rpower and rcons commands.

# Anything missing?
If there are any missing bits, please let me know, I'll be glad to share any xCAT configuration that I have here. 

Regards,

