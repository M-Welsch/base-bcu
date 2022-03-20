#!/bin/sh

fstab="/etc/fstab"
smbconf="/etc/samba/smb.conf"
smbcredentials="/etc/base-credentials"

echo_info () {
  NORMAL='\033[0;39m'
  YELLOW='\033[1;33m'
  MESSAGE="$1"
  echo "${YELLOW}$MESSAGE${NORMAL}"
}

install_packages () {
  packages_to_install="rsync samba openssh-server"
  echo_info "installing packages that are required for testing: '$packages_to_install'"
  sudo apt update
  sudo apt install $packages_to_install
}

configure_ssh () {
  echo_info "Authenticate yourself to yourself. This is necessary in order to do a backup via ssh while both soruce and target are on your machine"
  ssh-copy-id -i ~/.ssh/id_rsa.pub "$(users)"@127.0.0.1
}

configure_samba () {
  echo_info "Add linux-user 'base' and smb-user 'base' in order to simulate a backup from a samba-source"
  sudo useradd base
  sudo smbpasswd -a base
  echo_info "Adding entry to smb.conf"
  backup_entry="[Backup]
    path = /tmp/base_tmpshare
    browsable = yes
    writable = no
    valid users = base"
  add_entry_to_file "$smbconf" "[Backup]" "$backup_entry"
  echo "username=base
password=<the password for the smb user 'base' from above>
domain=WORKGROUP
  " | sudo tee "$smbcredentials" > /dev/null
  sudo chmod 404 "$smbcredentials"
  RED='\033[1;31m'
  NORMAL='\033[0;39m'
  echo "${RED}Important !! Go to the file $smbcredentials and enter the correct for the base-samba share. This is the same password you entered earlier${NORMAL}"
}

add_entry_to_file () {
  target=$1
  condition=$(grep "$2" "$target")
  line_to_add=$3

  if [ -z "$condition" ];
  then
    echo "$line_to_add" | sudo tee -a  "$target" > /dev/null
  fi;
}

setup_virtual_hard_drive () {
  echo_info "Setting up virtual hard drive"
  virtual_hard_drive="$(dirname $(readlink -f $0))/utils/backup_environment/virtual_hard_drive"
  dd if=/dev/urandom of=$virtual_hard_drive bs=1M count=40
  mkfs.ext4 $virtual_hard_drive

  virtual_hard_drive_mountpoint=/tmp/base_tmpfs_mntdir
  mkdir $virtual_hard_drive_mountpoint
  add_entry_to_file "$fstab" 'base_tmpfs' "$virtual_hard_drive $virtual_hard_drive_mountpoint ext4 noauto,user,rw"
}

setup_virtual_smb_share () {
  echo_info "Setting up virtual samba share"
  add_entry_to_file "$fstab" '//127.0.0.1/Backup' "//127.0.0.1/Backup /tmp/base_tmpshare_mntdir cifs credentials=/etc/base-credentials,noauto,users"
}

make_backup_sink_writable () {
  vhd_mount_dir=/tmp/base_tmpfs_mntdir
  backup_target="${vhd_mount_dir}/backup_target"
  mkdir $vhd_mount_dir
  mount $vhd_mount_dir
  sudo mkdir "$backup_target"
  sudo chmod 666 "$backup_target"
  sudo chown $(users):$(users) "$backup_target"
  umount $vhd_mount_dir
}

install_packages
configure_ssh
configure_samba
setup_virtual_hard_drive
setup_virtual_smb_share
make_backup_sink_writable