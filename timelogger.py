from time import time
from datetime import timedelta

class TimeLogger(object):
    def __init__(self):
        self.start_time = None
        self.info = ""

    def seconds_str(t):
        return str(timedelta(seconds=t))

    def start(self, info=""):
        self.start_time = time()
        self.info = info
        print " %s started at %s" % (self.info, self.start_time)

    def end(self):
        self.end_time = time()
        print "%s finished at %s, elapsed %s seconds" % \
                (self.info,
                 self.end_time,
                 timedelta(seconds=self.end_time - self.start_time))

