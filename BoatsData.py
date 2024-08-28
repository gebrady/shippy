from BoatData import BoatData
from Statistics import Statistics

import pandas as pd
import geopandas as gpd

import os
import secrets
import time
import matplotlib.pyplot as plt
from datetime import datetime
from pathcalculations import *
import pytz

#from ship import *

class BoatsData:
    ALASKA_COASTLINE = gpd.read_file(r'./shapes/Alaska_Coastline/Alaska_Coastline.shp')
    ALASKA_COASTLINE_ALBERS = ALASKA_COASTLINE.to_crs(epsg=3338)
    ALASKA_COASTLINE_WGS84 = ALASKA_COASTLINE.to_crs(epsg=4326)

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
        grouped = rows.groupby('name', dropna = False)
        
        for boatName, group in grouped:
            group = group.sort_values(by='bs_ts', ascending=True)
            if pd.isna(boatName):
                self.nanData.extend(group.values.tolist())
                continue
            
            if boatName not in self.boatsDataDictionary or not boatName:
                self.boatsDataDictionary[boatName] = BoatData(boatName)
            
            self.boatsDataDictionary[boatName].processGroup(group)

    def initializeStatistics(self):
        self.statistics = Statistics(self)

    def flatten(self):
        df = pd.DataFrame()
        for _, boat_data in self.boatsDataDictionary.items():
            df = pd.concat([df, boat_data.sorter.flattenCruises()], ignore_index = True)
        return df

