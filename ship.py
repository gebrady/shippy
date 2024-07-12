import pandas as pd
import os
import secrets
import time
import matplotlib.pyplot as plt
from datetime import datetime

import geopandas as gpd
from geopy.distance import distance
from shapely.geometry import Point, LineString

from shapely.ops import nearest_points

# Custom class representing AIS functionality
class AIS():

    def __repr__(self):
        return 'AIS: Testing worked'

class BoatsData:

    def __init__(self):
        self.boatsDataDictionary = {}  # Dictionary to store BoatData instances
        self.previousBoatName = ""
        self.nanData = []  # To store rows with NaN values

    def __str__(self):
        string = ""
        for key, value in self.boatsDataDictionary.items():
            string = string + str(key) + ": " + str(value) + '\n'
        return string
    
    def parseRows(self, rows):
        """Reads tabular data as rows, sorting them into NaN, and other BoatData Objects.
           The rows are assigned to particular Cruise objects within that Class and stored as such.
        """
        boat_data = None
        grouped = rows.groupby('name', dropna = False)
        
        for boatName, group in grouped:
            group = group.sort_values(by='bs_ts', ascending=True)
            if pd.isna(boatName):
                self.nanData.extend(group.values.tolist())
                continue
            
            if boatName not in self.boatsDataDictionary or not boatName:
                self.boatsDataDictionary[boatName] = BoatData(boatName)
            
            self.boatsDataDictionary[boatName].processGroup(group)

class BoatData(AIS):
    TIME_THRESHOLD = pd.Timedelta(days=1) #if entry appears on next day, belongs to same cruise
    GLBA_BOUNDARY = gpd.read_file(r'./shapes/nps_boundary_glba.shp')

    def __init__(self, boatName):
        super().__init__()
        self.cruisesDataDictionary = {}  # Dictionary to store Cruise instances
        self.boatName = boatName  # Store boat name    
        self.previousBoatName = ''
        self.cruiseID = '' ####
        self.previousCruiseID = ''

    def __str__(self):
        string = ''
        for key, value in self.cruisesDataDictionary.items():
            string = string + str(key) + ": " + str(value) + '\n'
        return string
    
    def processGroup(self, group):
        #print('processing group', group['name'].head)
        group = self.orderGroupByTime(group)
        #print(group['bs_ts'].head)
        #print(f'this group: {group.name[0]}, last boat: {self.previousBoatName} ')
        # first few lines
        if self.groupMatchesLastCruise(group):
            self.cruisesDataDictionary[self.previousCruiseID].addGroup(group)
        elif self.newBoatEncountered(group):
            self.sortAndAddGroup(group)
        else:
            print(f'new cruise found for {self.boatName}')
            self.incrementCruisesDataDictionary(group)
            self.cruisesDataDictionary[self.cruiseID].addGroup(group)
        
        self.previousCruiseID = self.cruiseID
        self.previousBoatName = self.boatName

    ####### HELPER FUNCTIONS #######

    def orderGroupByTime(self, group):
        """Orders the input group chronologically (timestamps) and returns the group 
           in the new order with an object desribing the date for those data.
        """
        group['bs_ts'] = pd.to_datetime(group['bs_ts'])
        group.sort_values(by='bs_ts', inplace=True)
        return group.reset_index(drop=True)

    def initializeCruisesDataDictionary(self):
        """Assigns first cruiseID using boat name, creates an empty cruisesDataDictionary.
        """
        self.cruiseID = self.boatName + '_01'
        self.cruisesDataDictionary[self.cruiseID] = Cruise(self.cruiseID)
 
    def incrementCruisesDataDictionary(self, group):
        """creates a new entry in cruisesDataDictionary with an incremented cruiseID, updates instance variables.
        """
        self.cruiseID = self.boatName + f'_{len(self.cruisesDataDictionary) + 1:02d}'
        self.cruisesDataDictionary[self.cruiseID] = Cruise(self.cruiseID)
   
    def inPreviousCruiseRange(self, group_date):
        """checks if date of current group meets threshold to belong to previous edited cruise.
        """
        (group_date - BoatData.TIME_THRESHOLD) in self.cruisesDataDictionary[self.previousCruiseID].days
    
    def groupMatchesLastCruise(self, group):
        """Returns true if current group data belongs to the last processed group. False otherwise.
        """
        group_date = group['bs_ts'][0].date()
        return self.boatName == self.previousBoatName and (group_date - BoatData.TIME_THRESHOLD) in self.cruisesDataDictionary[self.previousCruiseID].days

    def newBoatEncountered(self, group):
        """Checks if new boat name from previous group, initializes cruisesDataDictionary at
           new cruiseID if None, and returns False for error
        """
        if self.boatName != self.previousBoatName:
            if not self.cruisesDataDictionary: #if empty
                #print('No Cruise Object, making instance for:', self.boatName)
                self.initializeCruisesDataDictionary()
            return True
        else: return False

    def sortAndAddGroup(self, group):
        """Adds data to the initial cruise if this is a new entry
           sorts the data to a cruise using timestamps, adds after identifying
           increments into a new cruise for an existing boats and adds.
        """
        group_date = group['bs_ts'][0].date()
        if len(self.cruisesDataDictionary) == 1:
            self.cruisesDataDictionary[self.cruiseID].addGroup(group)
        elif len(self.cruisesDataDictionary) > 1:
            for cruiseID, cruiseData in self.cruisesDataDictionary.items():
                if any((cruiseData['bs_ts'].dt.date == group_date) or (cruiseData['bs_ts'].dt.date + BoatData.TIME_THRESHOLD == group_date)):
                    self.cruiseID = cruiseID
                    self.cruisesDataDictionary[self.cruiseID].addGroup(group)
                    #print(f'adding new entries to cruise: {self.cruiseID}')
                    break
                else: # new cruise found for this boat
                    print(f'new cruise found for {self.boatName}')
                    self.incrementCruisesDataDictionary(group)
                    self.cruisesDataDictionary[self.cruiseID].addGroup(group)
        else:
            print('error in sortAndAddGroup')

    def getOtherCruises(self, cruiseName):
        if cruiseName in self.cruisesDataDictionary:
            return self.cruisesDataDictionary[cruiseName].getOtherCruises()
        else:
            return []

    def getCruise(self, cruiseName):
        if cruiseName in self.cruisesDataDictionary:
            return self.cruisesDataDictionary[cruiseName]
        else:
            return None

