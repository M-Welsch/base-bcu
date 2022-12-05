#!/bin/bash

NGINX_CONFIG_FILE="/etc/nginx/nginx.conf"
echo "
stream {
  upstream ssh {
    server $IP_ADDRESS_SSH_SERVER:22;
  }
  upstream rsyncd {
    server $IP_ADDRESS_RSYNC_SERVER:$RSYNC_DAEMON_PORT;
  }
  upstream nfs {
    server $IP_ADDRESS_NFS_SERVER:2049;
  }
  server {
    listen 22;
    proxy_pass ssh;
  }
  server {
    listen $RSYNC_DAEMON_PORT;
    proxy_pass rsyncd;
  }
  server {
    listen 2049;
    proxy_pass nfs;
  } 
}
" >> $NGINX_CONFIG_FILE
cat $NGINX_CONFIG_FILE

nginx -g "daemon off;"
