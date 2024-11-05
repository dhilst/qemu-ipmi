#!/bin/sh -eu

# This script outputs what CPU model is supported. This
# was required because EL9 requires x86-64-v2. I had
# to add `-cpu host` to QEMU scripts but it may not work
# on very old CPUs, so I'm keeping this script in git.
# Before the `-cpu host` option, OL9 was kernel panicking
# on QEMU.

flags=$(cat /proc/cpuinfo | grep flags | head -n 1 | cut -d: -f2)

supports_v2='awk "/cx16/&&/lahf/&&/popcnt/&&/sse4_1/&&/sse4_2/&&/ssse3/ {found=1} END {exit !found}"'
supports_v3='awk "/avx/&&/avx2/&&/bmi1/&&/bmi2/&&/f16c/&&/fma/&&/abm/&&/movbe/&&/xsave/ {found=1} END {exit !found}"'
supports_v4='awk "/avx512f/&&/avx512bw/&&/avx512cd/&&/avx512dq/&&/avx512vl/ {found=1} END {exit !found}"'

echo "$flags" | eval $supports_v2 || exit 2 && echo "CPU supports x86-64-v2"
echo "$flags" | eval $supports_v3 || exit 3 && echo "CPU supports x86-64-v3"
echo "$flags" | eval $supports_v4 || exit 4 && echo "CPU supports x86-64-v4"

