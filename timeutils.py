import datetime
import dateutil.relativedelta

def readabletime(dif):
    remtime = ''
    attrs = ['days', 'hours', 'minutes']
    for attr in attrs:
        if getattr(dif, attr):
            remtime += "{} {} ".format(getattr(dif, attr), attr)
    return remtime

def get_diff(end, start = datetime.datetime.now()):
    return dateutil.relativedelta.relativedelta(end, start)

def get_rdbl_timediff(endstamp):
    end = datetime.datetime.fromtimestamp(endstamp)
    dif = get_diff(end)
    return readabletime(dif)