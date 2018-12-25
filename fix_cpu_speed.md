# How To Fix The CPU Speed In Linux

Run the `fix_cpu_speed.sh` with the desired fixed CPU speed as the argument.
For example, `./fix_cpu_speed.sh 800MHz` will fix the CPU speed on all cores 
to `800MHz`.

If you have the `intel_pstate` driver installed, you'll have to add the
`intel_pstate=disable` flag to your kernel boot line.

## Adding intel\_pstate=disable To Kernel Boot Line

1. `sudo vim /etc/default/grub`
2. find the line starting with `GRUB_CMDLINE_LINUX_DEFAULT` and append `intel_pstate=disable` to it
3. run `sudo update-grub` to update GRUB's configuration
4. reboot

You can check with which parameters your kernel booted with by running `cat /proc/cmdline`

# Resources

* [The Need To Disable intel\_pstate](https://unix.stackexchange.com/questions/153693/cant-use-userspace-cpufreq-governor-and-set-cpu-frequency)
* [Add Kernel Boot Parameter](https://askubuntu.com/questions/19486/how-do-i-add-a-kernel-boot-parameter)

