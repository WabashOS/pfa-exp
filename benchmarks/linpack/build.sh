#!/bin/bash
# Make this portable between platforms
# this package doesn't support parallel build
# Also /requires/ a fully qualified path in Make.fedora/ubuntu!

if [ `uname -m` == riscv64 ]
then
	make arch=fedora
	cp ./bin/fedora/xhpl ./bin/
else
	make arch=ubuntu
	cp ./bin/ubuntu/xhpl ./bin/
fi
