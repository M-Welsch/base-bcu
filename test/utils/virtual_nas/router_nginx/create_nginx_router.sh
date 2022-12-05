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
  server {
    listen 22;
    proxy_pass ssh;
  }
  server {
    listen $RSYNC_DAEMON_PORT;
    proxy_pass rsyncd;
  }
}
" >> $NGINX_CONFIG_FILE
cat $NGINX_CONFIG_FILE

nginx -g "daemon off;"
