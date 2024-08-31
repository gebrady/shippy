import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import numpy as np
import rasterio
from rasterio.features import rasterize
from rasterio.transform import from_origin

#cruises_shp_filepath = r'./data/cruises_shp/ais_in_glba.shp'
cruises_shp_filepath = r'./data/cruises_shp/processed_cruises.shp'

# Load the data
gdf = gpd.read_file(cruises_shp_filepath)
gdf = gdf.to_crs(6394)

# Define the grid parameters
cell_size = 250  # meters
xmin, ymin, xmax, ymax = gdf.total_bounds
width = int((xmax - xmin) / cell_size)
height = int((ymax - ymin) / cell_size)

# Create an empty array to hold the sum of values and counts
sum_grid = np.zeros((height, width), dtype=np.float64)
count_grid = np.zeros((height, width), dtype=np.int64)

# Function to update the grids
def update_grids(geom, value):
    x, y = geom.xy
    row = min(max(int((y[0] - ymin) / cell_size), 0), height - 1)
    col = min(max(int((x[0] - xmin) / cell_size), 0), width - 1)
    
    sum_grid[row, col] += value
    count_grid[row, col] += 1

# Update grids with the values from the GeoDataFrame
gdf.apply(lambda row: update_grids(row.geometry, row['sog']), axis=1)

# Calculate the average values
average_grid = np.divide(sum_grid, count_grid, out=np.zeros_like(sum_grid), where=count_grid != 0)

#average_grid = np.rot90(average_grid, 2)

# Define the transform for the raster
transform = from_origin(xmin, ymin, cell_size, -cell_size)

# Write the average values to a new raster file
output_raster = './out/cruise_rasters/mean_sog_raster_250m.tif'
with rasterio.open(
    output_raster,
    'w',
    driver='GTiff',
    height=height,
    width=width,
    count=1,
    dtype=average_grid.dtype,
    crs=gdf.crs,
    transform=transform
) as dst:
    dst.write(average_grid, 1)
