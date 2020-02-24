#!/bin/bash
guestmount -a fed.qcow2 -i --rw mnt/
cp riscv-linux/arch/x86/boot/bzImage mnt/boot/vmlinuz-4.15.0-rc6pfa+
guestunmount mnt
