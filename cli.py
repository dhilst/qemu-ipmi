"""
This script create, destroy and manage virtual cluster for testing purposes

!!!! DO NOT ADD PIP DEPENDENCIES TO THIS !!!!


# Network configuration (an example)

* br0 `192.168.123.254/24`
* Head node `192.168.123.253/24`
* Service node `192.168.123.252/24`
* Computing node 1 `192.168.123.1/24`, BMC `192.168.124.1/24`
* Computing node 2 `192.168.123.2/24`, BMC `192.168.124.2/24`
"""
import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from subprocess import CalledProcessError, check_output
import urllib.request
import urllib.parse

def json_dumps(obj) -> str:
    return json.dumps(obj, default=str)

def sh(cmd: str) -> str:
    print(f"Running {cmd}")
    return check_output(cmd, shell=True, universal_newlines=True)

type IP = str # X.X.X.X/X
type MAC = str # xx:xx:xx:xx:xx:xx
type Network = str # X.X.X.0/X
type Port = int

@dataclass
class VM:
    mac: MAC
    ip: IP
    bmc_addr: tuple[IP, Port]
    name: str
    disk: Path
    memory: int
    ncpu: int
    tap: str # tap device


@dataclass
class Cluster:
    mn: Network # X.X.X.X/M
    sn: Network
    an: Network
    hn: VM
    cns: list[VM]


# The below functions must be idempotent
def iptables(args: str):
    """Create an iptables rule if does not exists, i.e., idempotently"""
    try:
        sh("sudo iptables " + args.replace("-A", "-C"))
    except CalledProcessError:
        print("iptables rule already exists, skipping")
        return
    sh(f"sudo iptables {args}")

def symlink(link: Path, to: Path) -> Path:
    if link.exists():
        print(link)
        assert link.is_symlink(), f"{link} is not a link"
        return link

    link.symlink_to(to.absolute())
    return link

def mkdir(path: Path):
    return path.mkdir(parents=True, exist_ok=True)

def create_hard_disk(path: Path, sizgb: int) -> Path:
    if path.exists():
        return path
    sh(f"qemu-img create -f qcow2 {path} {sizgb}G")
    assert path.exists()
    return path

def download_file(url: str, directory: Path) -> Path:
    assert directory.exists(), f"{directory} No such file or directory"
    path = Path(urllib.parse.urlparse(url).path).name
    fullpath = directory.joinpath(path).absolute()
    if fullpath.exists():
        print(f"ISO {fullpath} found, skipping download")
        return fullpath

    print(f"Downloading {fullpath}")
    urllib.request.urlretrieve(url, fullpath)

    return fullpath

def create_bridge(name: str, outnic: str, tap: str, ip: IP, more_ips: list[IP] = []):
    try:
        sh(f"sudo ip link show dev {name}")
        return  # bridge already exists
    except CalledProcessError:
        pass
    sh(f"sudo ip link add name {name} type bridge")
    sh(f"sudo ip link set {name} up")
    sh(f"sudo ip addr add {ip} dev {name}")
    for ip in more_ips:
        sh(f"ip addr add {ip} dev {name}")

    # sh(f"systemctl stop firewalld")
    # TODO make this iptables commands idempotent
    iptables(f"-t nat -A POSTROUTING -o {outnic} -j MASQUERADE")
    iptables(f"-A FORWARD -i {tap} -o {outnic} -j ACCEPT")
    # TODO, try this again instead of iptables (it was not working)
    # firewall-cmd --zone=external --add-masquerade --permanent
    # firewall-cmd --reload
    sh(f"sudo sysctl net.ipv4.ip_forward=1")


def delete_bridge(name: str):
    sh(f"sudo ip link delete {name} type bridge")



