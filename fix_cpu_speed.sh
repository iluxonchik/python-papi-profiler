#!/bin/bash

# This is a helper script to fix the CPU speed to a cerntain frequency
sudo sudo sh -c "echo -n userspace > /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor"
sudo sudo sh -c "echo -n userspace > /sys/devices/system/cpu/cpu1/cpufreq/scaling_governor"
sudo sudo sh -c "echo -n userspace > /sys/devices/system/cpu/cpu2/cpufreq/scaling_governor"
sudo sudo sh -c "echo -n userspace > /sys/devices/system/cpu/cpu3/cpufreq/scaling_governor"
sudo sudo sh -c "echo -n userspace > /sys/devices/system/cpu/cpu4/cpufreq/scaling_governor"
sudo sudo sh -c "echo -n userspace > /sys/devices/system/cpu/cpu5/cpufreq/scaling_governor"
sudo sudo sh -c "echo -n userspace > /sys/devices/system/cpu/cpu6/cpufreq/scaling_governor"
sudo sudo sh -c "echo -n userspace > /sys/devices/system/cpu/cpu7/cpufreq/scaling_governor"

sudo cpufreq-set -c 0 -f $1
sudo cpufreq-set -c 1 -f $1
sudo cpufreq-set -c 2 -f $1
sudo cpufreq-set -c 3 -f $1
sudo cpufreq-set -c 4 -f $1
sudo cpufreq-set -c 5 -f $1
sudo cpufreq-set -c 6 -f $1
sudo cpufreq-set -c 7 -f $1

echo -e "CPU frequency set to " $1 " MHz\nYou can check this with\n\tcpupower frequency-info"
