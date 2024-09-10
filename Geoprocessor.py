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
            print('error: no lat/lon') 
            print(data.columns)
            return gpd.GeoDataFrame(data, geometry=None)
        
    ######## ASSESSING MANAGEMENT ALTERNATIVES ########

    @staticmethod
    def generate_management_alternatives(data, group_field, list_of_adjustments):
        """takes the `data` table of a cruise and returns a GeoDataFrame with new fields containing
           calculated sog's and bs_ts's given the scenarios in `list_of_adjustments`, a list of 
           management alternatives in integer format and minutes units. 
           For example: Geoprocessor.reapportionTimes(data, [-30, -15, 15, 30]) would add 8 columns
           to the return data, bs_ts and sog appended with either dec30, dec15, inc15, inc30 as a siffix
           for the scenarios given: an increased 30 minutes for the trip from start of data to end of data

           Read on the math in the jupyter notebooks...
        """

        alts = {}
        for group_id, group in data.groupby(group_field):
            for inc in list_of_adjustments:
                if inc > 0:
                    key = 'inc_' + str(inc) # if positive, "increase by 15 minutes"
                elif inc < 0:
                    key = 'dec_' + str(abs(inc)) #else "decrease by 15" and remove negative symbol
                key = group_id.replace(' ','_') + '_' + key
                alts[key] = Geoprocessor.reapportion_timestamps_sogs(group, inc)

        return alts

    @staticmethod
    def reapportion_timestamps_sogs(data, increment):
        """helper function to add field for the increment (integer in minutes)"""
        adj = data.sort_values(by='bs_ts').reset_index(drop=True)
        adj['delta_t'] = adj['bs_ts'].diff().dt.total_seconds() / 60 # get timedelta in minutes
        T = adj['delta_t'].sum() # T_original = (adj.bs_ts.iloc[-1] - adj.bs_ts.iloc[0]) assert this is correct
        ratio = (T + increment) / T # increment in minutes

        adj['delta_t_new'] = adj['delta_t'] * ratio
        adj['sog_new'] = adj['sog'] / ratio
        adj['bs_ts_new'] = adj['bs_ts'].iloc[0] + pd.to_timedelta(adj['delta_t_new'].cumsum().fillna(0), unit='m')

        return adj
    
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

    @staticmethod
    def boatsDataToLinesShapefile(BoatsData, filepath):
        new_row = {}
        rows = []
        for boatName, boatData in BoatsData.boatsDataDictionary.items():
            #print(boatData)
            for cruise_id, cruise_data in boatData.cruisesDataDictionary.items():
                #print(cruise_data)
                line = LineString(cruise_data.data.geometry.values)
                #print(line)
                new_row = {
                    'boatName': boatName,
                    'cruiseID': cruise_id,
                    'startDate': str(min(cruise_data.days)),
                    'endDate': str(max(cruise_data.days)),
                    'geometry': line
                    #'distance' : distance,
                    #'time' : time
                }
                rows.append(new_row)

        line_gdf = gpd.GeoDataFrame(rows, geometry = 'geometry', crs=cruise_data.data.crs)
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
    

    

