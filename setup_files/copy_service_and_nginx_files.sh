#!/bin/sh

echo "copying service file for base-webapp"
sudo cp /home/base/base/setup_files/base-webapp.service /etc/systemd/system/

echo "copying nginx site file for base-webapp"
sudo cp /home/base/base/setup_files/base-webapp /etc/nginx/sites-available/
echo "linking nginx site file for base-webapp to sites-enabled"
sudo ln -s /etc/nginx/sites-available/base-webapp /etc/nginx/sites-enabled/base-webapp

echo "copying service file for base and enable to run on startup"
sudo cp /home/base/base/setup_files/base.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable base