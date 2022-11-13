
FROM ubuntu

WORKDIR /home/user/
COPY . .

RUN apt update
RUN apt install rsync -y
RUN chmod +x rsync_daemon_entry_point.sh

EXPOSE 1234

CMD ["/home/user/rsync_daemon_entry_point.sh"]