def create_qemu_install_script(mac: str, path: Path, scripts_path: Path, tap_ifname: str):
    # TODO:
    # Command line arguments for OpenIPMI
    # -chardev socket,id=ipmi0,host=localhost,port=9002,reconnect=10 \
    # -serial mon:telnet::9003,server,telnet,nowait
    contents = f"""#!/bin/bash -xe

this_dir=$(realpath $(dirname $0))

DISPLAY=:0 sudo qemu-system-x86_64 -hda ${{this_dir}}/disk.qcow2 \
-cdrom ${{this_dir}}/iso -boot d -device e1000,netdev=net0,mac={mac} \
-netdev tap,id=net0,ifname={tap_ifname},script={scripts_path}/qemu-ifup.sh -m 2048 -smp 2 -enable-kvm \
-machine q35,accel=kvm -device intel-iommu -usb -device usb-mouse -device usb-kbd -cpu host
"""
    path.write_text(contents)
    sh(f"chmod +x {path.absolute()}")

@staticmethod
def create_qemu_script(mac: str, path: Path, scripts_path: Path):
    # TODO:
    # Command line arguments for OpenIPMI
    # -chardev socket,id=ipmi0,host=localhost,port=9002,reconnect=10 \
    # -serial mon:telnet::9003,server,telnet,nowait
    # HN (run) 
    # -device ipmi-bmc-extern,id=bmc0,chardev=ipmi0 
    # -device isa-ipmi-bt,bmc=bmc0 \
    contents = f"""#!/bin/bash

this_dir=$(realpath $(dirname $0))

DISPLAY=:0 qemu-system-x86_64 -cpu host -hda ${{this_dir}}/disk.qcow2 \
    -device e1000,netdev=net0,mac={mac} \
    -netdev tap,id=net0,script={scripts_path}/qemu-ifup.sh \
    -m 8192 -smp 2 -enable-kvm -machine q35,accel=kvm \
    -device intel-iommu -usb -device usb-mouse -device usb-kbd \
"""
    path.write_text(contents)
    sh(f"chmod +x {path.absolute()}")

@staticmethod
def create_machine(mn, sn, an) -> VM:
    # TODO, maybe use libvirt instead
    raise NotImplemented

@staticmethod
def create_cluster(args: argparse.Namespace):
    # Download the ISO 
    cluster_path = args.state_directory.joinpath("clusters").joinpath(args.cluster_id).absolute()
    scripts_path = args.state_directory.joinpath("scripts").absolute()
    mkdir(scripts_path)
    mkdir(cluster_path)
    iso_path = download_file(isos[args.iso], args.state_directory.joinpath("isos"))
    hn_path = cluster_path.joinpath("HN")
    mkdir(hn_path)
    hn_disk = create_hard_disk(hn_path.joinpath("disk.qcow2"), 40)
    symlink(hn_path.joinpath("iso"), iso_path)

    # Network
    # TODO: Generalize this
    delete_bridge(args.mn_bridge)
    create_bridge(args.mn_bridge, args.output_iface, args.hn_tap_iface, args.hn_ip)


    # Headnode
    hn_qemu_install = hn_path.joinpath("HN-qemu-install.sh")
    hn_qemu = hn_path.joinpath("HN-qemu.sh")
    create_qemu_install_script(args.hn_mac, hn_qemu_install, scripts_path)
    create_qemu_script(args.hn_mac, hn_path.joinpath("HN-qemu.sh"), scripts_path)

    # install the headnode
    # TODO make this step idempotent
    if args.install_os:
        sh(f"sudo {hn_qemu_install}") # how to make this idempotent? maybe write a file to the disk afterwards?

    # Run the HN
    sh(f"sudo {hn_qemu}")

    # create_machine(mn, sn, an) # head node
    # for i in range(1, 3):
    #     create_machine(mn, sn, an) # computing nodes


type ip = str
type ip_range = tuple[str, str]

isos = {
    "rocky-9.4-minimal": "https://download.rockylinux.org/pub/rocky/9/isos/x86_64/Rocky-9.4-x86_64-minimal.iso"
}

# Head node qemu command
# DISPLAY=:0 qemu-system-x86_64 -cpu host -hda HN.qcow2 \ -device e1000,netdev=net0,mac=00:00:00:00:00:01 \
#   -netdev tap,id=net0,script=./qemu-ifup.sh \
#   -m 8192 -smp 2 -enable-kvm -machine q35,accel=kvm \
#   -device intel-iommu -usb -device usb-mouse -device usb-kbd \
#   -chardev socket,id=ipmi0,host=localhost,port=9002,reconnect=10 \
#   -device ipmi-bmc-extern,id=bmc0,chardev=ipmi0 \
#   -device isa-ipmi-bt,bmc=bmc0 \
#   -serial mon:telnet::9003,server,telnet,nowait

