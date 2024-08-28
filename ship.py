import pandas as pd
from CruiseSorter import *
import os
import secrets
import time
import matplotlib.pyplot as plt
from datetime import datetime
from pathcalculations import *
import pytz

# Custom class representing AIS functionality
class AIS():

    def __repr__(self):
        return 'AIS: Testing worked'

class Cruise(AIS):

    CRUISE_DOCKS = {
        'Juneau': {'name': 'Juneau Cruise Ship Terminal', 'coordinates': (-134.4197, 58.3019)},
        'Ketchikan': {'name': 'Ketchikan Cruise Ship Dock', 'coordinates': (-131.6461, 55.3422)},
        'Skagway': {'name': 'Skagway Cruise Ship Dock', 'coordinates': (-135.3300, 59.4500)},
        'Seward': {'name': 'Seward Cruise Ship Terminal', 'coordinates': (-149.4330, 60.1244)},
        'Sitka': {'name': 'Sitka Sound Cruise Terminal', 'coordinates': (-135.3381, 57.0516)},
        'Haines': {'name': 'Haines Cruise Ship Dock', 'coordinates': (-135.4456, 59.2358)},
        'Whittier': {'name': 'Whittier Cruise Ship Terminal', 'coordinates': (-148.6836, 60.7722)},
        'Anchorage': {'name': 'Port of Anchorage', 'coordinates': (-149.9003, 61.2181)},
        'Icy Strait Point': {'name': 'Icy Strait Point Cruise Dock', 'coordinates': (-135.4460, 58.1378)},
        'Valdez': {'name': 'Valdez Cruise Ship Terminal', 'coordinates': (-146.3483, 61.1246)},
        'Kodiak': {'name': 'Kodiak Cruise Ship Dock', 'coordinates': (-152.4072, 57.7900)},
        'Petersburg': {'name': 'Petersburg Cruise Dock', 'coordinates': (-132.9556, 56.8125)},
        'Wrangell': {'name': 'Wrangell Cruise Dock', 'coordinates': (-132.3801, 56.4708)},
        'Hubbard Glacier': {'name': 'Hubbard Glacier Cruise Area', 'coordinates': (-139.4938, 60.0200)},
        'Prince Rupert': {'name': 'Prince Rupert Cruise Terminal', 'coordinates': (-130.3200, 54.3150)},
        'Seattle': {'name': 'Seattle Cruise Ship Terminal', 'coordinates': (-122.3331, 47.6097)},
        'Victoria': {'name': 'Victoria Cruise Ship Terminal', 'coordinates': (-123.3656, 48.4284)},
        'Bellingham': {'name': 'Bellingham Cruise Ship Terminal', 'coordinates': (-122.4784, 48.7519)},
        'Port Angeles': {'name': 'Port Angeles Cruise Ship Terminal', 'coordinates': (-123.4308, 48.1184)},
        'San Francisco': {'name': 'San Francisco Cruise Ship Terminal', 'coordinates': (-122.3960, 37.7946)},
        'Glacier Bay': {'name': 'Glacier Bay Cruise Area', 'coordinates': (-136.9002, 58.6658)},
        'College Fjord': {'name': 'College Fjord Cruise Area', 'coordinates': (-147.8333, 61.2106)},
        'Cordova': {'name': 'Cordova Cruise Ship Dock', 'coordinates': (-145.7575, 60.5428)},
    }

    DOCK_BUFFERS = gpd.read_file(r'./buffers/docks_albers_2000m_buffer.shp')

    ##### CONSTRUCTORS AND REPRESENTATION #####
    
    def __init__(self, cruiseID):
        super().__init__()
        self.data = pd.DataFrame(columns=['lat', 'lon', 'time'])
        self.cruiseID = cruiseID
        self.boatName = None
        self.days = []
        self.time_records = []
        self.gdf = None # geodataframe version of cruiseData
        self.thinned = None # duplicate of cruiseData, with a low resolution the result of thinning
        self.portsOfCall = None # List of ports visited and on which days
        self.timestamps_of_interest = None # timestamps of points logged within dock bufffers
        self.gdf_clipped = None # 
        self.portAfterGLBA = None
        self.daily_itinerary = None # Dictionary or List of ports visited or itinerary IDs (enteres GLBA, AtSea, etc.)
        self.sub = None

    def __str__(self):
        return self.data.to_string()

    ##### MAIN IMPORT FUNCTIONALITIES #####
    
    def addGroup(self, group):
        """Adds a full group pd DataFrame object to the Cruise instance 
           on which the method is called
        """
        self.data = pd.concat([self.data, group], ignore_index=True)
        self.days.append(group['bs_ts'][0].date())
    
    def addCruiseToShapfile(self, shapefile):
        """adds a cruise's geodataframe to a feature in an ESRI shapefile. This generally would come after the cropping and conversion from point to line data
        """
        self.dataToGeodata()
        self.assignPorts()
        port = self.getPortAfterGlacierBay()

    ##### GEOSPATIAL METHODS #####

    import geopandas as gpd
    from geopy.distance import distance
    from shapely.geometry import Point, LineString
    from geopy.distance import geodesic

    from shapely.ops import nearest_points

    def dataToGeodata(self): # Convert self.data to a geodataframe
        """Converts a populated self.data to a geodataframe and stores it as self.gdf
        """
        if self.gdf is None:
            geometry = [Point(xy) for xy in zip(self.data['lon'], self.data['lat'])]
            #points_gdf = gpd.GeoDataFrame(data, geometry=gpd.points_from_xy(data['longitude'], data['latitude'])) 
            # ^^ another way to do it
            gdf = gpd.GeoDataFrame(self.data, geometry=geometry)
            gdf.set_crs(epsg=4326, inplace=True)
            self.gdf = gdf
        else:
            pass

    def clipBoundary(self, boundary):
        """writes shapefile of cruiseData, using the boundary polygon to subset the geodataframe
        """
        if not self.gdf_clipped:
            geometry = [Point(xy) for xy in zip(self.data['lon'], self.data['lat'])]
            # Convert DataFrame to GeoDataFrame
            gdf = gpd.GeoDataFrame(self.data, geometry=geometry)
            # Set CRS to WGS 84 (EPSG:4326)
            gdf.set_crs(epsg=4326, inplace=True)
            # Subset the GeoDataFrame by the boundary
            gdf_sub = gdf[gdf.geometry.within(boundary.geometry.unary_union)]
            self.gdf_clipped = gdf_sub
        else:
            print('error in clipboundary')

    def toPointShapefile_og(self, filepath):
        """Converts a Cruise object to a shapefile and writes it to filepath.
           filepath takes .shp extension
        """
        # Create geometry column from latitude and longitude columns
        geometry = [Point(xy) for xy in zip(self.data['lon'], self.data['lat'])]
        # Convert DataFrame to GeoDataFrame
        #print(cruiseData.data)
        gdf = gpd.GeoDataFrame(self.data, geometry=geometry)
        #print(gdf)
        # Set CRS to WGS 84 (EPSG:4326)
        gdf.set_crs(epsg=4326, inplace=True)
        gdf.to_file(os.path.join(os.getcwd(), filepath))
        self.gdf = gdf
    
    def toLineShapefile(self, filepath, start_index, end_index):
        print(self.gdf)
        if start_index and end_index:
            line = LineString(self.gdf.loc[start_index:end_index].geometry.values)
            distance = PathCalculations.distanceAlongPath(self.gdf.geometry, start_index, end_index)[1]
            time = PathCalculations.timelapseAlongPath(self.gdf.bs_ts ,start_index, end_index)

        else: 
            line = LineString(self.gdf.geometry.values)
            distance = PathCalculations.distanceAlongPath(self.gdf.geometry, self.gdf.index[0], self.gdf.index[-1])[1]
            time = PathCalculations.timelapseAlongPath(self.gdf.bs_ts, self.gdf.index[0], self.gdf.index[-1])

        new_row = {
            'cruiseID': self.cruiseID,
            'boatName': self.boatName,
            'startDate': str(min(self.days)),
            'endDate': str(max(self.days)),
            'departGLBA': str(self.getLastTimestampInGlacierBay()),
            'afterGLBA': self.getPortAfterGlacierBay(),
            'distance' : distance,
            'time' : time
        }
        # Create a new GeoDataFrame with the new row
        line_gdf = gpd.GeoDataFrame([new_row], geometry=[line], crs=self.gdf.crs)
        line_gdf.set_crs(epsg=4326, inplace=True)
        line_gdf.to_file(os.path.join(os.getcwd(), filepath), driver='ESRI Shapefile')

    def appendToLineShapefile(self, filepath, start_index, end_index):
        """adds the self.gdf entries to the shapefile at filepath. if the file doesn't exist, then creates one.
        """
        full_path = os.path.join(os.getcwd(),filepath)
        if not os.path.exists(full_path):
            if start_index and end_index:
                self.toLineShapefile(filepath, start_index, end_index)
            else:
                self.toLineShapefile(filepath)

        else:
            existing_gdf = gpd.read_file(full_path)
            existing_df = existing_gdf.reset_index(drop=True)
            if self.cruiseID in existing_df.cruiseID.values:
                pass
            print(f"appending to shapefile: {self.cruiseID}")
            ###SUBSET IN GLBA
            ###

            if start_index and end_index:
                line = LineString(self.gdf.loc[start_index:end_index].geometry.values)
                distance = PathCalculations.distanceAlongPath(self.gdf.geometry, start_index, end_index)[1]
                time = PathCalculations.timelapseAlongPath(self.gdf.bs_ts, start_index, end_index)

            else: 
                line = LineString(self.gdf.geometry.values)
                distance = PathCalculations.distanceAlongPath(self.gdf.geometry, self.gdf.index[0], self.gdf.index[-1])[1]
                time = PathCalculations.timelapseAlongPath(self.gdf.bs_ts, self.gdf.index[0], self.gdf.index[-1])


            new_row = {
                'cruiseID': self.cruiseID,
                'boatName': self.boatName,
                'startDate': str(min(self.days)),
                'endDate': str(max(self.days)),
                'departGLBA': str(self.getLastTimestampInGlacierBay()),
                'afterGLBA': self.getPortAfterGlacierBay(),
                'distance' : distance,
                'time' : time
            }
        
            # Create a new GeoDataFrame with the new row
            new_line_gdf = gpd.GeoDataFrame([new_row], geometry=[line], crs=self.gdf.crs)
            new_line_gdf.set_crs(epsg=4326, inplace=True)

                # Convert date columns to datetime format
            new_line_gdf['startDate'] = pd.to_datetime(new_line_gdf['startDate'])
            new_line_gdf['endDate'] = pd.to_datetime(new_line_gdf['endDate'])
            new_line_gdf['departGLBA'] = pd.to_datetime(new_line_gdf['departGLBA'])

            # Specify other column types explicitly
            new_line_gdf = new_line_gdf.astype({
                'cruiseID': 'str',
                'boatName': 'str',
                'afterGLBA': 'str'
            })
      
            
            new_df = new_line_gdf.reset_index(drop=True)
            
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
            
            updated_gdf = gpd.GeoDataFrame(combined_df, geometry='geometry', crs=self.gdf.crs)
            
            # Write the updated GeoDataFrame back to the shapefile
            updated_gdf.to_file(full_path, driver='ESRI Shapefile')
            # Append all new rows to the result DataFrame at once

    def fillPointsWithinGlacierBay(self):
        """Populates new inGLBA column as True or false depending on intersection with the GLBA boundary polygon. 
           Will be used to determine exit time from GLBA
        """
        search_area = BoatData.GLBA_BOUNDARY
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
     
    def toPointShapefile(self, filepath):
        # Create geometries from lon and lat
        geometry = [Point(xy) for xy in zip(self.data['lon'], self.data['lat'])]
        gdf = gpd.GeoDataFrame(self.data, geometry=geometry)
        gdf.set_crs(epsg=4326, inplace=True)
        
        # Add additional information
        gdf['cruiseID'] = self.cruiseID
        gdf['boatName'] = self.boatName
        gdf['startDate'] = str(min(self.days))
        gdf['endDate'] = str(max(self.days))
        gdf['departGLBA'] = str(self.getLastTimestampInGlacierBay())
        gdf['afterGLBA'] = self.getPortAfterGlacierBay()

        gdf.to_file(os.path.join(os.getcwd(), filepath), driver='ESRI Shapefile')
        self.gdf = gdf

    def appendToPointShapefile(self, filepath):
        """Adds the self.gdf entries to the shapefile at filepath. If the file doesn't exist, then creates one."""
        full_path = os.path.join(os.getcwd(), filepath)
        
        # Create geometries from lon and lat
        geometry = [Point(xy) for xy in zip(self.data['lon'], self.data['lat'])]
        gdf = gpd.GeoDataFrame(self.data[['bs_ts', 'name', 'sog', 'cog']], geometry=geometry)
        gdf.set_crs(epsg=4326, inplace=True)
        
        # Add additional information
        gdf['cruiseID'] = self.cruiseID
        gdf['boatName'] = self.boatName
        gdf['startDate'] = str(min(self.days))
        gdf['endDate'] = str(max(self.days))
        gdf['departGLBA'] = str(self.getLastTimestampInGlacierBay())
        gdf['afterGLBA'] = self.getPortAfterGlacierBay()

        if not os.path.exists(full_path):
            gdf.to_file(full_path, driver='ESRI Shapefile')
        else:
            existing_gdf = gpd.read_file(full_path)
            
            # Convert date columns to datetime format
            existing_gdf['startDate'] = pd.to_datetime(existing_gdf['startDate'])
            existing_gdf['endDate'] = pd.to_datetime(existing_gdf['endDate'])
            existing_gdf['departGLBA'] = pd.to_datetime(existing_gdf['departGLBA'])
            
            # Append the new GeoDataFrame to the existing one
            combined_gdf = pd.concat([existing_gdf, gdf], ignore_index=True)
            
            # Write the combined GeoDataFrame back to the shapefile
            combined_gdf.to_file(full_path, driver='ESRI Shapefile')
    
    ##### BOOLEAN METHODS #####

    def visitsGlacierBay(self):
        """returns true if the cruise enters the park boundary of GLBA. else false
        """
        self.dataToGeodata() # populates self.gdf if needed
        if any(self.gdf.intersects(BoatData.GLBA_BOUNDARY.unary_union)):
            return True
        else:
            return False
    
    def visitsPort(self, portName):
        """returns true if the cruise enters the geofence of the portName
        """
        self.dataToGeodata()
        search_area = Cruise.DOCK_BUFFERS
        search_area = search_area[search_area['name']==portName]
        search_area = search_area.to_crs(4326)
        if any(self.gdf.intersects(search_area.unary_union)):
            return True
        else:
            return False
    
    ##### DATA MANAGEMENT METHODS #####

    def thinCruiseData(self, n): # Resample data to every n entries
        if not self.thinned:
            self.thinned = self.data.iloc[::n]
        
        #Thins the data to every 
    
    def assignBoatName(self):
        if self.boatName is None:
            self.boatName = self.gdf.name[0]
        else:
            print('error in assignboatname()')
    
    ##### PORT OF CALL & ITINERARY ANALYSIS #####

    def assignPorts(self):
        """Adds columns that specify the location as either within a port or in transit between ports.
        Port location is determined by containment of an AIS point within a 2km circular buffer around ports of interest.
        Adds columns: 'port', 'status' (either 'inPort' or 'inTransit'), and 'next_port' to the DataFrame.
        """
        search_area = Cruise.DOCK_BUFFERS
        search_area = search_area.to_crs(4326)
        self.gdf['port'] = None
        self.gdf.at[self.gdf.index[0], 'port'] = 'StartOfCruise'
        self.gdf.at[self.gdf.index[-1], 'port'] = 'EndOfCruise' # default for now since we don't have many Seattle/CAN cruises
        self.gdf['status'] = 'inTransit'  # Default to 'inTransit'
                
        self.gdf.at[self.gdf.index[0], 'status'] = 'inPort'
        self.gdf.at[self.gdf.index[-1], 'status'] = 'inPort'

        self.gdf['next_port'] = None
        
        # Iterate over all ports in the search area
        for _, buffer in search_area.iterrows():
            # Check if any point intersects with this buffer
            intersecting_points1 = self.gdf[self.gdf.geometry.intersects(buffer.geometry)]
            intersecting_points2 = self.gdf[(self.gdf.sog == 0) | (self.gdf.nav_status == 'Moored')]
            intersecting_indices = intersecting_points1.index.intersection(intersecting_points2.index)

            if len(intersecting_indices) > 0:
                self.gdf.loc[intersecting_indices, 'port'] = buffer['name']
                self.gdf.loc[intersecting_indices, 'status'] = 'inPort'
                #print('populating column for', buffer['name'])
                #print(f'There were {len(intersecting_points1)} points within the geofence and  {len(intersecting_points2)} moored or at rest, populating {len(intersecting_indices)} entries in the column')
            else:
                pass
                #print('no entries for', buffer['name'])

        # Create a new column with backward filled values
        self.gdf['filled_port'] = self.gdf['port'].fillna(method='bfill')
        # Update NaN values in the original 'port' column to be 'to' + the filled value
        self.gdf['next_port'] = self.gdf.apply(lambda row: f"to{row['filled_port']}" if pd.isna(row['port']) else row['port'], axis=1)

    def initializeItinerary(self):
        """Initializes the itinerary dictionary for the cruise, storing port information and directionality.
        """
        self.itinerary = []
        current_port = None
        previous_port = None

        for idx, row in self.gdf.iterrows():
            if row['status'] == 'inPort':
                current_port = row['port']
                if current_port is not None:
                    if current_port != previous_port:
                        # Append the previous port's details and the next port
                        self.itinerary.append({
                            'from_port': current_port,
                            'timestamp': row['bs_ts']
                        })
                        previous_port = current_port
                    else:
                        continue
                else:
                    print('error in initialize Itinerary')

        # Print the itinerary for debugging
        for leg in self.itinerary:
            print(f"In {leg['from_port']}, entered port at {leg['timestamp']}")

    ##### TRANSIT ANALYTICS #####

    def getPointsInPort(self, portName):
        """returns the subset of points moored in portName
        """
        return self.gdf[self.gdf.port == portName]

    def getLastTimestampInPort(self, portName):
        """Returns timestamp value for the last point moored in portName
        """
        subset = self.getPointsInPort(portName)
        return subset.bs_ts.iloc[-1], subset.bs_ts.iloc[-1].index

    def getTransitToNextPort(self, portName): 
        """returns the data subset that includes the transit between port portName and the next logged port.
           Should currently not anticipate multiple visits to ports of the same name, should generally be used right now with Glacier Bay as the portname
        """
        lastPointInPort = max(self.gdf[self.gdf.port == portName].index)
        nextPort = self.gdf.filled_port.iloc[lastPointInPort + 1]
        lastPointInTransit = max(self.gdf[self.gdf.next_port == 'to' + nextPort].index)
        return self.gdf.iloc[lastPointInPort + 1 : lastPointInTransit - 1]

    def averageTransitSpeed(self, transitSub):
        _, distance_km = PathCalculations.distanceAlongPath(self.gdf.geometry, transitSub.index[0], transitSub.index[-1])
        time_elapsed_seconds = (transitSub.bs_ts.iloc[-1] - transitSub.bs_ts.iloc[0]).total_seconds()
        time_elapsed_hours = time_elapsed_seconds / 3600
        print(distance_km)
        print(time_elapsed_hours)
        return distance_km/time_elapsed_hours

    def getFirstIndexInPort(self, portName):
        """Returns the index of the first occurrence of being in a port."""
        filtered_gdf = self.gdf[self.gdf.port == portName]
        if filtered_gdf.empty:
            raise ValueError(f"Port {portName} not found in the GeoDataFrame.")
        return filtered_gdf.index[0]

    def getLastIndexInPort(self, portName):
        """Returns the index of the last occurrence of being in a port."""
        filtered_gdf = self.gdf[self.gdf.port == portName]
        if filtered_gdf.empty:
            raise ValueError(f"Port {portName} not found in the GeoDataFrame.")
        return filtered_gdf.index[-1]


    ##### GLACIER BAY ANALYSIS #####

    def getLastTimestampInGlacierBay(self):
        if self.visitsGlacierBay():
            first_index_outside_GLBA = self.fillPointsWithinGlacierBay()
            last_timestamp = self.gdf.bs_ts.iloc[first_index_outside_GLBA - 1] # get timestamp of last point in GLBA
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

    ##### ITINERARY FUNCTIONS #####

    def displayItinerary(self):
        """Returns a string of the days for the cruise and the locations visited
            ex. NORWEGIAN BLISS 
                7/1 Juneau
                7/2 Juneau -> Icy Strait
                7/3 Icy Strait --> At Sea
                7/4 At Sea
                7/5 Seward
                7/6 Seward --> At Sea
                7/7 At Sea --> GLBA --> Juneau
                7/8 Juneau
        """
        #date_range = pd.date_range(self.days[0], self.days[-1]) self.days is sorted already so useable in loop

        port = ''
        previous_port = ''

        df = pd.DataFrame(self.gdf)

        # Initialize the itinerary dictionary
        itinerary = {}
        ports_of_call = []

        # Iterate over the DataFrame and populate the itinerary
        for index, row in df.iterrows():
            date_key = (row['bs_ts'].year, row['bs_ts'].month, row['bs_ts'].day)
            port = row['port']
            if not ports_of_call and port != 'at sea':
                ports_of_call.append(port)
                pass
            if port == previous_port:
                continue
            if date_key not in itinerary:
                itinerary[date_key] = []
            if port not in itinerary[date_key] and port != previous_port:
                itinerary[date_key].append(port)
                if port != 'at sea' and ports_of_call[-1] != port:
                    ports_of_call.append(port)
                previous_port = port    

        # Display the itinerary
        for date_key, ports in itinerary.items():
            year, month, day = date_key
            print(f"{year}-{month:02d}-{day:02d}: {', '.join(ports)}")
        print()
        print(ports_of_call)

    def getPortsOfCall(self):
        """Retrieves the ports of call for the cruise instance in order of appearance and sets it to an object variable.
        """
        if not self.portsOfCall:
            # Initialize an empty list and a variable to track the last seen value
            orderedUniquePorts = []
            previousPort = None

            # Iterate through the column and append unique values when a change occurs
            for index, port in self.data['destination'].iterrows():
                if port != previousPort:
                    orderedUniquePorts.append(port)
                    previousPort = port

            self.portsOfCall = orderedUniquePorts
            #return self.portsOfCall
        else:
            print('error in get ports of call')

    def getNextPort(self, current_index):
        """Get the next port after the given index in the itinerary."""
        for i in range(current_index + 1, len(self.gdf)):
            if self.gdf.loc[i, 'port'] is not None:
                return self.gdf.loc[i, 'port'], i
        return 'Error'

    def getPreviousPort(self, current_index):
        """Get the previous port before the given index in the itinerary."""
        for i in range(current_index - 1, -1, -1):
            if self.gdf.loc[i, 'port'] is not None:
                return self.gdf.loc[i, 'port'], i
        return 'Error'

    def getNextPorts(self, timestamp):
        """Returns tuple of current and next destinations.
        """
        if timestamp > max(self.data['bs_ts']) or timestamp < min(self.data['bs_ts']):
            print('error in timestamp: out of range')
            pass
        else:
            timestamp = pd.Timestamp(timestamp)
            #start_index = self.data.index[self.data['bs_ts'] == timestamp][0]
            start_index = self.data['bs_ts'].get_loc(timestamp, method='nearest')
            
            portsOfCall = set()
            currentDestination = self.data.loc[start_index, 'destination']
            portsOfCall.add(currentDestination)

            for idx in range(start_index + 1, len(self.data)):
                value = df.loc[idx, 'data_column']
                if value not in portsOfCall:
                    portsOfCall.add(value)
                    # Do analysis on the unique value found
                    print(f"Unique value found: {value} at index {idx}")
                    break
                print('no other destination found')
                portsOfCall.add('Nan')

            return portsOfCall
        
    ##### VISUALIZATION FUNCITONS #####

    def plotCruiseVelocity(self):
        """Plots speed-time graph for the cruise object, could be paired with a map at some point.
        """
        if self.data is not None:
            plt.figure(figsize=(10, 6))
            plt.plot(self.data['bs_ts'], self.data['sog'], linestyle='-')
            plt.xlabel('Timestamp')
            plt.ylabel('Speed over ground')
            plt.title(f'Velocity Over Time: {self.cruiseID}')
            plt.grid(True)
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.show()
        else:
            print('error: no data in plotCruise()')
    
    def plotCruiseRoute(self):
        """uses matplotlib to plot the cruise route as a line
        """
        # Load the points into a GeoDataFrame
        points_gdf = self.gdf

        # Load the coastline shapefile into a GeoDataFrame
        coastline_gdf = BoatsData.ALASKA_COASTLINE_WGS84  # Adjust the path as needed

        # Ensure points_gdf is sorted by the order you want the points to be connected
        points_gdf = points_gdf.sort_values(by='bs_ts')  # Replace 'order_column' with your actual column

        # Convert the points to a LineString
        line = LineString(points_gdf.geometry.values)
        line_gdf = gpd.GeoDataFrame(geometry=[line], crs=points_gdf.crs)

        # Create a plot
        fig, ax = plt.subplots(figsize=(10, 10))

        # Plot the coastline
        coastline_gdf.plot(ax=ax, color='black', linewidth=0.5)

        # Plot the line
        line_gdf.plot(ax=ax, color='blue', linewidth=2)

        # Set the extent to the line
        ax.set_xlim([line.bounds[0], line.bounds[2]])
        ax.set_ylim([line.bounds[1], line.bounds[3]])

        # Add title and labels
        ax.set_title('Line Plot on Alaska Coastline')
        ax.set_xlabel('Longitude')
        ax.set_ylabel('Latitude')

        # Show the plot
        plt.show()

    ####### HELPER FUNCTIONS #######

    def getOtherCruises(self):
        if self.boatData is None:
            return []
        elif self.boatData.boatName in self.boatData.cruisesDataDictionary:
            return [cruise for cruise in self.boatData.cruisesDataDictionary.values() if cruise.cruiseName != self.cruiseName]
        else:
            return []

    def format_timestamp(timestamp_str): # DEPRECATED?
        """Convert a timestamp string to a formatted string with month, day, and 24-hour time."""
        # Parse the timestamp string into a datetime object
        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
        
        # Format the datetime object to 'Month Day, HH:MM' format
        formatted_str = timestamp.strftime('%b %d, %H:%M')
        
        return formatted_str

    ##### DEPRECATED ITINERARY METHODS #####

    def populatePortsColumn(self): # DEPRECATED
        """Adds a column that specifies the location as either within a port or at sea
           port location is determined by containmenet of an AIS point within a 2km circular buffer around ports of interest.
        """
        if self.portsOfCall is not None:
            search_area = Cruise.DOCK_BUFFERS
            search_area = search_area.to_crs(4326)
            self.gdf['port'] = None
            for _, buffer in search_area.iterrows():
                # Check if any point intersects with this buffer
                intersecting_indices = self.gdf[self.gdf.geometry.intersects(buffer.geometry)].index
                if len(intersecting_indices) > 0:
                    self.gdf.loc[intersecting_indices, 'port'] = buffer['name']
                    #print('populating column for', buffer['name'])
                else:
                    print('error in populatePortsColumn')

        else:
            self.listPorts()
            self.populatePortsColumn()

    def getItinerary(self): # DEPRECATED
        if self.portsOfCall is not None:
            start_date = min(self.days)
            end_date = max(self.days)

            # Create a date range from the start to end date
            date_range = pd.date_range(start=start_date, end=end_date)

            # Prepare a dictionary to hold the itinerary
            self.daily_itinerary = {}
            print(date_range)
            # Populate the itinerary
            for date in date_range:
                date_str = date.strftime('%m/%d')
                daily_ports = []
                for port, dates in self.portsOfCall.items():
                    formatted_dates = [d.strftime('%m/%d') for d in dates]
                    if date_str in formatted_dates:
                        daily_ports.append(port)

                #daily_ports = [port for port, dates[1] in self.portsOfCall.items() if date_str in [d.strftime('%m/%d') for d in dates]]
                daily_itinerary[date.strftime('%Y-%m-%d')] = daily_ports

            # Print the daily itinerary
            # for date, ports in daily_itinerary.items():
            #     print(f"{date}: {', '.join(ports) if ports else 'At Sea'}")
            return self.daily_itinerary
        else:
            self.listPorts()
            self.getItinerary()

    def listPorts(self): # DEPRECATED
        """returns a list of the ports of call visited by the cruise during its itinerary
           ASSIGNS self.portsOfCall as a dict where each key is the dock visited
           and the values are the timestamps of the points that visited that dock
        """
        if self.gdf is None:
            self.dataToGeodata()
        if self.portsOfCall is None:
            self.portsOfCall = {}
            self.timestamps_of_interest = []
            search_area = Cruise.DOCK_BUFFERS
            search_area = search_area.to_crs(4326)
            #print(search_area)
            #search_radius = .1125  # ~ 2 mile radius in degrees
            # Collect the names of features in the buffer layer that intersect with any of the buffers from the points layer
            for _, buffer in search_area.iterrows():
                buffer_geom = buffer['geometry']  # Buffer geometry
                # Check if any point intersects with this buffer
                intersecting_indices = self.gdf[self.gdf.geometry.intersects(buffer_geom)].index

                if len(intersecting_indices) > 0:
                    #print('match found for', buffer['name'])
                    dock_name = buffer['name']
                    #print(f'Match found for {dock_name}')
                    # Retrieve the timestamps of the intersecting points
                    timestamps = self.gdf.loc[intersecting_indices, 'bs_ts'].tolist()
                    timestamps_formatted = format_timestamp_range2(timestamps)
                    self.portsOfCall[dock_name] = (timestamps_formatted, timestamps)
                else:
                    pass
            s = ''
            for key, value in self.portsOfCall.items():
                s += f'{key}: {value[0]} \n'
            return s
        else:
            print('self.portsOfCall has been assigned error in listPorts')
            return None

################################################################

##### FORMATTING METHODS #####

def format_timestamp_range(timestamp_list):
    """Converts a list of timestamps to a string describing its range."""
    # Find the minimum and maximum timestamps
    lo = min(timestamp_list)
    hi = max(timestamp_list)
    
    # Format the datetime objects to 'MM/DD HHMM' format
    lo_str = lo.strftime('%-m/%-d %H:%M')
    hi_str = hi.strftime('%-m/%-d %H:%M')
    
    # Create the final formatted string
    formatted_str = f'{lo_str} - {hi_str}'
    
    return formatted_str

def format_timestamp_range2(timestamps):
    # Extract the dates from the timestamps
    dates = [ts.date() for ts in timestamps]
    # Get the unique dates
    unique_dates = list(set(dates))
    # Sort the unique dates
    unique_dates.sort()
    # Format the dates to month/day
    formatted_dates = [date.strftime('%m/%d') for date in unique_dates]
    return formatted_dates