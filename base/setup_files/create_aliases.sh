#!/bin/sh

echo "creating aliases base and base-test"
sudo echo "# BaSe aliases" >> /home/base/.bashrc
sudo echo "alias base='cd ~ && sudo python3 python.base/base'" >> /home/base/.bashrc