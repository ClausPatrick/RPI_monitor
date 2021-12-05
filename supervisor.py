import threading
import sys
import os
import logging
import json
import RPI_monitor


class Supervisor():
    def __init__(self):
        self.counter = 0

    def main_routine(self):
        s = RPI_monitor.Session()
        s.check()    
        self.counter = (self.counter + 1) % 10
        if self.counter > 0:
            threading.Timer(5, self.main_routine).start()

c = Supervisor()
c.main_routine()

