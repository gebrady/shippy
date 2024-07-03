import folium
import geopandas as gpd
from geopy.distance import distance
from shapely.geometry import Point

from app import *

# Read the shapefile
gdf = gpd.read_file('./shapes/nps_boundary.shp')
gdf = gdf[gdf.PARKNAME == 'Glacier Bay']
gdf = gdf.to_crs(epsg=4326)

# Initialize the folium map centered around Los Angeles
center = (58.58566454530601, -136.04670618412524)

m = folium.Map(location=center, zoom_start=9)

for col in gdf.columns:
    if pd.api.types.is_datetime64_any_dtype(gdf[col]):
        gdf[col] = gdf[col].astype(str)

# Add the GeoDataFrame to the map
folium.GeoJson(gdf).add_to(m)

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


a = App(r'/Users/Graham/cruise/small_ais_data')

gdfs = []

for boat_name, boat_data in a.boatsData.boatsDataDictionary.items():
            for cruise_id, cruise_data in boat_data.cruisesDataDictionary.items():
                cruiseGeoData = cruiseData_to_cruiseGeoData(cruise_id, cruise_data, 'lat', 'lon')
                gdfs.append(cruiseGeoData)
                #cruiseGeoData.to_file(os.path.join(r'/Users/Graham/cruise/cruiseGeodata', cruise_id), driver='ESRI Shapefile')

for gdf in gdfs:
    for col in gdf.columns:
        if pd.api.types.is_datetime64_any_dtype(gdf[col]):
            gdf[col] = gdf[col].astype(str)
    folium.GeoJson(gdf).add_to(m)
    print(f'adding gdf: {gdf.cruiseID}')
    break

# Optionally, save the map to an HTML file
m.save('./maps/map_glba.html')

#a = App(r'/Users/Graham/cruise/test_data')
