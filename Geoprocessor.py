import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, LineString
from PortManager import PortManager
import os

from PathCalculations import PathCalculations

class Geoprocessor():
    GLBA_BOUNDARY = gpd.read_file(r'./data/shapes/GlacierBayGeofence.shp')
    GLBA_BOUNDARY = GLBA_BOUNDARY.set_crs(epsg=4326)
    PROJECT_EPSG = 4326

    def __init__(self, data):
        self.gdf = data

        self.portManager = PortManager(self)

    ######## CONVERSION #######
    @staticmethod
    def dataToGeodata(data): # Convert self.data to a geodataframe
        """Converts a populated self.data to a geodataframe and stores it as self.gdf
        """
        #print('converting data to geodata')
        if 'lat' in data.columns and 'lon' in data.columns: #brief check for xy contents, return gdf with None geometry if not
            geometry = [Point(xy) for xy in zip(data['lon'], data['lat'])]
            #points_gdf = gpd.GeoDataFrame(data, geometry=gpd.points_from_xy(data['longitude'], data['latitude'])) 
            # ^^ another way to do it
            gdf = gpd.GeoDataFrame(data, geometry=geometry)
            gdf.set_crs(epsg=4326, inplace=True)
            gdf = gdf.set_geometry(geometry)
            return gdf
        else:
            print('error') 
            return gpd.GeoDataFrame(data, geometry=None)
    
    ######## CLIPPING #######
    def clip(self, boundary, within = True):
        """clips geodata to within the boundary unless specified"""
        if within:
            return self.gdf[self.gdf.geometry.within(boundary.geometry.unary_union)]
        else:
            return self.gdf[~self.gdf.geometry.within(boundary.geometry.unary_union)]
        
    @staticmethod
    def clip2(gdf, boundary, within = True):
        """clips geodata to within the boundary unless specified"""
        if within:
            return gdf[gdf.geometry.within(boundary.geometry.unary_union)]
        else:
            return gdf[~gdf.geometry.within(boundary.geometry.unary_union)]

    ######## EXPORTING ########

    @staticmethod 
    def toPointShapefile(cruise, filepath):
        # Create geometries from lon and lat
        gdf = cruise.data
        gdf.set_crs(epsg=4326, inplace=True)
        
        # Add additional information
        gdf['cruiseID'] = cruise.cruiseID
        gdf['boatName'] = cruise.boatName
        gdf['startDate'] = str(min(cruise.days))
        gdf['endDate'] = str(max(cruise.days))

#       gdf['departGLBA'] = str(cruise.getLastTimestampInGlacierBay()) #edit these 
#       gdf['afterGLBA'] = cruise.getPortAfterGlacierBay() #edit these

        gdf.to_file(os.path.join(os.getcwd(), filepath), driver='ESRI Shapefile')

    @staticmethod
    def appendToPointShapefile(cruise, filepath):
        """Adds the self.gdf entries to the shapefile at filepath. If the file doesn't exist, then creates one."""
        full_path = os.path.join(os.getcwd(), filepath)
        gdf = cruise.data
        
        # Add additional information
        gdf['cruiseID'] = cruise.cruiseID
        gdf['boatName'] = cruise.boatName
        gdf['startDate'] = pd.to_datetime(str(min(cruise.days)))
        gdf['endDate'] = pd.to_datetime(str(max(cruise.days)))

#       gdf['departGLBA'] = str(cruise.getLastTimestampInGlacierBay()) #edit these 
#       gdf['afterGLBA'] = cruise.getPortAfterGlacierBay() #edit these

        if os.path.exists(full_path):
            existing_gdf = gpd.read_file(full_path)
            gdf = pd.concat([existing_gdf, gdf], ignore_index=True)

        gdf.to_file(full_path, driver='ESRI Shapefile')
    
    @staticmethod          
    def toLineShapefile(cruise, filepath, start_index, end_index):
        if start_index and end_index:
            line = LineString(cruise.data.loc[start_index:end_index].geometry.values)
            distance = PathCalculations.distanceAlongPath(cruise.data.geometry, start_index, end_index)[1]
            time = PathCalculations.timelapseAlongPath(cruise.data.bs_ts ,start_index, end_index)

        else: 
            line = LineString(cruise.data.geometry.values)
            distance = PathCalculations.distanceAlongPath(cruise.data.geometry, cruise.data.index[0], cruise.data.index[-1])[1]
            time = PathCalculations.timelapseAlongPath(cruise.data.bs_ts, cruise.data.index[0], cruise.data.index[-1])

        new_row = {
            'cruiseID': cruise.cruiseID,
            'boatName': cruise.boatName,
            'startDate': str(min(cruise.days)),
            'endDate': str(max(cruise.days)),
            # 'departGLBA': str(cruise.getLastTimestampInGlacierBay()), # fix these
            # 'afterGLBA': cruise.getPortAfterGlacierBay(),  # Fix these
            'distance' : distance,
            'time' : time
        }

        # Create a new GeoDataFrame with the new row
        line_gdf = gpd.GeoDataFrame([new_row], geometry=[line], crs=cruise.data.crs)
        line_gdf.set_crs(epsg=4326, inplace=True)
        line_gdf.to_file(os.path.join(os.getcwd(), filepath), driver='ESRI Shapefile')


    ######## FLATTENING DATA #######

    @staticmethod
    def aggregate(gdf_list):
        return pd.concat(gdf_list, ignore_index=True)

########## SCRATCH AREA ######################

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
    

    

