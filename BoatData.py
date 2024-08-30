from AIS import AIS
from CruiseSorter import CruiseSorter
from Geoprocessor import Geoprocessor
from Slicer import Slicer
import pandas as pd
import geopandas as gpd
import os
import secrets
import time
import matplotlib.pyplot as plt

from typing import Dict
from Cruise import Cruise
from datetime import datetime
from PathCalculations import PathCalculations
import pytz

class BoatData(AIS):
    GLBA_BOUNDARY = gpd.read_file(r'./data/shapes/port_GLBA.shp')
    GLBA_BOUNDARY = GLBA_BOUNDARY.set_crs(epsg=4326)

    def __init__(self, boatName):
        super().__init__()
        self.cruisesDataDictionary = {}  # Dictionary to store Cruise instances
        self.boatName = boatName  # Store boat name

        self._previousCruise = None # Reference to the last Cruise edited

    def __str__(self):
        string = ''
        for key, value in self.cruisesDataDictionary.items():
            string = string + str(key) + ": " + str(value) + '\n'
        return string
    
    #### READING DATA ####

    def flattenedCruises(self) -> gpd.GeoDataFrame:
        """returns a summary of all the data together for the season.
        """
        df = gpd.GeoDataFrame()
        for cruise_id, cruise_data in self.cruisesDataDictionary.items():
            df = pd.concat([df, cruise_data.data], ignore_index=True)
        #print('here is the flattened set of cruises')
        return df
    
    def aggregateGeodata(self): # not called
        """returns a flattened GeoDataFrame of all Cruise geodata from this boatData's cruiseDataDict
        """
        all_gdf = [cruise.gdf for _, cruise in self.cruisesDataDictionary.items() if cruise.gdf is not None]
        return Geoprocessor.aggregate(all_gdf)

    def isEmpty(self):
        return not self.cruisesDataDictionary
    
    #### IMPORTING DATA ####

    def processGroup(self, group):
        group = Slicer.orderGroupByTime(group) # convert group contents to AKDT and order as timestamps type
        self._sortAndAddGroupToDictionary(group)

    #### SORTING DATA HELPERS (These helper functions mutate the cruisesDataDictionary) ####

    def _sortAndAddGroupToDictionary(self, group: pd.DataFrame) -> None: 
        """
        Sort new data into existing cruises or create new cruises as needed.
        Args:
            group (new_data) (pd.DataFrame): DataFrame containing the new data to be sorted.
        """
        # IF THIS GROUP MATCHES PREVIOUS CRUISE WE WORKED WITH
        if self._previousCruise and self._previousCruise.shouldGroupBeAdded(group):
            self._addGroupToCruise(self._previousCruise, group)
            #print(f'matched to previous')
            return
        
        # ITERATE TO FIND THE MATCH THEN ADD
        for cruise_id, cruise in self.cruisesDataDictionary.items():
            if cruise.shouldGroupBeAdded(group):
                self._addGroupToCruise(cruise, group)
                print(f'searched and found matching cruise {cruise_id}')
                return
        
        # DEFAULT TO CREATING AND POPULATING AN EMPTY CRUISE
        newCruise = self._incrementCruisesDataDictionary()
        self._addGroupToCruise(self.newCruise, group)
        print(f'created new cruise for this: {newCruise.cruiseID}')
        return

    def _incrementCruisesDataDictionary(self) -> Cruise:
        """Creates a new entry in cruisesDataDictionary with an incremented cruiseID and returns a reference to the new instance."""
        next_cruise_number = len(self.cruisesDataDictionary) + 1
        cruise_id = f"{self.boatName}_{next_cruise_number:02d}"
        self.cruisesDataDictionary[cruise_id] = Cruise(cruise_id)
        return self.cruisesDataDictionary[cruise_id]

    def _addGroupToCruise(self, cruise, group) -> None:
        cruise.addGroup(group)
        self._previousCruise = cruise