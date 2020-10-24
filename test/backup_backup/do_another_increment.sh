#!/bin/sh

# Manual
####################
# 
# root-directory
# |
# |-Source
# |  |-file1
# |  |-file2 ...
# |
# |-Sink <- Skript hier ausführen


# Function Prototypes

get_latest_bu () {
	echo $(ls -d */ | head -1)
}

get_current_bu () {
	echo $(date +%Y_%m_%d-%H_%M_%S)
}

copy_with_hardlinks () {
	echo "copying with hardlinks"
	cp -al ${latest_bu}* $current_bu
}

synchronize () {
	rsync -avh --delete -e ssh root@192.168.0.34:/mnt/HDD/* $1
}

# Start

latest_bu=$( get_latest_bu )
echo "latest_bu $latest_bu"
current_bu=$( get_current_bu )
echo "current_bu $current_bu"

mkdir $current_bu

if [ $latest_bu ]
then
copy_with_hardlinks
fi

synchronize $current_bu
