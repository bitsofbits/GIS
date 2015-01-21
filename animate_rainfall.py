from __future__ import print_function
import csv
import numpy as np
from datetime import datetime, timedelta
from collections import OrderedDict
from zipfile import ZipFile
from matplotlib.patches import Circle
from matplotlib import animation
from datetime_range import datetime_range


class Station(object):
    
    def __init__(self, station_id, raw_lat, raw_lon, raw_data):
        self.station_id = station_id
        # Longitude is west so we invert sign.
        self.lon = -self._coord_to_float(raw_lon)
        self.lat = self._coord_to_float(raw_lat)
        self.data = self.cook(raw_data)
        
    def hourly_rainfall(self, time):
        times = datetime_range(time - timedelta(minutes=60), time, timedelta(minutes=1))
        total = 0.0
        for t in times:
            total += self.data.get(t, 0.0)
        return total
                
    @staticmethod
    def cook(raw_data):
        # Rain data consists of a preamble of 6 lines, then a data in Month/Day/Year format followed by lines in
        # "time precip" where time is in military time format (eg 2215 for 10:15 PM).
        date = None
        cooked = {}
        # Skip preamble by starting after line 6.
        for line in raw_data[6:]:
            if '/' in line:
                month, day, year = (int(x) for x in line.split('/'))
                date = (month, day, year)
            else:
                if date is None:
                    raise ValueError("date not set before time-precip data encountered")
                time, precip = line.split()
                stamp = (year, month, day, int(time))
                if precip == "_____":
                    precip = 0  # use 0 for unknown? data
                cooked[Station._to_datetime(stamp)] = float(precip)
        return cooked
    
    @staticmethod
    def _to_datetime(ts):
        year, month, day, time24 = ts
        year += 2000
        hour = time24 // 100
        minute = time24 % 100
        if hour == 24:
            hour = 0
            return datetime(year, month, day, hour, minute) + timedelta(days=1)         
        else:
            return datetime(year, month, day, hour, minute)
    
    @staticmethod
    def _coord_to_float(text):
        degrees, minutes, seconds = (float(x) for x in text.split())
        return degrees + minutes / 60.0 + seconds / 3600      
        
        
def load_station_data():
    station_data = OrderedDict()
    with ZipFile("rainfall_data.zip") as rainfall_data:
        with rainfall_data.open('rainfall_data/ALERT_sensors_all_by_id.csv') as csvfile:
            csv_data = csv.reader(csvfile)
            next(csv_data) # discard header
            for (raw_id, name, type_, date, raw_lat, raw_lon, elev, locstring) in csv_data:
                if type_ == "Precip.":
                    # For some reason, station ID is represented as "{ID}.00", so we discard the unused trailing part here. 
                    station_id = int(raw_id.split('.')[0])
                    with rainfall_data.open("rainfall_data/station_{0}.txt".format(station_id)) as source:
                        raw_data = source.readlines()   
                    station_data[station_id] = Station(station_id, raw_lat, raw_lon, raw_data)
    return station_data
                    
                    
def plot_weather_station_locs(themap, station_data):
    for rdata in station_data.values():
        x, y = themap.bmap(rdata.lon, rdata.lat)
        # We use a radius of 200 since the x, y coordinates are in meters. Smaller values result
        # in dots that are too small or invisible.
        p = Circle((x,y), radius=200, facecolor='black', edgecolor='black')
        themap.axes.add_patch(p)
                    
                    
def normalized_hourly_rainfall(stat_data, times):
    max_rainfall = 0.0
    rainfall = {}
    for t in times:
        hourly = np.array([x.hourly_rainfall(t) for x in stat_data.values()])
        rainfall[t] = hourly
        max_rainfall = max(max_rainfall, hourly.max())
    # Normalize the rainfall to the max rainfall.
    for x in rainfall.values():
        x /= max_rainfall
    return rainfall
    
    

    
class RainfallAnimator(object):
    
    def __init__(self, themap, station_data, rainfall, scale=20000, verbose=True):
        self.themap = themap
        self.station_data = station_data
        self.rainfall = rainfall
        self.scale = scale
        self.verbose = verbose
        
    def init(self):
        self.patches = []
        for rdata in self.station_data.values():
            x, y = self.themap.bmap(rdata.lon, rdata.lat)
            p = Circle((x,y), radius=1, facecolor='blue', edgecolor='none', alpha=0.3)
            self.themap.axes.add_patch(p)
            self.patches.append(p)
        # Place a label in the lower-left corner of the map than displays the current time.
        x0 = self.themap.axes.get_xlim()[0]
        y0 = self.themap.axes.get_ylim()[0]
        self.label = self.themap.axes.text(x0, y0, "")
        return self.patches + [self.label]
    
    def animate(self, ts):
        if self.verbose:
            print('.', end='')
        if ts in self.rainfall:
            for w, p in zip(self.rainfall[ts], self.patches):
                # We set the *area* of the circle to be proportional to the rainfall at this time.
                p.radius = self.scale*np.sqrt(w)
        # Update the time and date.
        self.label.set_text("{0.year}:{0.month:02}:{0.day:02}:{0.hour:02}{0.minute:02}".format(ts))
        return self.patches + [self.label]  
    
    def make_animation(self, times, interval=20):
        return animation.FuncAnimation(self.themap.fig, self.animate, 
                                       init_func=self.init,
                                       frames=times, 
                                       interval=interval,
                                       blit=True)
    
# def animate_rainfall(themap, station_data, rainfall, times, scale=20000):
#     # Make a black dot for each station *and* and paritally transparent blue circle.
#     # The dot is used to represent the locations of the station while the area of the
#     # circle is updated at each time step to indicate the amount of rainfall.
#     patches = []
#     #
#     def init():
#         global label
#         for rdata in station_data.values():
#             x, y = themap.bmap(rdata.lon, rdata.lat)
#             p = Circle((x,y), radius=1, facecolor='blue', edgecolor='none', alpha=0.3)
#             themap.axes.add_patch(p)
#             patches.append(p)
#         # Place a label in the lower-left corner of the map than displays the current time.
#         x0 = themap.axes.get_xlim()[0]
#         y0 = themap.axes.get_ylim()[0]
#         label = themap.axes.text(x0, y0, "")
#         return patches + [label]
#     #
#     def animate(dt):
#         print('.', end='')
#         if dt in rainfall:
#             for w, p in zip(rainfall[dt], patches):
#                 # We set the *area* of the circle to be proportional to the rainfall at this time.
#                 p.radius = scale*np.sqrt(w)
#         # Update the time and date.
#         label.set_text("{0.year}:{0.month:02}:{0.day:02}:{0.hour:02}{0.minute:02}".format(dt))
#         return patches + [label]
#     #
#     return animation.FuncAnimation(themap.fig, animate, 
#                                    init_func=init,
#                                    frames=times, 
#                                    interval=20,
#                                    blit=True)
    