#!/bin/bash
# Make this portable between platforms
if [ `uname -m` == riscv64 ]
then
	make -l arch=fedora
	cp ./bin/fedora/xhpl ./bin/
else
	make -l arch=ubuntu
	cp ./bin/ubuntu/xhpl ./bin/
fi
