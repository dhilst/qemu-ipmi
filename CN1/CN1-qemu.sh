# Installation, add this line
# -cdrom iso -boot d \
# -hda CN1.qcow2 \

# WARNING!!! IF YOU COPY THIS CHANGE THE UUID

DISPLAY=:0 qemu-system-x86_64 \
  -device e1000,netdev=net0,mac=00:00:00:00:00:02 \
  -netdev tap,id=net0,script=./qemu-ifup.sh \
  -m 2048 -smp 2 -enable-kvm -machine q35,accel=kvm \
  -device intel-iommu -usb -device usb-mouse -device usb-kbd -show-cursor \
  -chardev socket,id=ipmi0,host=localhost,port=9102,reconnect=10 \
  -device ipmi-bmc-extern,id=bmc0,chardev=ipmi0 \
  -device isa-ipmi-bt,bmc=bmc0 \
  -serial mon:telnet::9103,server,telnet,nowait \
  -uuid 3ad70b74-f256-4b74-ab83-0b2de1f81269
