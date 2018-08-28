import datetime
import dateutil.relativedelta
import time

def readabletime(dif):
    remtime = ''
    attrs = ['days', 'hours', 'minutes']
    for attr in attrs:
        if getattr(dif, attr):
            remtime += "{} {} ".format(getattr(dif, attr), attr)
    return remtime

def get_diff(end, start):
    return dateutil.relativedelta.relativedelta(end, start)

def get_rdbl_timediff(endstamp):
    end = datetime.datetime.fromtimestamp(endstamp)
    start = datetime.datetime.fromtimestamp(time.time())
    dif = get_diff(end, start)
    return readabletime(dif)