# Computing node qemu command
# 
# WARNING!!! IF YOU COPY THIS CHANGE THE UUID
# 
# DISPLAY=:0 qemu-system-x86_64 \
#   -device e1000,netdev=net0,mac=00:00:00:00:00:02 \
#   -netdev tap,id=net0,script=./qemu-ifup.sh \
#   -m 2048 -smp 2 -enable-kvm -machine q35,accel=kvm \
#   -device intel-iommu -usb -device usb-mouse -device usb-kbd -show-cursor \
#   -chardev socket,id=ipmi0,host=localhost,port=9102,reconnect=10 \
#   -device ipmi-bmc-extern,id=bmc0,chardev=ipmi0 \
#   -device isa-ipmi-bt,bmc=bmc0 \
#   -serial mon:telnet::9103,server,telnet,nowait \
#   -uuid 3ad70b74-f256-4b74-ab83-0b2de1f81269


def main():
    # Initialize the argument parser
    parser = argparse.ArgumentParser(
        description="Create and manage testing clusters for Cloyster"
    )

    parser.add_argument("--state-directory", type=Path, help="Where to save the state", default="/var/run/cloyster-test/")
    parser.add_argument("--debug", type=bool, default=False)
    parser.add_argument("--cluster-id", type=str, required=True)

    commands = parser.add_subparsers(dest="command")
    commands.required = True
    create_cmd = commands.add_parser("create", help="Create a cluster")
    destroy_cmd = commands.add_parser("destroy", help="Destroy a cluster")

    # Define arguments
    create_cmd.add_argument(
        '--iso',
        choices=list(isos.keys()),
        required=True,
        help="ISO to use"
    )
    create_cmd.add_argument(
        '--install-os',
        action=argparse.BooleanOptionalAction,
        required=True,
        help="Run the OS installation step"
    )
    create_cmd.add_argument(
            '--hn-mac',
            type=str,
            required=True,
            help="HN MAC address"
    )
    create_cmd.add_argument(
            '--mn-bridge',
            type=str,
            required=True,
            help="Management network bridge name, e.g. br0"
    )
    create_cmd.add_argument(
            '--output-iface',
            type=str,
            required=True,
            help="Output interface, e.g. eth0"
    )
    create_cmd.add_argument(
            '--hn-tap-iface',
            type=str,
            required=True,
            help="Output interface, e.g. tap0"
    )
    create_cmd.add_argument(
            '--hn-ip',
            type=str,
            required=True,
            help="HN IPv4 in CIDR notation, e.g. 192.168.123.254/24"
    )
    # parser.add_argument(
    #     '-r', '--output',
    #     type=str,
    #     default='output.txt',
    #     help="Output file path (default: 'output.txt')"
    # )
    # parser.add_argument(
    #     '-v', '--verbose',
    #     action='store_true',
    #     help="Enable verbose output"
    # )
    # parser.add_argument(
    #     '--count',
    #     type=int,
    #     default=1,
    #     choices=range(1, 11),
    #     help="Number of iterations (1 to 10, default is 1)"
    # )
    # parser.add_argument(
    #     '--flag',
    #     action='store_true',
    #     help="Set a boolean flag"
    # )
    # parser.add_argument(
    #     '--threshold',
    #     type=float,
    #     help="A float threshold value"
    # )
    # parser.add_argument(
    #     '--list',
    #     nargs='+',
    #     type=int,
    #     help="List of integers"
    # )

    # Parse the arguments
    args = parser.parse_args()

    mkdir(args.state_directory.joinpath("isos"))
    mkdir(args.state_directory.joinpath("clusters"))
    if args.debug:
        print(args)

    if args.command == "create":
        return create_cluster(args)
    elif args.command == "destroy":
        raise NotImplemented 
    else:
        assert False, f"Unknonw command {args.command}"

    db.save()



if __name__ == '__main__':
    main()

