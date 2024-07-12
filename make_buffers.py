# HELPER FILE TO TEST WRITING IF BUFFERS
import geopandas as gpd
from ship import *
from app import *
from shapely.geometry import Point

coords = []
for key, value in Cruise.CRUISE_DOCKS.items():
    coords.append((value['coordinates'], key))

points = [Point(coord[0]) for coord in coords]
names = [coord[1] for coord in coords]

docks = gpd.GeoDataFrame({'geometry': points}, crs = "EPSG:4326")

docks['name'] = names

docks.to_file(r'./shapes/dock_points_wgs84.shp', driver='ESRI Shapefile')

#docks_albers = docks
docks_albers = docks.to_crs(epsg=3338)

print(f'Docks crs: {docks.crs} WGS84 : {docks}')
#docks_albers = docks.to_crs(3338)
print(f'Docks crs: {docks_albers.crs} Albers : {docks_albers}')

# Create buffer around the first point in the projected CRS
search_radius = 2000  # Buffer radius in meters (since EPSG:3338 is in meters)

docks_albers['buffer'] = docks_albers.geometry.buffer(search_radius)
# Convert the buffer to a GeoDataFrame
buffers = gpd.GeoDataFrame(docks_albers['name'], geometry=docks_albers['buffer'], crs=docks_albers.crs)
# Export the buffer to a shapefile
buffers.to_file(r'./buffers/docks_albers_2000m_buffer.shp', driver='ESRI Shapefile')