#!/bin/sh

sudo apt-get update
sudo apt-get install python3-pip nginx gunicorn python3-flask python3-paramiko python3-pytest -y

pip3 install flask gunicorn
sudo pip3 install schedule pyserial gitpython signalslot python-dateutil pyinotify websockets pytest-mock
sudo pip3 install schedule # for some reason this seems to be necessary
# GPIO Library installieren
cd ~
git clone https://github.com/LeMaker/RPi.GPIO_BP -b bananapi
cd RPi.GPIO_BP
sudo apt-get install python3-dev -y
python3 setup.py install
sudo python3 setup.py install


# sysdmanager
cd ~
sudo apt install dbus libdbus-glib-1-dev libdbus-1-dev -y
pip3 install dbus-python
git clone https://github.com/emlid/systemd-manager.git
cd systemd-manager
sudo python3 setup.py install
cd ~

# pyupdi
cd ~
git clone https://github.com/mraardvark/pyupdi.git
cd pyupdi
sudo python3 setup.py install

# copy and modify files
sudo chmod +x /home/base/base/setup_files/copy_service_and_nginx_files.sh
sudo chmod +x /home/base/base/setup_files/create_aliases.sh
/home/base/base/setup_files/copy_service_and_nginx_files.sh
/home/base/base/setup_files/create_aliases.sh

# create directories
sudo mkdir /media/BackupHDD
sudo mkdir /media/NASHDD

# program SBU
/home/base/base/setup_files/program_sbu.sh

sudo systemctl restart nginx
