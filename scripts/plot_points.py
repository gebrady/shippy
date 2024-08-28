import geopandas as gpd
from ship import *
from app import *
import matplotlib.pyplot as plt
from shapely.geometry import Point

coords = []
for key, value in Cruise.CRUISE_DOCKS.items():
    coords.append((value['coordinates'], key))

points = [Point(coord[0]) for coord in coords]
names = [coord[1] for coord in coords]

docks = gpd.GeoDataFrame({'geometry': points}, crs = "EPSG:4326")

docks['name'] = names

docks.to_file(r'./shapes/dock_points_wgs84.shp', driver='ESRI Shapefile')

# Reproject to Alaska Albers (EPSG:3338)
gdf_projected = docks.to_crs(epsg=3338)

# Load Alaska boundary from Natural Earth dataset
alaska = gpd.read_file(r'/Users/Graham/cruise/shapes/Alaska_Coastline/Alaska_Coastline.shp')
alaska = alaska.to_crs(epsg=3338)

# Plot the points on Alaska map
fig, ax = plt.subplots(1, 1, figsize=(10, 10))

# Add Alaska boundary for context
alaska.boundary.plot(ax=ax, linewidth=1, edgecolor='black')

# Plot the points
gdf_projected.plot(ax=ax, color='red', markersize=50)

# Set plot title and labels
ax.set_title("Cruise Docks in Alaska (Alaska Albers Projection)")
ax.set_xlabel("Easting (meters)")
ax.set_ylabel("Northing (meters)")

plt.show()
