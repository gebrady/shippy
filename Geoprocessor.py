import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, LineString
from PortManager import PortManager
import os


class Geoprocessor():
    PROJECT_EPSG = 4236

    def __init__(self, data):
        self.gdf = self.dataToGeodata(data)
        self.gdf_clipped = None

        self.portManager = PortManager(self)

        
    def dataToGeodata(self, data): # Convert self.data to a geodataframe
        """Converts a populated self.data to a geodataframe and stores it as self.gdf
        """
        geometry = [Point(xy) for xy in zip(data['lon'], data['lat'])]
        #points_gdf = gpd.GeoDataFrame(data, geometry=gpd.points_from_xy(data['longitude'], data['latitude'])) 
        # ^^ another way to do it
        gdf = gpd.GeoDataFrame(data, geometry=geometry)
        gdf.set_crs(epsg=4236, inplace=True)
        return gdf
    
    
    def fillPointsWithinGlacierBay(self):
        """Populates new inGLBA column as True or false depending on intersection with the GLBA boundary polygon. 
           Will be used to determine exit time from GLBA
        """
        search_area = PortManager.GLBA_BOUNDARY
        search_area = search_area.to_crs(4326)
        self.gdf['inGLBA'] = None #initialize column and set default to None type
        
        intersecting_points = self.gdf[self.gdf.geometry.intersects(search_area.geometry.unary_union)]
        intersecting_indices = intersecting_points.index
        if not intersecting_indices.empty:
            self.gdf.loc[intersecting_indices, 'inGLBA'] = True

            last_true_index = intersecting_indices[-1]
            next_index = self.gdf.index[self.gdf.index > last_true_index][0] if last_true_index < self.gdf.index[-1] else None

            #print(f"Last True Index: {last_true_index}, Next Index: {next_index}")
        else:
            print("No intersecting points found.")

        return next_index
    

    




    def clipBoundary(self, boundary):
        """writes shapefile of cruiseData, using the boundary polygon to subset the geodataframe
        """
        if not self.gdf_clipped:
            gdf_sub = self.gdf[self.gdf.geometry.within(boundary.geometry.unary_union)]
            self.gdf_clipped = gdf_sub
        else:
            print('error in clipboundary')

    def toPointShapefile_og(self, filepath):
        """Converts a Cruise object to a shapefile and writes it to filepath.
           filepath takes .shp extension
        """
        self.gdf.to_file(os.path.join(os.getcwd(), filepath))

    
  