class Cruise(AIS):
    CRUISE_DOCKS_OG = {'Skagway' : (59.44932, -135.323998),
                    'Juneau' : (58.29350, -134.40080)}

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
        'Yakutat Bay': {'name': 'Yakutat Bay Cruise Area', 'coordinates': (-139.7274, 59.5475)},
        'Dutch Harbor': {'name': 'Dutch Harbor Cruise Ship Dock', 'coordinates': (-166.5429, 53.8898)},
        'Hoonah': {'name': 'Hoonah Cruise Ship Dock', 'coordinates': (-135.4436, 58.1139)},
        'Homer': {'name': 'Homer Cruise Ship Dock', 'coordinates': (-151.5483, 59.6425)},
        'Kenai': {'name': 'Kenai Cruise Ship Dock', 'coordinates': (-151.2583, 60.5544)},
        'Glacier Bay': {'name': 'Glacier Bay Cruise Area', 'coordinates': (-136.9002, 58.6658)},
        'College Fjord': {'name': 'College Fjord Cruise Area', 'coordinates': (-147.8333, 61.2106)},
        'Cordova': {'name': 'Cordova Cruise Ship Dock', 'coordinates': (-145.7575, 60.5428)},
        'Nome': {'name': 'Nome Cruise Ship Dock', 'coordinates': (-165.4064, 64.5011)},
        'Unalaska': {'name': 'Unalaska Cruise Ship Dock', 'coordinates': (-166.5319, 53.8697)},
        'Saint Paul Island': {'name': 'Saint Paul Island Cruise Dock', 'coordinates': (-170.2767, 57.1253)},
        'Barrow': {'name': 'Barrow Cruise Ship Dock', 'coordinates': (-156.7886, 71.2906)},
        'Klawock': {'name': 'Klawock Cruise Ship Dock', 'coordinates': (-133.0958, 55.5525)},
        'Thorne Bay': {'name': 'Thorne Bay Cruise Dock', 'coordinates': (-132.5222, 55.6886)},
        'Elfin Cove': {'name': 'Elfin Cove Cruise Dock', 'coordinates': (-136.3436, 58.1942)}
    }

    DOCK_BUFFERS = gpd.read_file(r'./buffers/docks_albers_2000m_buffer.shp')

    def __init__(self, cruiseID):
        super().__init__()
        self.data = pd.DataFrame(columns=['lat', 'lon', 'time'])
        self.cruiseID = cruiseID
        self.days = []
        self.time_records = []
        self.gdf = None # initialize empty geodataframe
        self.thinned = None
        self.portsOfCall = None
        self.timestamps_of_interest = None
        self.gdf_clipped = None
        self.daily_itinerary = None
    
    def __str__(self):
        return self.data.to_string()
    
    def addGroup(self, group):
        """Adds a full group pd DataFrame object to the Cruise instance 
           on which the method is called
        """
        self.data = pd.concat([self.data, group], ignore_index=True)
        self.days.append(group['bs_ts'][0].date())
    
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
        
    def toPointShapefile(self, filepath):
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

    def thinCruiseData(self):
        if not self.thinned:
            self.thinned = self.data.iloc[::100]
        
        #Thins the data to every 

    def dataToGeodata(self):
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

    ##### BOOLEAN METHODS #####

    def visitsGlacierBay(self):
        """returns true if the cruise enters the park boundary of GLBA. else false
        """
        self.dataToGeodata() # populates self.gdf if needed
        if any(self.gdf.intersects(BoatData.GLBA_BOUNDARY.unary_union)):
            return True
        else:
            return False



    ##### PORT OF CALL ANALYSIS #####

    def listPorts(self):
        """returns a list of the ports of call visited by the cruise during its itinerary
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
                    #self.portsOfCall.append(dock_name)
                    
                    # Retrieve the timestamps of the intersecting points
                    timestamps = self.gdf.loc[intersecting_indices, 'bs_ts'].tolist()
                    #print(timestamps)
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

    ##### VISUALIZATION FUNCITONS #####

    def plotCruise(self):
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
    
#port of call of glacier bay and then next port
#we know when they were in glba due to glba concessions people
# test run our code, output to excel which boats were in glba on which days
# run tests, make sure its accurate, apply it to db 

    ##### ITINERARY FUNCTIONS #####
    def populatePortsColumn(self):
        """Adds a column that specifies the location as either within a port or at sea
           port location is determined by containmenet of an AIS point within a 2km circular buffer around ports of interest.
        """
        if self.portsOfCall is not None:
            search_area = Cruise.DOCK_BUFFERS
            search_area = search_area.to_crs(4326)
            self.gdf['port'] = 'at sea'
            for _, buffer in search_area.iterrows():
                # Check if any point intersects with this buffer
                intersecting_indices = self.gdf[self.gdf.geometry.intersects(buffer.geometry)].index
                if len(intersecting_indices) > 0:
                    self.gdf.loc[intersecting_indices, 'port'] = buffer['name']
                    #print('populating column for', buffer['name'])
                else:
                    pass

        else:
            self.listPorts()
            self.populatePortsColumn()



    # Define the start and end dates
    def getItinerary(self):
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

        

###if it enteres the geofence of the port, assign it as a port. 


#make a plot of the ships activities over its cruise, with speed and time to visualize ports

    def getPortsOfCall(self):
        """Retrieves the ports of call for the cruise instance in order of appearance and sets it to an object variable.
        """
        if not self.portsOfCall:
            # Initialize an empty list and a variable to track the last seen value
            orderedUniquePorts = []
            previousPort = None

            # Iterate through the column and append unique values when a change occurs
            for port in self.data['destination']:
                if port != previousPort:
                    orderedUniquePorts.append(port)
                    previousPort = port

            self.portsOfCall = orderedUniquePorts
            #return self.portsOfCall
        else:
            print('error in get ports of call')

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
        
    ####### HELPER FUNCTIONS #######

    def getOtherCruises(self):
        if self.boatData is None:
            return []
        elif self.boatData.boatName in self.boatData.cruisesDataDictionary:
            return [cruise for cruise in self.boatData.cruisesDataDictionary.values() if cruise.cruiseName != self.cruiseName]
        else:
            return []

    def format_timestamp(timestamp_str):
        """Convert a timestamp string to a formatted string with month, day, and 24-hour time."""
        # Parse the timestamp string into a datetime object
        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
        
        # Format the datetime object to 'Month Day, HH:MM' format
        formatted_str = timestamp.strftime('%b %d, %H:%M')
        
        return formatted_str


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