from __future__ import print_function
import numpy as np
from glob import glob
from subprocess import call
from netCDF4 import Dataset
from datetime import datetime, timedelta
from glob import glob
from collections import namedtuple
from matplotlib.colors import Colormap, LinearSegmentedColormap


def convert_NEXRAD_to_CDF():
    all_paths = glob("radar_data/*")
    for in_path in [x for x in all_paths if not x.endswith(".nc")]:
        out_path = "{0}.nc".format(in_path)
        if out_path not in all_paths:
            call(["java", "-Xmx512m", "-classpath", "toolsUI-4.5.jar", "ucar.nc2.dataset.NetcdfDataset", 
                  "-in", in_path, 
                  "-out", out_path])

RadarData = namedtuple('RadarData', ["extent", "returns"])
    
def parse_datetime_from_path(path):
    dtstr = path[-15:-3]
    year = int(dtstr[:4])
    month = int(dtstr[4:6])
    day = int(dtstr[6:8])
    hour = int(dtstr[8:10])
    minute = int(dtstr[10:12])
    return datetime(year, month, day, hour, minute) - timedelta(hours=7)  # Weather data is in GMT
    
def load_radar_data():    
    returns = {}
    extent = None
    ncpaths = glob("radar_data/*.nc")
    for path in ncpaths:
        dt = parse_datetime_from_path(path)
        root = Dataset(path)
        #
        this_extent = (root.geospatial_lon_min, root.geospatial_lon_max, root.geospatial_lat_min, root.geospatial_lat_max)
        if extent is None:
            extent = this_extent
        else:
            assert extent == this_extent
        # 
        # We reverse the reflectivity axes so that it plots correctly. The y-axis is reversed because image-y increases 
        # as we go down, while the x-axis is reversed because lat_min, is actually the largest magnitude and is thus 
        # larger(!) than lat_max (don't blame me, that's just how the data is).
        returns[dt] = root.variables['BaseReflectivityComp_RAW'][:,::-1]
        root.close() 
    return RadarData(extent, returns)
    
cdict = {'red':   [(0.0,  1.0, 1.0),
                   (1.0,  1.0, 1.0)],

         'green': [(0.0,  0.0, 0.0),
                   (1.0,  0.0, 0.0)],

         'blue':  [(0.0,  0.0, 0.0),
                   (1.0,  0.0, 0.0)],
                   
         'alpha':  [(0.0,  0.0, 0.0),
                    (0.2,  0.0, 0.0),
                    (0.3,  0.4, 0.4),
                    (1.0,  0.8, 0.8)]       
        }

transparent_red_colormap = LinearSegmentedColormap("Transparent Red", cdict)

from matplotlib import animation






class RadarAnimator(object):
    
    def __init__(self, themap, radar_data, verbose=True):
        self.themap = themap
        self.radar_data = radar_data
        self.verbose = verbose
        
    def init(self):
        vmin = 1e9
        vmax = -1e9
        for x in self.radar_data.returns.values():
            vmin = min(vmin, np.minimum.reduce(x.ravel()))
            vmax = max(vmax, np.maximum.reduce(x.ravel()))
        ts0 = sorted(self.radar_data.returns.keys())[0]
        lonmin, lonmax, latmin, latmax = self.radar_data.extent
        xmin, ymin = self.themap.bmap(lonmin, latmin)
        xmax, ymax = self.themap.bmap(lonmax, latmax)
        extent = (xmin, xmax, ymin, ymax)
        self.pc = self.themap.axes.imshow(self.radar_data.returns[ts0], cmap=transparent_red_colormap, vmin=vmin, vmax=vmax, extent=extent)
        return [self.pc]
    
    def animate(self, ts):
        if self.verbose:
            print(".", end='')
        if ts in self.radar_data.returns:
            self.pc.set_array(self.radar_data.returns[ts])
        return [self.pc] 
    
    def make_animation(self, times, interval=20):
        return animation.FuncAnimation(self.themap.fig, self.animate, 
                                       init_func=self.init,
                                       frames=times, 
                                       interval=interval,
                                       blit=True)


