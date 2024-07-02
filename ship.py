import pandas as pd
import os
import secrets
import time

# Custom class representing AIS functionality
class AIS():
    def __repr__(self):
        return 'AIS: Testing worked'

# Main application class
class App:
    def __init__(self, dataFolder):
        self.boatsData = BoatsData()  # Initialize BoatsData instance
        self.rowsParsedCount = 0
        #main function when App initialized
        self.populateBoatsData(dataFolder)  # Populate boatsData with data from CSV files

    def __str__(self):
        return str(self.boatsData)  # String representation of boatsData
    
    def populateBoatsData(self, dataFolder):
        tik = time.perf_counter()
        count=0
        for dirs, _, files in os.walk(dataFolder):
            for f in sorted(files):
                if f.endswith('csv'):
                    count+=1
                    file_path = os.path.join(dirs, f)
                    rows = pd.read_csv(file_path)  # Read CSV file into DataFrame
                    print(f'Starting parsing file: {f}')
                    self.boatsData.parseRows(rows)  # Parse rows into boatsData
                    self.rowsParsedCount += len(rows)
                    print(f'Finished parsing file: {f}')
                
        tok = time.perf_counter()
        print(f"Imported data from {count} files in {tok - tik:0.4f} seconds")

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
            if pd.isna(boatName):
                self.nanData.extend(group.values.tolist())
                continue
            
            if boatName not in self.boatsDataDictionary or not boatName:
                self.boatsDataDictionary[boatName] = BoatData(boatName)
            
            self.boatsDataDictionary[boatName].processGroup(group)

class BoatData(AIS):
    TIME_THRESHOLD = pd.Timedelta(days=1) #if entry appears on next day, belongs to same cruise

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

    def processGroup(self, group):
        #print('processing group', group['name'].head)
        group = self.orderGroupByTime(group)
        #print(group['bs_ts'].head)
        print(f'this group: {group.name[0]}, last boat: {self.previousBoatName} ')
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
    def __init__(self, cruiseID):
        super().__init__()
        self.data = pd.DataFrame(columns=['lat', 'lon', 'time'])
        self.cruiseID = cruiseID
        self.days = []
        self.time_records = []
    
    def __str__(self):
        return self.data.to_string()
    
    def getOtherCruises(self):
        if self.boatData is None:
            return []
        elif self.boatData.boatName in self.boatData.cruisesDataDictionary:
            return [cruise for cruise in self.boatData.cruisesDataDictionary.values() if cruise.cruiseName != self.cruiseName]
        else:
            return []

    def addGroup(self, group):
        """Adds a full group pd DataFrame object to the Cruise instance 
           on which the method is called
        """
        self.data = pd.concat([self.data, group], ignore_index=True)
        self.days.append(group['bs_ts'][0].date())
        
        #print('group added, appended to self.days:', self.days)
    
    def addNewRow(self, row):
        "dep"
        new_row = pd.DataFrame({'lat': [row['lat']], 'lon': [row['lon']], 'time': [row['bs_ts']]})
        self.data = pd.concat([self.data, new_row], ignore_index=True)
        self.time_records.append(pd.to_datetime(row['bs_ts']))

##### TESTING #####

data_folder = r'/Users/Graham/cruise/ais_data'
test_folder = r'/Users/Graham/cruise/test_data'

isTest = False

a = App(test_folder) if isTest else App(data_folder)

sum_of_points = 0
for boat_name, boat_data in a.boatsData.boatsDataDictionary.items():
    print(f"Boat: {boat_name}")
    for cruise_id, cruise_data in boat_data.cruisesDataDictionary.items():
        print(f"  Cruise ID: {cruise_id}")
        print(f"    {min(cruise_data.days).strftime('%Y/%m/%d')} - {max(cruise_data.days).strftime('%Y/%m/%d')}")
        print(f"       data points: {len(cruise_data.data)}")
        sum_of_points += len(cruise_data.data)

print(f'Expected point count: {a.rowsParsedCount}, actual point count: {sum_of_points}, nan point count: {len(a.boatsData.nanData)}, condition is: {sum_of_points+len(a.boatsData.nanData) == a.rowsParsedCount}')