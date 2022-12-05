#!/bin/bash

NGINX_CONFIG_FILE="/etc/nginx/nginx.conf"
echo "
stream {
  upstream ssh {
    server $IP_ADDRESS_SSH_SERVER:22;
  }
  server {
    listen 22;
    proxy_pass ssh;
  }
}
" >> $NGINX_CONFIG_FILE
cat $NGINX_CONFIG_FILE

nginx -g "daemon off;"
