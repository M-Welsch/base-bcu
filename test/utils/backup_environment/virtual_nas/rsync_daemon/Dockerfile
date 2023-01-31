
FROM ubuntu

WORKDIR /home/user/
COPY . .

RUN apt update
RUN apt install rsync -y
RUN chmod +x rsync_daemon_entry_point.sh

CMD ["/home/user/rsync_daemon_entry_point.sh"]
