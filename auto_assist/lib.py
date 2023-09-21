import os
import logging

USER_HOME = os.path.join(os.path.expanduser("~"), '.auto-assist')

# format to include timestamp and module
logging.basicConfig(format='%(asctime)s %(name)s: %(message)s', level=logging.INFO)

def get_logger(name=None):
    return logging.getLogger(name)

def pending():
    input('Press any key to exit ...')