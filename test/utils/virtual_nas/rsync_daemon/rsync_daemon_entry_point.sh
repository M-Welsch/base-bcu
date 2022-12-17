#!/bin/bash

mkdir -p $BACKUP_SOURCE_DIRECTORY
echo "use chroot = true
hosts allow = $HOSTS_ALLOW

transfer logging = true
log file = /var/log/rsyncd.log
log format = %h %o %f %l %b

[$BACKUP_SOURCE_NAME]
comment = Public Share
path = $BACKUP_SOURCE_DIRECTORY
read only = no
list = yes" > /etc/rsyncd.conf

echo "starting rsync daemon on port $RSYNC_DAEMON_PORT. Serving directory $BACKUP_SOURCE_DIRECTORY"
rsync --daemon --no-detach --port="$RSYNC_DAEMON_PORT"
