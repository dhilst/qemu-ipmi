#!/bin/bash -x

xhost +
pushd HN
sudo ./setup-br0.sh
sudo ./start-ipmi-sim.sh &
popd

pushd CN1
sudo ./start-ipmi-sim.sh &
popd

pushd CN2
sudo ./start-ipmi-sim.sh &
popd
