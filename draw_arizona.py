from __future__ import print_function

import numpy as np
import fiona
from collections import namedtuple
from matplotlib import pyplot as plt
from matplotlib.path import Path
from matplotlib.collections import PathCollection
from mpl_toolkits.basemap import Basemap

# We pass around (figure, axes, basemap) a lot, so wrap them in a namedtuple
MapData = namedtuple('MapData', ["fig", "axes", "bmap"])

def draw_arizona(min_lon=-115.0, max_lon=-109.0, min_lat=30.0, max_lat=38.0, figsize=(6,6)):
    fig = plt.figure(figsize=figsize)
    ax = fig.add_axes([0.1,0.1,0.8,0.8])
    m = Basemap(projection='merc', llcrnrlat=min_lat, urcrnrlat=max_lat, llcrnrlon=min_lon, urcrnrlon=max_lon, resolution='c')
    m.shadedrelief(scale=0.25)
    m.drawcountries()
    m.drawstates()
    m.drawcounties(linewidth=0.3)
    return MapData(fig, ax, m)

def draw_roads(themap, types=['motorway']):
    # This might be doable with basemap.readshapefile, but this seems cleaner
    # Shapefile downloaded from www.openstreetmap.org and www.mapcruzin.com 
    # (http://www.mapcruzin.com/download-shapefile/us/arizona_highway.zip)
    with fiona.open('shapefiles/arizona_highway/arizona_highway.shp', 'r') as source:
        types = set(types)
        road_coords = []
        for road in source:
            if road['properties']['TYPE'] not in types:
                continue
            geom = road['geometry']
            assert geom['type'] == 'LineString'
            # A LineString geometry is a list of (x, y) coordinate values.
            coords = geom['coordinates']
            lons, lats = np.array(coords).T
            # lons and lats are in degrees, but we need them them in plot coordinates. Conveniently, 
            # passing lat/lon to basemap instanace results in a set of plot coordinates.
            transformed = np.array(themap.bmap(lons, lats)).T
            # Use the plot coordinates to create a matplotlib Path instance, then store that away for future use.
            road_coords.append(Path(transformed))
        # Create a PatchCollection from the road Paths and plot it. 
        themap.axes.add_collection(PathCollection(road_coords, facecolors='none', edgecolors="brown", linewidth=1))