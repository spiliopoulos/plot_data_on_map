from mpl_toolkits.basemap import Basemap
from geopy.geocoders import Nominatim
from sys import argv
import matplotlib.pyplot as plt
import numpy as np
import pickle

geo_cache_file = "./geo_cache.pickle"

locations = [
    "New York",
    "USA",
    "Brazil",
    "Canada",
    "Germany",
    "Italy",
    "India",
    "Russia",
    "UK",
    "Australia"
]

class GeoCache():
    def __init__(self, path_to_file):
        self.path_to_file = path_to_file
        self.geolocator = Nominatim()
        self.cache = {}
        try:
            with open(self.path_to_file, "rb") as f:
                self.cache = pickle.load(f)
        except FileNotFoundError:
            print("Cache file not found.\nCreating an empty one")
            with open(self.path_to_file, "wb") as f:
                pickle.dump({}, f)
    
    def __enter__(self):
        return self
    
    def __exit__(self, type, value, traceback):
        with open(self.path_to_file, "rb+") as f:
            old = pickle.load(f)
            old.update(self.cache)
            f.seek(0)
            pickle.dump(old, f)

    def get_geo_info_for_locations(self, locations):
        geo_info = {}
        geolocator = self.geolocator
        for location in locations:
            try:
                geo_info[location] = self.cache[location]
            except KeyError:
                print("{} missing from cache!".format(location))
                print("Asking OpenStreetMaps...")
                geo_code = geolocator.geocode(location)
                print("{} is {}".format(location, geo_code.raw))
                self.cache[location] = geo_code
                geo_info[location] = geo_code
        return geo_info

if len(argv) < 3:
    print("{} DataFile PlotFile")
# set up orthographic map projection with
# perspective of satellite looking down at 50N, 100W.
# use low resolution coastlines.
# don't plot features that are smaller than 1000 square km.
map = Basemap(
    projection='merc',
    llcrnrlat=-80,
    urcrnrlat=80,
    llcrnrlon=-180,
    urcrnrlon=180,
    lat_ts=20,
    resolution = 'l',
    area_thresh = 1000.
)
# draw coastlines, country boundaries, fill continents.
#map.drawcoastlines()
map.drawcountries()
map.fillcontinents(color = 'coral')
# draw the edge of the map projection region (the projection limb)
map.drawmapboundary()
# draw lat/lon grid lines every 30 degrees.
#map.drawmeridians(np.arange(0, 360, 30))
#map.drawparallels(np.arange(-90, 90, 30))

with open(argv[1], "rb") as datafile:
    data, baseline = pickle.load(datafile)
locations = list(data.keys())

with GeoCache(geo_cache_file) as geocache:
    geo_info = geocache.get_geo_info_for_locations(locations)
lons, lats = zip(*(
    [
        (geo_info[location].longitude, geo_info[location].latitude)
        for location in locations
    ]
))

unit_arrow_length = 1800000
unit_arrow_width = 250000
unit_arrow_head_width = 3 * unit_arrow_width

# compute the native map projection coordinates for cities.
x,y = map(lons,lats)
# plot filled circles at the locations of the cities.
map.plot(x,y,'bo')
for x1,y1,location in zip(x,y,locations):
    #y1 -= (unit_arrow_length / 2.0)
    datum = data[location]
    datum = (datum / float(baseline))
    color = 'black'
    if datum > 1:
        color = 'crimson'
    elif datum < 1:
        color = 'springgreen'
    plt.arrow(
        x1, y1, 0, datum * unit_arrow_length,
        width=unit_arrow_width,
        head_width=unit_arrow_head_width,
        color=color,
        alpha=1.0
    )
# plot the names of those five cities.
for name,xpt,ypt in zip(locations,x,y):
    plt.text(xpt+50000,ypt+50000,name)

#plt.show()
plt.savefig(argv[2], dpi=1000, format="png")
