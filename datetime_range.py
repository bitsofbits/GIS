from datetime import datetime, timedelta

def datetime_range(start, stop, step=timedelta(minutes=1)):
    """Analogous to the range function, but for datetime objects"""
    times = []
    while start < stop:
        times.append(start)
        start = start + step
    return times