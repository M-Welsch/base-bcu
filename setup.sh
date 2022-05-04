#!/bin/sh

echo_info () {
  NORMAL='\033[0;39m'
  YELLOW='\033[1;33m'
  MESSAGE="$1"
  echo "${YELLOW}$MESSAGE${NORMAL}"
}

install_apt_packages () {
  packages_to_install="python3 python3-pip"
  echo_info "installing packages that are required for testing: '$packages_to_install'"
  sudo apt update
  sudo apt install $packages_to_install
}

install_bpi_gpio () {
  echo_info "Installing GPIO Package for Bananapi"
  cd ~
  git clone https://github.com/LeMaker/RPi.GPIO_BP -b bananapi
  cd RPi.GPIO_BP
  sudo apt-get install python3-dev -y
  python3 setup.py install
  sudo python3 setup.py install
}

install_pyupdi () {
  cd ~
  git clone https://github.com/mraardvark/pyupdi.git
  cd pyupdi
  sudo python3 setup.py install
}

install_packages_deprecated () {
  # back in time it was necessary to start BaSe as root.
  # Therefore some packages had to be installed as root. Hopefully these times are over. Keeping this just in case ...
  sudo apt-get install python3-pip nginx gunicorn python3-flask python3-paramiko python3-pytest -y
  pip3 install flask gunicorn
  sudo pip3 install schedule pyserial gitpython signalslot python-dateutil pyinotify websockets pytest-mock
  sudo pip3 install schedule # for some reason this seems to be necessary
}

install_packages() {
  install_apt_packages
  install_bpi_gpio
  install_pyupdi
  # install_packages_deprecated  # hopefully this won't be necessary anymore!
}

create_directories () {
  dirs="log"
  dirs_root="/media/BackupHDD /media/NASHDD"
  echo "creating directories: $dirs. And those with root permissions: $dirs_root"
  mkdir $dirs
  sudo mkdir $dirs_root
}

create_aliases () {
  echo_info "creating aliases base and base-test"
  echo "" >> /home/base/.bashrc
  echo -e "# BaSe aliases\n
alias base='cd ~ && sudo python3 /python.base/base'\n
alias base-test='sudo python3 /home/base/base/test/rev3b_bringup_test_suite.py'\n
alias dock='cd ~/base-bcu && python3 utils/control_hardware.py -D'\n
alias power='cd ~/base-bcu && python3 utils/control_hardware.py -P'\n
alias unpower='cd ~/base-bcu && python3 utils/control_hardware.py -p'\n
alias undock='cd ~/base-bcu && python3 utils/control_hardware.py -d'\n
alias mount_backuphdd='cd ~/base-bcu && python3 utils/control_hardware.py -M'\n
alias unmount_backuphdd='cd ~/base-bcu && python3 utils/control_hardware.py -m'\n
alias base='cd ~/base-bcu && python3 base'
" >> ~/.bashrc
}

create_service_file_for_base_bcu () {
  echo_info "create service-file for BaSe BCU"
  echo "[Unit]
Description=Backup Server's Backup Control Unit

[Service]
Type=simple
User=root
WorkingDirectory=/home/base/base-bcu
ExecStart=python3 base

[Install]
WantedBy=multi-user.target" | sudo tee /etc/systemd/system/base.service > /dev/null
}

create_service_file_for_base_webapp () {
  echo_info "create service-file for BaSe Webapp"
  echo "[Unit]
Description=Backup Server Webapp
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/home/base/webapp
ExecStart=/usr/bin/gunicorn3 --workers 3 --bind unix:/tmp/base-webapp.sock wsgi

[Install]
WantedBy=multi-user.target" | sudo tee /etc/systemd/system/base-webapp.service > /dev/null
}

create_nginx_website () {
  echo_info "creating nginx-website file"
  echo "upstream app_server {
    # fail_timeout=0 means we always retry an upstream even if it failed
    # to return a good HTTP response

    # for UNIX domain socket setups
    server unix:/tmp/base-webapp.sock fail_timeout=0;

    # for a TCP configuration
    # server 192.168.0.7:8000 fail_timeout=0;
  }


server {
    # use 'listen 80 deferred;' for Linux
    # use 'listen 80 accept_filter=httpready;' for FreeBSD
    listen 84 default_server;
    client_max_body_size 4G;

    # set the correct host(s) for your site
    server_name _;

    keepalive_timeout 5;

    # path for static files
    root /home/maxi/base/webapp/;

    location / {
      # checks for static file, if not found proxy to app
      try_files \$uri @proxy_to_app;
    }

    location @proxy_to_app {
      proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
      proxy_set_header X-Forwarded-Proto \$scheme;
      proxy_set_header Host \$http_host;
      # we don't want nginx trying to do something clever with
      # redirects, we set the Host: header above already.
      proxy_redirect off;
      proxy_pass http://app_server;
    }

    error_page 500 502 503 504 /500.html;
    location = /500.html {
      root /path/to/app/current/public;
    }
  }" | sudo tee /etc/nginx/sites-available/base-webapp > /dev/null
  echo_info "linking nginx site file for base-webapp to sites-enabled"
  sudo ln -s /etc/nginx/sites-available/base-webapp /etc/nginx/sites-enabled/base-webapp
}

create_files () {
  create_service_file_for_base_bcu
  create_service_file_for_base_webapp
  create_nginx_website
}

enable_access_to_hardware () {
  echo_info "enabling user base to access hardware without sudo permissions"
  echo 'SUBSYSTEMS=="mem", MODE="0666"' | sudo tee /etc/udev/rules.d/99-backup_server.rules > /dev/null
  sudo setcap CAP_SYS_RAWIO+ep /usr/bin/python3.8
}

program_sbu () {
  echo_info "programing Standby Control Unit (SBU)"
  sudo python3 ./sbu_interface/sbu_updater.py
}

restart_services () {
  services="nginx"
  echo_info "restarting services $services"
  for service in $services
  do
    sudo systemctl restart $service
  done
}

install_packages
create_directories
create_aliases
create_files
enable_access_to_hardware
program_sbu
restart_services
