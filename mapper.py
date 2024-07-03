import folium
import pandas as pd
import geopandas as gpd
from geopy.distance import distance
from shapely.geometry import Point, LineString
from app import *
import random
import colorsys
import numpy as np

###### SETUP FOLIUM WITH GLACIER BAY BOUNDARY ######

# Read the shapefile
glba = gpd.read_file('./shapes/nps_boundary.shp')
glba = glba[glba.PARKNAME == 'Glacier Bay']
glba = glba.to_crs(epsg=4326)

for col in glba.columns:
    if pd.api.types.is_datetime64_any_dtype(glba[col]):
        glba[col] = glba[col].astype(str)

center = (58.58566454530601, -136.04670618412524)
m = folium.Map(location=center, zoom_start=9)

# Add the GeoDataFrame to the map
folium.GeoJson(glba).add_to(m)

########## HELPER FUNCTIONS #######

# Function to convert a DataFrame to a GeoDataFrame
def cruiseData_to_cruiseGeoData(cruiseID, cruiseData, lat_col, lon_col):
    # Create geometry column from latitude and longitude columns
    geometry = [Point(xy) for xy in zip(cruiseData.data[lon_col], cruiseData.data[lat_col])]
    # Convert DataFrame to GeoDataFrame
    cruiseData.data['cruiseID'] = cruiseID
    #print(cruiseData.data)
    gdf = gpd.GeoDataFrame(cruiseData.data, geometry=geometry)
    #print(gdf)
    # Set CRS to WGS 84 (EPSG:4326)
    gdf.set_crs(epsg=4326, inplace=True)
    return gdf

def cruiseDataToPolyline(cruiseData):
    gdf_points = gpd.GeoDataFrame(
        cruiseData.data,
        geometry = gpd.points_from_xy(cruiseData.data['lon'], cruiseData.data['lat'])
    )
    line = LineString(gdf_points.geometry.tolist())
    # Create a GeoDataFrame for the polyline
    gdf_line = gpd.GeoDataFrame(
        {'cruiseID': [gdf_points['cruiseID'].iloc[0]]},  # Inherit an attribute from the first point
        geometry=[line]
    )
    #gdf_line.set_crs(epsg=4326, inplace=True)
    return gdf_line

######## BEGIN WORKING WITH AIS CRUISE DATA 2023 ############

a = App(r'/Users/Graham/cruise/small_ais_data')
#a = App(r'/Users/Graham/cruise/test_data')

gdfs = []
gdfs_line = []

for boat_name, boat_data in a.boatsData.boatsDataDictionary.items():
            for cruise_id, cruise_data in boat_data.cruisesDataDictionary.items():
                cruiseGeoData = cruiseData_to_cruiseGeoData(cruise_id, cruise_data, 'lat', 'lon')
                cruiseLine = cruiseDataToPolyline(cruise_data)
                gdfs.append(cruiseGeoData)
                gdfs_line.append(cruiseLine)
                #cruiseGeoData.to_file(os.path.join(r'/Users/Graham/cruise/cruiseGeodata', cruise_id), driver='ESRI Shapefile')

for gdf in gdfs:
    for col in gdf.columns:
        if pd.api.types.is_datetime64_any_dtype(gdf[col]):
            gdf[col] = gdf[col].astype(str)
    #folium.GeoJson(gdf).add_to(m)
    print(f'adding gdf: {gdf.cruiseID}')
    break

for gdf_line in gdfs_line:
    gdf_line.set_crs(epsg=4326, inplace=True)

def generate_distinguishable_colors(num_colors):
    """
    Generate a list of distinguishable colors.
    Args: num_colors (int): Number of unique colors needed.
    Returns: List of color codes in RGB format.
    """
    colors = []
    for i in range(num_colors):
        hue = i / float(num_colors)
        rgb = colorsys.hsv_to_rgb(hue, 0.8, 0.8)  # Use a constant saturation and value
        rgb = tuple(int(255 * x) for x in rgb)
        colors.append('#{:02x}{:02x}{:02x}'.format(*rgb))
    return colors

def generate_color_mapping(gdf, id_column):
    """
    Generate a dictionary mapping unique IDs to unique RGB color codes.
    Args: gdf (GeoDataFrame): GeoDataFrame containing LineString geometries and a unique ID column.
    id_column (str): Column name containing unique IDs.
    Returns: Dictionary with IDs as keys and unique RGB color codes as values.
    """
    unique_ids = gdf[id_column].unique() 
    colors = generate_distinguishable_colors(len(unique_ids))
    color_mapping = {cruise_id: color for cruise_id, color in zip(unique_ids, colors)}
    return color_mapping

def get_color(category):
    return color_dict.get(category, 'black')  # Default to 'black' if category not found

def plot_lines_with_folium(gdf, id_column, color_mapping):
    """
    Plot lines from a GeoDataFrame on a Folium map with colors based on unique ID.
    
    Args:
    gdf (GeoDataFrame): GeoDataFrame containing LineString geometries.
    id_column (str): Column name containing unique IDs.
    color_mapping (dict): Dictionary mapping IDs to unique RGB color codes.
    
    Returns:
    folium.Map: Folium map with plotted lines.
    """
    # Initialize the folium map centered around the first LineString's midpoint
    center = (58.58566454530601, -136.04670618412524)  # Adjust as needed for your data
    m = folium.Map(location=center, zoom_start=10)
    
    # Iterate over the GeoDataFrame and add each LineString to the map
    for _, row in gdf.iterrows():
        # Get the color for the current row's ID
        color = color_mapping[row[id_column]]
        
        # Create a folium PolyLine and add it to the map
        folium.PolyLine(
            locations=[(coord[1], coord[0]) for coord in row['geometry'].coords],
            color=color,
            weight=5  # Adjust the weight as needed
        ).add_to(m)
    
    return m

# Example usage

# Create a GeoDataFrame
data = {
    'geometry' : [gdf_line.geometry[0] for gdf_line in gdfs_line],
    'cruiseID' : [gdf_line.cruiseID[0] for gdf_line in gdfs_line]
}

gdf_lines = gpd.GeoDataFrame(data, crs="EPSG:4326")
# Assuming you have a GeoDataFrame 'gdf_lines' with a column 'cruiseID'

color_mapping = generate_color_mapping(gdf_lines, 'cruiseID')

# Plot lines with folium
m = plot_lines_with_folium(gdf_lines, 'cruiseID', color_mapping)

# Optionally, save the map to an HTML file
m.save('./maps/map_glba.html')



