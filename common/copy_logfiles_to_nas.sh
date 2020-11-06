#!/bin/sh
scp -i /home/base/.ssh/id_rsa -o LogLevel=DEBUG3 /home/base/base/log/* root@192.168.0.100:/mnt/HDD/share/Max/BaSe_Logs/
