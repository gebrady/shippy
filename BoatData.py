from AIS import AIS
from CruiseSorter import CruiseSorter
from Geoprocessor import Geoprocessor
import pandas as pd
import geopandas as gpd
import os
import secrets
import time
import matplotlib.pyplot as plt
from datetime import datetime
from pathcalculations import *
import pytz



class BoatData(AIS):
    TIME_THRESHOLD = pd.Timedelta(days=1) #if entry appears on next day, belongs to same cruise
    GLBA_BOUNDARY = gpd.read_file(r'./shapes/port_GLBA.shp')
    GLBA_BOUNDARY = GLBA_BOUNDARY.set_crs(epsg=4326)

    def __init__(self, boatName):
        super().__init__()
        self.cruisesDataDictionary = {}  # Dictionary to store Cruise instances
        self.boatName = boatName  # Store boat name

        self.sorter = CruiseSorter(self)

        self.previousBoatName = '' # this is redundant should be a double check
        self.cruiseID = None ####
        self.previousCruiseID = ''

    def __str__(self):
        string = ''
        for key, value in self.cruisesDataDictionary.items():
            string = string + str(key) + ": " + str(value) + '\n'
        return string
    
    #### IMPORTING DATA ####

    def processGroup(self, group):
        group = self.orderGroupByTime(group) # convert group contents to AKDT and order as timestamps type
        self.sorter.sort_group(group)
        self.previousCruiseID = self.cruiseID
        self.previousBoatName = self.boatName

    def isEmpty(self):
        return not self.cruisesDataDictionary
    
    # def add_cruise(self, cruise: Cruise) -> None:
    #     """Add a new cruise to the list of cruises."""
    #     self.cruisesDataDictionary[cruise.cruiseID] = cruise


    def processGroup2(self, group):
        #print("Before sorting:", group)
        group = self.orderGroupByTime(group) # convert group contents to AKDT and order as timestamps type
        #print("After sorting:", group)

        if self.matchesLastCruise(group): # if belongs to previous cruise of this boatName
            self.cruisesDataDictionary[self.previousCruiseID].addGroup(group)
            #print('matches previous cruiseID')
        else:
            if self.cruiseID is None: #initialize if first cruiseID for this boatName
                print(f'initializing for {self.boatName}')
                self.initializeCruisesDataDictionary()
                self.cruisesDataDictionary[self.cruiseID].addGroup(group)
            else:
                print('sorting')
                self.sortToCruise(group)

        self.previousCruiseID = self.cruiseID
        self.previousBoatName = self.boatName

    ##################
    ## Sorting Data ##

    def matchesLastCruise(self, group):
        if self.cruiseID is None:
            return False
        time_diff = self.cruisesDataDictionary[self.previousCruiseID].data.bs_ts.max() - group.bs_ts.min()
        time_diff_hours = time_diff.total_seconds()/3600
        return self.previousBoatName == self.boatName and abs(time_diff_hours) <= 1.5 # basic Logic for new to sort all cruises to same based on boat Name
    
    def sortToCruise(self, group):
        #group_date = group['bs_ts'][0].date()
        for cruiseID, cruiseData in self.cruisesDataDictionary.items():
            time_diff = cruiseData.data.bs_ts.max() - group.bs_ts.min()
            time_diff_hours = time_diff.total_seconds()/3600
            if abs(time_diff_hours) <= 1.5: # update this when needed for additional sorting
                self.cruiseID = cruiseID
                self.cruisesDataDictionary[self.cruiseID].addGroup(group)
                print('found matching boatName and added group')
                break
        else: # no matches found in the cruiseDataDict, need to increment and add to that cruiseID
            print(f'new cruise identified for {self.boatName}')
            self.incrementCruisesDataDictionary()
            self.cruisesDataDictionary[self.cruiseID].addGroup(group)
            print(f'incremented and added a cruise at {self.cruiseID}')


    ####### HELPER FUNCTIONS #######

    def orderGroupByTime(self, group):
        """Orders the input group chronologically (timestamps) and returns the group 
           in the new order with an object desribing the date for those data.
        """
        group['bs_ts'] = pd.to_datetime(group['bs_ts'], utc = True).dt.tz_convert(pytz.timezone('US/Alaska'))
        group.sort_values(by='bs_ts', inplace=True)
        return group.reset_index(drop=True)

    def initializeCruisesDataDictionary(self): # deprecated
        """Assigns first cruiseID using boat name, creates an empty cruisesDataDictionary.
        """
        self.cruiseID = self.boatName + '_01'
        self.cruisesDataDictionary[self.cruiseID] = Cruise(self.cruiseID)
 
    def incrementCruisesDataDictionary(self):
        """creates a new entry in cruisesDataDictionary with an incremented cruiseID, updates instance variables.
        """
        self.cruiseID = self.boatName + f'_{len(self.cruisesDataDictionary) + 1:02d}'
        self.cruisesDataDictionary[self.cruiseID] = Cruise(self.cruiseID)
   
   ######## DEPRECATED ##########

    def sortAndAddGroup(self, group): ##### DEPRECATED?
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

    def sortAndAddGroup2(self, group): ##### DEPRECATED?
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

    ##### MANAGEMENT METHODS #####

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
