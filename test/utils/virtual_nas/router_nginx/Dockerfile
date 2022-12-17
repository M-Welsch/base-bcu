FROM nginx

WORKDIR /home/user
COPY . .

RUN chmod +x /home/user/create_nginx_router.sh

CMD ["/home/user/create_nginx_router.sh"]
