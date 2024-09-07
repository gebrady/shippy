import pandas as pd
import geopandas as gpd
import numpy as np


class PortManager():
    GLBA_BOUNDARY = gpd.read_file(r'./data/shapes/port_GLBA.shp')
    GLBA_BOUNDARY = GLBA_BOUNDARY.set_crs(epsg=4326)
    DOCK_BUFFERS = gpd.read_file(r'./data/buffers/docks_albers_2000m_buffer.dbf')
    #DOCK_BUFFERS = DOCK_BUFFERS.set_crs(epsg=4326)
    
    def __init__(self, geoprocessor):
        self.geoprocessor = geoprocessor

    @staticmethod
    def populate_status_and_ports(df):
        """determines if rows are inPort or inTransit and updates cruise_geodata table"""
        search_area = PortManager.DOCK_BUFFERS
        search_area = search_area.to_crs(4326)

        if not isinstance(df, gpd.GeoDataFrame):
            raise TypeError("df must be of type GeoDataFrame")
    
        df = df.set_geometry('geometry')

        df['port'] = None # default port field to None
        df['status'] = None  # Default status field to 'inTransit'

        # Iterate over all ports in the search area, check if any points intersect and are at rest/moored
        for _, buffer in search_area.iterrows():
            withinPortBoundary = df[df.geometry.intersects(buffer.geometry)]
            intersection = withinPortBoundary.index

            # # OLD APPROACH USING MOORING AND SOG CONSTRAINTS IN ADDITION TO BUFFERS
            # if buffer['name'] not in ['Endicott Arm', 'Tracy Arm', 
            #                           'College Fjord', 'Hubbard Glacier', 
            #                           'Glacier Bay', 'Misty Fjords']:
            #     mooredPoints = df[(df.sog == 0) | (df.nav_status == 'Moored')]
            #     intersection = withinPortBoundary.index.intersection(mooredPoints.index)

            # else:
            #     intersection = withinPortBoundary.index

            if len(intersection) > 0: # if matches exist
                df.loc[intersection, 'port'] = buffer['name']
                df.loc[intersection, 'status'] = 'inPort'

        df['port'].fillna('atSea', inplace=True)
        df['status'].fillna('inTransit', inplace=True)

        port_changes = df['port'].ne(df['port'].shift())

        inPortIndices = df[df['status'] == 'inPort'].index

        df['next_port'] = df['port'].where(port_changes).shift(-1).bfill()

        df['previous_port'] = df['port'].shift().where(port_changes).ffill()

        return df

    @staticmethod
    def identify_status_changes(df):
        """detects change in state over course of AIS data, assigns incremental IDs 
           to those segments of a particular state for creation of DLL for Cruise sorting
           
           generates segment_id values
        """

        df['status_change'] = df['status'] != df['status'].shift(1) # create temp field bool for if current row diff status than prev
        df['segment_id'] = df['status_change'].cumsum()
        df['segment_number'] = df['status_change'].cumsum()
        boatName = df['name'].mode()[0].replace(' ', '_')
        df['segment_id'] = df.apply(lambda row: f"{boatName}_{row['segment_number']:04}", axis=1)
        df.drop(columns=['status_change', 'segment_number'], inplace=True)

        return df
    
    #updates cruise.data
    @staticmethod #???????
    def assignPorts(cruise):
        """Adds columns that specify the location as either within a port or in transit between ports.
        Port location is determined by containment of an AIS point within a 2km circular buffer around ports of interest.
        Adds columns: 'port', 'status' (either 'inPort' or 'inTransit'), and 'next_port' to the DataFrame.
        """
        search_area = PortManager.DOCK_BUFFERS.to_crs(4326)

        cruise.data['port'] = None # default port field to None
        cruise.data['status'] = 'inTransit'  # Default status field to 'inTransit'
        cruise.data['next_port'] = None #default next_port



        #assign start and end port/status
        cruise.data.at[cruise.data.index[0], 'port'] = 'StartOfCruise'
        cruise.data.at[cruise.data.index[-1], 'port'] = 'EndOfCruise' # default for now since we don't have many Seattle/CAN cruises
                
        cruise.data.at[cruise.data.index[0], 'status'] = 'inPort'
        cruise.data.at[cruise.data.index[-1], 'status'] = 'inPort'

        
        # Iterate over all ports in the search area, check if any points intersect and are at rest/moored
        for _, buffer in search_area.iterrows():
            if buffer['name'] not in ['Endicott Arm', 'Tracy Arm', 
                                      'College Fjord', 'Hubbard Glacier', 
                                      'Glacier Bay', 'Misty Fjords']:
                intersecting_points1 = cruise.data[cruise.data.geometry.intersects(buffer.geometry)]
                intersecting_points2 = cruise.data[(cruise.data.sog == 0) | (cruise.data.nav_status == 'Moored')]
                intersecting_indices = intersecting_points1.index.intersection(intersecting_points2.index)

                if len(intersecting_indices) > 0:
                    cruise.data.loc[intersecting_indices, 'port'] = buffer['name']
                    cruise.data.loc[intersecting_indices, 'status'] = 'inPort'
                    #print('populating column for', buffer['name'])
                    #print(f'There were {len(intersecting_points1)} points within the geofence and  {len(intersecting_points2)} moored or at rest, populating {len(intersecting_indices)} entries in the column')
                else:
                    pass
                    #print('no entries for', buffer['name'])
            else:
                intersecting_points = cruise.data[cruise.data.geometry.intersects(buffer.geometry)]
                intersecting_indices = intersecting_points.index()
                if len(intersecting_indices) > 0:
                    cruise.data.loc[intersecting_indices, 'port'] = buffer['name']
                    cruise.data.loc[intersecting_indices, 'status'] = 'inPort'
                    #print('populating column for', buffer['name'])
                    #print(f'There were {len(intersecting_points1)} points within the geofence and  {len(intersecting_points2)} moored or at rest, populating {len(intersecting_indices)} entries in the column')
                else:
                    pass
                    #print('no entries for', buffer['name'])


        # Create a new column with backward filled values
        cruise.data['filled_port'] = cruise.data['port'].fillna(method='bfill')
        # Update NaN values in the original 'port' column to be 'to' + the filled value
        cruise.data['next_port'] = cruise.data.apply(lambda row: f"to{row['filled_port']}" if pd.isna(row['port']) else row['port'], axis=1)

    @staticmethod
    def visitsGlacierBay(cruise) -> bool:
        """returns true if the cruise enters the park boundary of GLBA. else false
        """
        return any(cruise.data.intersects(PortManager.GLBA_BOUNDARY.unary_union))
    
    @staticmethod
    def visitsGlacierBay2(segment_node) -> bool:
        """returns true if the cruise enters the park boundary of GLBA. else false
        """
        return any(segment_node.intersects(PortManager.GLBA_BOUNDARY.unary_union))
    
    @staticmethod
    def visitsPort(cruise, portName) -> bool:
        """returns true if the cruise enters the geofence of the portName
        """
        search_area = PortManager.DOCK_BUFFERS
        search_area = search_area[search_area['name']==portName]
        search_area = search_area.to_crs(4326)

        return any(cruise.data.intersects(search_area.unary_union))
    
    @staticmethod # check functionality
    def getNextPort(data, current_index):
        """Get the next port after the given index in the cruise data."""
        for i in range(current_index + 1, len(data)):
            if data.loc[i, 'port'] is not None:
                return data.loc[i, 'port'], i
        return 'Error'

    @staticmethod # check functionality
    def getPreviousPort(data, current_index):
        """Get the previous port before the given index in the itinerary."""
        for i in range(current_index - 1, -1, -1):
            if data.loc[i, 'port'] is not None:
                return data.loc[i, 'port'], i
        return 'Error'

    @staticmethod
    def getFirstIndexInNextPort(data, current_index):
        port_changes = data['port'].ne(data['port'].shift())
        return port_changes.index[port_changes].shift(-1).iloc[current_index]
    
    @staticmethod
    def getLastIndexInPrevPort(data, current_index):
        port_changes = data['port'].ne(data['port'].shift())
        return port_changes.index[port_changes].shift().iloc[current_index]



