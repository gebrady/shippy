import geopandas as gpd
from shapely.geometry import LineString, Point
import folium
import branca.colormap as cm
import numpy as np
import rasterio
from rasterio.transform import from_origin


# Example GeoDataFrame with LineString geometries and velocity attribute
data = {
    'geometry': [
        LineString([(-118.2437, 34.0522), (-119.4179, 36.7783)]),
        LineString([(-122.4194, 37.7749), (-119.4179, 36.7783)]),
        LineString([(-118.2437, 34.0522), (-122.4194, 37.7749)]),
        LineString([(-118.2437, 34.0522), (-118.2437, 35.0522)]),
        LineString([(-119.4179, 36.7783), (-119.4179, 37.7783)])
    ],
    'velocity': [10, 15, 12, 8, 20]  # Example velocities in knots or any unit
}

gdf_lines = gpd.GeoDataFrame(data, crs="EPSG:4326")


def interpolate_points(line, num_points=100):
    """
    Interpolate points along a LineString.
    
    Args:
    line (LineString): Input LineString.
    num_points (int): Number of points to interpolate.
    
    Returns:
    list: List of interpolated Points.
    """
    distances = np.linspace(0, line.length, num_points)
    points = [line.interpolate(distance) for distance in distances]
    return points

# Example usage
num_points = 100
all_points = []
for line in gdf_lines['geometry']:
    points = interpolate_points(line, num_points=num_points)
    all_points.extend(points)
point_velocities = []
for line, velocity in zip(gdf_lines['geometry'], gdf_lines['velocity']):
    points = interpolate_points(line, num_points=num_points)
    point_velocities.extend([(point, velocity) for point in points])


# Define raster properties
pixel_size = 0.01  # Adjust as needed
west, south, east, north = gdf_lines.total_bounds
width = int((east - west) / pixel_size)
height = int((north - south) / pixel_size)
transform = from_origin(west, north, pixel_size, pixel_size)

# Create an empty raster with a default value (e.g., 0)
raster = np.zeros((height, width), dtype=np.float32)
for point, velocity in point_velocities:
    # Calculate the row and column in the raster corresponding to the point
    col, row = ~transform * (point.x, point.y)
    col, row = int(col), int(row)
    
    # Assign the velocity value to the raster cell, averaging if needed
    if 0 <= row < height and 0 <= col < width:
        raster[row, col] = (raster[row, col] + velocity) / 2  # Averaging

# Save the raster to a file
with rasterio.open(
    'velocity_raster.tif', 'w',
    driver='GTiff', height=height, width=width,
    count=1, dtype=raster.dtype,
    crs=gdf_lines.crs, transform=transform
) as dst:
    dst.write(raster, 1)


# Initialize the folium map
m = folium.Map(location=[36.7783, -119.4179], zoom_start=6)

# Add LineStrings to the map
for line in gdf_lines['geometry']:
    folium.PolyLine(
        locations=[(coord[1], coord[0]) for coord in line.coords],
        color='blue', weight=2
    ).add_to(m)

# Define a colormap
colormap = cm.linear.YlOrRd_09.scale(0, 20)  # Adjust scale to match your velocities

# Add the raster to the map
folium.raster_layers.ImageOverlay(
    image=raster,
    bounds=[[south, west], [north, east]],
    colormap=lambda value: colormap(value)
).add_to(m)

# Add the colormap to the map
colormap.add_to(m)

# Save the map to an HTML file
m.save('./maps/velocity_map.html')
