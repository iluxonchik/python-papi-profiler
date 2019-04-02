#!/bin/bash

# This is a helper script to fix the CPU speed to a cerntain frequency
sudo cpufreq-set -c 0 -d 800MHz -u 2.40GHz -g powersave
sudo cpufreq-set -c 1 -d 800MHz -u 2.40GHz -g powersave
sudo cpufreq-set -c 2 -d 800MHz -u 2.40GHz -g powersave
sudo cpufreq-set -c 3 -d 800MHz -u 2.40GHz -g powersave
sudo cpufreq-set -c 4 -d 800MHz -u 2.40GHz -g powersave
sudo cpufreq-set -c 5 -d 800MHz -u 2.40GHz -g powersave
sudo cpufreq-set -c 6 -d 800MHz -u 2.40GHz -g powersave
sudo cpufreq-set -c 7 -d 800MHz -u 2.40GHz -g powersave

echo -e "CPU frequency restored to original value You can check this with\n\tcpupower frequency-info"