############ SCRATCH AREA ################

    def getFirstIndexInPort(self, portName):
        """Returns the index of the first occurrence of being in a port."""
        filtered_gdf = self.geoprocessor.gdf[self.geoprocessor.gdf.port == portName]
        if filtered_gdf.empty:
            raise ValueError(f"Port {portName} not found in the GeoDataFrame.")
        return filtered_gdf.index[0]

    def getLastIndexInPort(self, portName):
        """Returns the index of the last occurrence of being in a port."""
        filtered_gdf = self.geoprocessor.gdf[self.geoprocessor.gdf.port == portName]
        if filtered_gdf.empty:
            raise ValueError(f"Port {portName} not found in the GeoDataFrame.")
        return filtered_gdf.index[-1]

    def getNextPort(self, current_index):
        """Get the next port after the given index in the itinerary."""
        for i in range(current_index + 1, len(self.geoprocessor.gdf)):
            if self.geoprocessor.gdf.loc[i, 'port'] is not None:
                return self.geoprocessor.gdf.loc[i, 'port'], i
        return 'Error'

    def getPreviousPort(self, current_index):
        """Get the previous port before the given index in the itinerary."""
        for i in range(current_index - 1, -1, -1):
            if self.geoprocessor.gdf.loc[i, 'port'] is not None:
                return self.geoprocessor.gdf.loc[i, 'port'], i
        return 'Error'

    def fillPointsWithinGlacierBay(self):
        """Populates new inGLBA column as True or false depending on intersection with the GLBA boundary polygon. 
           Will be used to determine exit time from GLBA
        """
        search_area = PortManager.GLBA_BOUNDARY
        search_area = search_area.to_crs(4326)
        self.geoprocessor.gdf['inGLBA'] = None #initialize column and set default to None type
        
        intersecting_points = self.geoprocessor.gdf[self.geoprocessor.gdf.geometry.intersects(search_area.geometry.unary_union)]
        intersecting_indices = intersecting_points.index
        if not intersecting_indices.empty:
            self.geoprocessor.gdf.loc[intersecting_indices, 'inGLBA'] = True

            last_true_index = intersecting_indices[-1]
            next_index = self.geoprocessor.gdf.index[self.geoprocessor.gdf.index > last_true_index][0] if last_true_index < self.geoprocessor.gdf.index[-1] else None

            #print(f"Last True Index: {last_true_index}, Next Index: {next_index}")
        else:
            print("No intersecting points found.")

        return next_index
     
    ##### GLACIER BAY ANALYSIS #####

    def getLastTimestampInGlacierBay(self):
        if self.visitsGlacierBay():
            first_index_outside_GLBA = self.fillPointsWithinGlacierBay()
            last_timestamp = self.geoprocessor.gdf.bs_ts.iloc[first_index_outside_GLBA - 1] # get timestamp of last point in GLBA
            if last_timestamp is not None:
                return last_timestamp
        else:
            return 'error in getLastTimestampInGLBA'

    def getPortAfterGlacierBay(self):
        if self.visitsGlacierBay():
            first_index_outside_GLBA = self.fillPointsWithinGlacierBay()
            next_port = self.getNextPort(first_index_outside_GLBA)
            if next_port is not None:
                return next_port
