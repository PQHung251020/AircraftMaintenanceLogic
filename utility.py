from datetime import date
from datetime import timedelta

def timestamp_to_day_int(timestamp):
    '''Calculate day from start'''
    d0 = date(2017, 9, 25) # HARDCODE
    d1 = date(timestamp.year, timestamp.month, timestamp.day)
    delta = d1 - d0
    return delta.days

def day_int_to_timestamp(day):
    d0 = date(2017, 9, 25)
    return d0 + timedelta(days=day)

def performance_log(title, t1, t2):
    print(title, round((t2 - t1) * 1000, 0), "ms")