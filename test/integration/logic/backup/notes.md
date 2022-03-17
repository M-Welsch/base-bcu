# Test Backup Prequisites

This file documents what `test/setup_test_environment.sh` does. 
Although code should be self-documenting, the bash-file itself looks confusing and is difficult to follow at some point.

That's why this file as a "second source of truth" is maintained parallely. 
Anyway please conside the bash-file(s) as primary source of truth!

In order to run the complete backup chain locally, a few things need to be set up.

## Test sync via ssh

```shell
sudo apt install rsync
ssh-copy-id -i ~/.ssh/id_rsa.pub <your_username>@127.0.0.1
```

Test this by running. You should see your own home directory without being asked for your password:

```shell
ssh  <your_username>@127.0.0.1
```

## Test sync via SMB

```shell
sudo apt install samba
sudo useradd base
sudo smbpasswd -a base  # creates the samba user. Use the same password as you use for your production NAS
cd ~
mkdir .base_test/root_of_share -p
```

add the following lines to `/etc/samba/smb.conf`

```
[Backup]
    path = /tmp/base_tmpshare
    browsable = yes
    writable = no
    valid users = base
```

create credentials file `/etc/base-credentials`, fill it with content and restrict permissions

```
sudo vim /etc/base-credentials

# put the content in
username=base
password=<the password for the smb user 'base' from above>
domain=WORKGROUP

# restrict permissions
sudo chmod 404 /etc/base-credentials
```

## Commons

add to `/etc/fstab`

```
/tmp/base_tmpfs /tmp/base_tmpfs_mntdir ext4 noauto,users
//127.0.0.1/Backup /tmp/base_tmpshare_mntdir cifs credentials=/etc/base-credentials,noauto,users
```

create virtual hard drive as backup target

```shell
virtual_hard_drive="/utils/backup_environment/virtual_hard_drive"
dd if=/dev/urandom of=$virtual_hard_drive bs=1M count=40
mkfs.ext4 $virtual_hard_drive
mkdir /tmp/base_tmpfs_mntdir

# create a subfolder that is rw for the ordinary user
cd /tmp/base_tmpfs_mntdir
sudo mkdir backup_target
sudo chmod 666 "$backup_target"
sudo chown $(users):$(users) "$backup_target"
```
