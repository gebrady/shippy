import pandas as pd
import geopandas as gpd


class PortManager():
    GLBA_BOUNDARY = gpd.read_file(r'./shapes/port_GLBA.shp')
    GLBA_BOUNDARY = GLBA_BOUNDARY.set_crs(epsg=4326)
    DOCK_BUFFERS = gpd.read_file(r'./buffers/docks_albers_2000m_buffer.shp')

    def __init__(self, geoprocessor):
        self.geoprocessor = geoprocessor

    def visitsGlacierBay(self):
        """returns true if the cruise enters the park boundary of GLBA. else false
        """
        if any(self.geoprocessor.gdf.intersects(PortManager.GLBA_BOUNDARY.unary_union)):
            return True
        else:
            return False
    
    def visitsPort(self, portName):
        """returns true if the cruise enters the geofence of the portName
        """
        search_area = PortManager.DOCK_BUFFERS
        search_area = search_area[search_area['name']==portName]
        search_area = search_area.to_crs(4326)
        if any(self.geoprocessor.gdf.intersects(search_area.unary_union)):
            return True
        else:
            return False
    
    def assignPorts(self):
        """Adds columns that specify the location as either within a port or in transit between ports.
        Port location is determined by containment of an AIS point within a 2km circular buffer around ports of interest.
        Adds columns: 'port', 'status' (either 'inPort' or 'inTransit'), and 'next_port' to the DataFrame.
        """
        search_area = PortManager.DOCK_BUFFERS
        search_area = search_area.to_crs(4326)
        self.geoprocessor.gdf['port'] = None
        self.geoprocessor.gdf.at[self.geoprocessor.gdf.index[0], 'port'] = 'StartOfCruise'
        self.geoprocessor.gdf.at[self.geoprocessor.gdf.index[-1], 'port'] = 'EndOfCruise' # default for now since we don't have many Seattle/CAN cruises
        self.geoprocessor.gdf['status'] = 'inTransit'  # Default to 'inTransit'
                
        self.geoprocessor.gdf.at[self.geoprocessor.gdf.index[0], 'status'] = 'inPort'
        self.geoprocessor.gdf.at[self.geoprocessor.gdf.index[-1], 'status'] = 'inPort'

        self.geoprocessor.gdf['next_port'] = None
        
        # Iterate over all ports in the search area
        for _, buffer in search_area.iterrows():
            # Check if any point intersects with this buffer
            intersecting_points1 = self.geoprocessor.gdf[self.geoprocessor.gdf.geometry.intersects(buffer.geometry)]
            intersecting_points2 = self.geoprocessor.gdf[(self.geoprocessor.gdf.sog == 0) | (self.geoprocessor.gdf.nav_status == 'Moored')]
            intersecting_indices = intersecting_points1.index.intersection(intersecting_points2.index)

            if len(intersecting_indices) > 0:
                self.geoprocessor.gdf.loc[intersecting_indices, 'port'] = buffer['name']
                self.geoprocessor.gdf.loc[intersecting_indices, 'status'] = 'inPort'
                #print('populating column for', buffer['name'])
                #print(f'There were {len(intersecting_points1)} points within the geofence and  {len(intersecting_points2)} moored or at rest, populating {len(intersecting_indices)} entries in the column')
            else:
                pass
                #print('no entries for', buffer['name'])

        # Create a new column with backward filled values
        self.geoprocessor.gdf['filled_port'] = self.geoprocessor.gdf['port'].fillna(method='bfill')
        # Update NaN values in the original 'port' column to be 'to' + the filled value
        self.geoprocessor.gdf['next_port'] = self.geoprocessor.gdf.apply(lambda row: f"to{row['filled_port']}" if pd.isna(row['port']) else row['port'], axis=1)

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
