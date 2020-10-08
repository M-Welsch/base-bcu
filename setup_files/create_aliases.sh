#!/bin/sh

echo "creating aliases base and base-test"
sudo echo "# BaSe aliases" >> /home/base/.bashrc
sudo echo "alias base='cd ~ && sudo python3 base'" >> /home/base/.bashrc
sudo echo "alias base-test='sudo python3 /home/base/test/rev3b_bringup_test_suite.py'" >> /home/base/.bashrc