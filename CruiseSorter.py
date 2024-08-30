import pandas as pd
import geopandas as gpd

from Cruise import Cruise
from SegmentNode import SegmentNode
from Segments import Segments
from PortManager import PortManager


class CruiseSorter:
    """Hands operations related to sorting data into cruises, returning flattened cruises for a whole boat,
    manageing the data import and triage 
    """
    #TIMELAPSE_THRESOLD = BoatData.TIME_THRESHOLD
    TIMELAPSE_THRESHOLD = pd.Timedelta(hours = 10)
    DEFINITE_INCREMENTATION = pd.Timedelta(days = 1)

    def __init__(self, BoatData):
        self.boatData = BoatData
        self.previousCruise = None # Placeholder for last Cruise edited
        self.currentCruise = None

    def convert_to_segments(self):
        """generates a Segments object (doubly linked list with SegmentNodes of AIS data). 
           Each state change connects the nodes: inPort, inTransit, inPort, etc.
           Use for flattening and resorting data into a cruise itinerary format.
        """
        big_df = self.flattenCruises() # if needed
        big_df.set_geometry('geometry')
        big_df = PortManager.populate_status_and_ports(big_df) # assigns rows as either inTransit/inPort and with geofence Port name or AtSea
        big_df = PortManager.identify_status_changes(big_df)
        
        big_df.sort_values(by='segment_id')
        grouped = big_df.groupby('segment_id')

        #instantiate DLL and populate with each SegmentNode in chronological order, assign segmentID, return entire DLL from CruiseSorter.
        segments = Segments()
        for segment_id, group in grouped:
            #print('adding node')
            segments.add_node(group, segment_id)
        
        return segments
        
    def assign_cruise_id_from_segments(self):
        pass

    ########## SORTING METHODS FOR DATA IMPORT ############

    @classmethod
    def is_matching_cruise(cls, unassigned_group: pd.DataFrame, cruise) -> bool:
        """
        Determine if an unassigned group matches a given cruise based on a time threshold.
        """
        max_timestamp = cruise.data['bs_ts'].max()
        min_timestamp = unassigned_group['bs_ts'].min()

        if (min_timestamp - max_timestamp) <= cls.TIMELAPSE_THRESHOLD:
        #if unassigned_group.name.mode()[0] == cruise.data.name.mode()[0]:
            return True
        return False

    def sort_group(self, group: pd.DataFrame) -> None: 
        """
        Sort new data into existing cruises or create new cruises as needed.
        Args:
            group (new_data) (pd.DataFrame): DataFrame containing the new data to be sorted.
        """
        # IF THIS GROUP MATCHES PREVIOUS CRUISE WE WORKED WITH
        if self.previousCruise and self.is_matching_cruise(group, self.previousCruise):
            self.addToCruise(group, self.previousCruise)
            #print(f'matched to previous')
            return
        
        # ITERATE TO FIND THE MATCH THEN ADD
        for cruise_id, cruise_data in self.boatData.cruisesDataDictionary.items():
            if self.is_matching_cruise(group, cruise_data):
                self.currentCruise = cruise_data
                self.addToCruise(group, self.currentCruise)
                print(f'searched and found matching cruise {cruise_id}')
                return
        
        # DEFAULT TO CREATING AND POPULATING AN EMPTY CRUISE
        self.createEmptyCruise()
        self.addToCruise(group, self.currentCruise)
        print(f'created new cruise for this: {self.currentCruise.cruiseID}')
        return

    def addToCruise(self, unassigned_group, cruise) -> None:
        cruise.addGroup(unassigned_group) #main add function
        #print('adding cruise within CruiseSorter')
        cruise.data['cruise_id'] = cruise.cruiseID #update cruiseID
        self.previousCruise = cruise

    def createEmptyCruise(self) -> None:
        """Creates a new cruise, initializing or incrementing cruise ID."""
        if self.boatData.isEmpty():
            self.initializeCruisesDataDictionary()
        else:
            self.incrementCruisesDataDictionary()

    def initializeCruisesDataDictionary(self) -> None:
        """Assigns the first cruiseID using the boat name and creates an empty cruisesDataDictionary."""
        cruise_id = f"{self.boatData.boatName}_01"
        self.boatData.cruisesDataDictionary = {}  # Initialize the dictionary
        self.boatData.cruisesDataDictionary[cruise_id] = Cruise(cruise_id)
        self.currentCruise = self.boatData.cruisesDataDictionary[cruise_id]

    def incrementCruisesDataDictionary(self) -> None:
        """Creates a new entry in cruisesDataDictionary with an incremented cruiseID, updates instance variables."""
        next_cruise_number = len(self.boatData.cruisesDataDictionary) + 1
        cruise_id = f"{self.boatData.boatName}_{next_cruise_number:02d}"
        self.boatData.cruisesDataDictionary[cruise_id] = Cruise(cruise_id)
        self.currentCruise = self.boatData.cruisesDataDictionary[cruise_id]
    
    def predictCruiseID(self, unassigned_group) -> str:
        for _, cruise_data in self.boatData.items():
            if cruise_data.data.name.contains(unassigned_group.name.mode()[0]).any():
                self.currentCruise = cruise_data
                return 'Found Match'
                break
        else:
            return 'No Matches'
        
    ######## ADDITIONAL METHODS ###########

    def flattenCruises(self) -> gpd.GeoDataFrame:
        """returns a summary of all the data together from self.boatData for the season.
        """
        df = gpd.GeoDataFrame()
        for cruise_id, cruise_data in self.boatData.cruisesDataDictionary.items():
            df = pd.concat([df, cruise_data.data], ignore_index=True)
        #print('here is the flattened set of cruises')
        return df   

    def get_cruise_match(self, group):
        for cruise_id, cruise_data in self.boatData.cruisesDataDictionary.items():
            if self.is_matching_cruise(group, cruise_data):
                return cruise_data
        return None
            
    @staticmethod
    def match(unassigned_group, cruise): #deprecated
        """
        Static method to check if unassigned data matches a cruise based on time thresholds.
        """
        max_timestamp = cruise.data['bs_ts'].max()
        min_timestamp = unassigned_group['bs_ts'].min()
        return (min_timestamp - max_timestamp) <= CruiseSorter.TIMELAPSE_THRESHOLD