import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
import folium
from folium.plugins import TimestampedGeoJson
import json

# # Sample data creation
# data = {
#     'latitude': [37.77, 37.78, 37.79, 37.80],
#     'longitude': [-122.42, -122.43, -122.44, -122.45],
#     'timestamp': ['2023-01-01T00:00:00Z', '2023-01-02T00:00:00Z', '2023-01-03T00:00:00Z', '2023-01-04T00:00:00Z']
# }

# # Create DataFrame
# df = pd.DataFrame(data)

# # Create GeoDataFrame with CRS
# gdf = gpd.GeoDataFrame(
#     df, geometry=gpd.points_from_xy(df.longitude, df.latitude),
#     crs="EPSG:4326"
# )

# # Save to shapefile (if you already have a shapefile, skip this step)
# gdf.to_file('points_with_timestamps.shp')

# Load the shapefile (assuming you have one)
gdf = gpd.read_file('/Users/Graham/cruise/cruises_shp/processed_cruises.shp')

# Convert GeoDataFrame to GeoJSON
geojson = json.loads(gdf.to_json())

# Add 'time' property to each feature
for feature in geojson['features']:
    feature['properties']['time'] = feature['properties']['bs_ts']
    feature['properties']['name'] = feature['properties']['boatName']
    feature['properties']['speed'] = feature['properties']['sog']


# Save GeoJSON to a file (optional)
with open('points_with_timestamps.geojson', 'w') as f:
    json.dump(geojson, f)

# Create a base map
m = folium.Map(location=[58.626732625571684, -136.07959678862855], zoom_start=12)

# Add TimestampedGeoJson layer
TimestampedGeoJson(
    geojson,
    period='PT5M',  # One day intervals
    add_last_point=False,
    auto_play=False,
    loop=False,
    max_speed=24,
    loop_button=True,
    date_options='YYYY-MM-DD',
    time_slider_drag_update=True,
    duration='PT5M'  # Make the points disappear after one day
).add_to(m)

# Save the map to an HTML file
m.save('timestamped_map.html')
