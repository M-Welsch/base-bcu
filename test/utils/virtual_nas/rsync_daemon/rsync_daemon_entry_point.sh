#!/bin/bash

mkdir -p $BACKUP_SOURCE_DIRECTORY
echo "use chroot = true
hosts allow = 172.17.0.0/24

transfer logging = true
log file = /var/log/rsyncd.log
log format = %h %o %f %l %b

[virtual_backup_source]
comment = Public Share
path = "$BACKUP_SOURCE_DIRECTORY"
read only = no
list = yes" > /etc/rsyncd.conf

echo "starting rsync daemon on port $RSYNC_DAEMON_PORT. Serving directory $BACKUP_SOURCE_DIRECTORY"
rsync --daemon --no-detach --port="$RSYNC_DAEMON_PORT"
