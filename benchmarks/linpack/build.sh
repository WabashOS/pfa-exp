#!/bin/bash
# Make this portable between platforms
# this package doesn't support parallel build
# Due to a shockingly convoluted build system, the TOPdir can not be determined
# from within the makefile, so we have to define it out here.

. /etc/os-release
if [ $ID == 'centos' ];
then
  TOPdir=${PWD} make arch=centos -j1
  cp ./bin/centos/xhpl ./bin/
elif [ $ID == 'fedora' ];
then
  TOPdir=${PWD} make arch=fedora -j1
	cp ./bin/fedora/xhpl ./bin/
elif [ $ID == 'ubuntu' ];
then
  TOPdir=${PWD} make arch=ubuntu -j1
	cp ./bin/ubuntu/xhpl ./bin/
else
  echo "Unrecognized distro: $ID"
fi
