from threading import Thread

class Logger(Thread):
    def __init__(self, work_off_msg):
        super(Logger, self).__init__()
        self._term_flag = False
        self._work_off_msg = work_off_msg

    def run(self):
        while not self._term_flag:
            self._work_off_msg(self.log)

    def terminate(self):
        self._term_flag = True

    def append_to_queue(self, msg):
        self.queue.put(msg)

    def log(self, msg):
        print(msg)