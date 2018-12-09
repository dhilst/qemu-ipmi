# Installation, add this line
# -cdrom iso -boot d \
# -hda CN1.qcow2 \

DISPLAY=:0 qemu-system-x86_64 \
  -device e1000,netdev=net0,mac=00:00:00:00:00:02 \
  -netdev tap,id=net0,script=./qemu-ifup.sh \
  -m 1024 -smp 2 -enable-kvm -machine q35,accel=kvm \
  -device intel-iommu -usb -device usb-mouse -device usb-kbd -show-cursor \
  -chardev socket,id=ipmi0,host=localhost,port=9102,reconnect=10 \
  -device ipmi-bmc-extern,id=bmc0,chardev=ipmi0 \
  -device isa-ipmi-bt,bmc=bmc0 \
  -serial mon:telnet::9103,server,telnet,nowait
