#!/bin/bash -x

xhost +

sudo fuser -kn tcp 9001
sudo fuser -kn tcp 9002
sudo fuser -kn tcp 9003

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
