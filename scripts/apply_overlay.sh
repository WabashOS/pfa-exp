#!/bin/bash
set -e

OVERLAY=bootstrap-overlay
MNT=disk-mount/
IMG=../../test.img

while getopts ":k:" opt; do
  case ${opt} in
    k )
			SSH_KEY_PATH=$OPTARG
      ;;
    \? ) echo "Usage: ./apply_overlay.sh [-k GITHUB_KEY]"
      ;;
  esac
done

sudo mount -o loop $IMG $MNT

# Apply default overlay
sudo chown -R root:root $OVERLAY/*
sudo cp -a $OVERLAY/* $MNT/

# Handle ssh keys (if needed)
if [ ! -z $SSH_KEY_PATH ]; then
  sudo cp $SSH_KEY_PATH $MNT/root/.ssh/git_key
  sudo chown -R root:root $MNT/root/.ssh
fi

# Clean up mount
sudo umount $MNT 
