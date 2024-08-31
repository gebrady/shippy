
from BoatsData import BoatsData

import geopandas as gpd
from shapely.geometry import Point
import rasterio
import numpy as np
from rasterio.features import rasterize
from rasterio.transform import from_origin
from rasterio.plot import show


import numpy as np
import matplotlib.pyplot as plt
import rasterio
from shapely.geometry import box
from rasterio.plot import show


class Mapper:
    def __init__(self, data):
        self.data = data

    def writeRasters(self, group_field, plot_field):
        gdf = self.data.to_crs(6394)

        ##### FILTER #####
        def update_grids(geom, value):
            x, y = geom.xy
            row = min(max(int((y[0] - ymin) / cell_size), 0), height - 1)
            col = min(max(int((x[0] - xmin) / cell_size), 0), width - 1)
        
            sum_grid[row, col] += value
            count_grid[row, col] += 1

        #####################

        cell_size = 500  # meters

        grouped = gdf.groupby(group_field)

        rasters = {}

        for key, group in grouped:
            df = group[group[group_field] == key]

            #print(df.sog.mean())

            xmin, ymin, xmax, ymax = df.total_bounds
            width = int((xmax - xmin) / cell_size)
            height = int((ymax - ymin) / cell_size)

            sum_grid = np.zeros((height, width), dtype=np.float64)
            count_grid = np.zeros((height, width), dtype=np.int64)

            df.apply(lambda row: update_grids(row.geometry, row[plot_field]), axis=1)
            average_grid = np.divide(sum_grid, count_grid, out=np.zeros_like(sum_grid), where=count_grid != 0)
            transform = from_origin(xmin, ymin, cell_size, -cell_size)
            key_name = key.replace(' ','_')
            output_raster = f'./products/rasters/mean_{plot_field}_raster_{cell_size}m_glba_to_{key_name}_cruises.tif'
            #print(f'writing {output_raster}')
        
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

            extent = [xmin, xmax, ymin, ymax]

            rasters[key] = (group_field, plot_field, output_raster, cell_size, extent)

        return rasters
    
    @staticmethod
    def plotRaster(key, rasters_dict):
        vector_data = BoatsData.ALASKA_COASTLINE.to_crs(6394)

        raster_file = rasters_dict[key][2]
        extent = rasters_dict[key][4]
        #print(f"Extent: {extent}")

        with rasterio.open(raster_file) as src:
            #img = np.flipud(src.read(1))  # Read and flip the image
            img = src.read(1)
            transform = src.transform
            crs = src.crs

            fig, ax = plt.subplots(figsize=(10, 10))

            # Display raster data
            show(img, cmap='inferno', ax=ax, transform=transform, extent=extent)

            vector_data = vector_data.to_crs(crs)
            vector_data.boundary.plot(ax=ax, edgecolor='white', linewidth=1)  # Overlay vector boundaries

            ax.set_xlim([extent[0], extent[1]])
            ax.set_ylim([extent[2], extent[3]])
            cbar = plt.colorbar(ax.images[0], ax=ax, orientation='vertical')
            cbar.set_label('Mean SOG (kt)')
            ax.set_xlabel('Longitude')
            ax.set_ylabel('Latitude')
            ax.set_title(f"Mean SOG GLBA to {key}")

            # Show the plot
            plt.show()
