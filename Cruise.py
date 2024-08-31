import pandas as pd
from AIS import AIS
from Slicer import Slicer
from Geoprocessor import Geoprocessor


import os
import secrets
import time
import matplotlib.pyplot as plt
from datetime import datetime
from PathCalculations import *
import pytz


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

    DOCK_BUFFERS = gpd.read_file(r'./data/buffers/docks_albers_2000m_buffer.shp')

    ##### CONSTRUCTORS AND REPRESENTATION #####
    
    def __init__(self, cruiseID):
        super().__init__()
        self.data = gpd.GeoDataFrame(columns=['lat', 'lon', 'bs_ts', 'geometry'], geometry = 'geometry') #use gdf as primary data storage, add Geometries and other attributes during data import.
        self.df_list = []

        self.cruiseID = cruiseID

        self.boatName = None

        self.geoprocessor = None
        self.slicer = None

        self.days = []
        self.time_records = []

    def __str__(self):
        return self.data.to_string()

    ##### MAIN IMPORT FUNCTIONALITIES #####

    def _init_geodata(self, group):
        return Geoprocessor.dataToGeodata(group)
    
    def addGroup(self, group):
        """Adds a full group pd DataFrame object to the Cruise instance 
           on which the method is called
        """
        #self.df_list.append(self._init_geodata(group))
        self.data = pd.concat([self.data, self._init_geodata(group)], ignore_index=True) #converts and adds new data to end of existing geodata
        self.days.append(group['bs_ts'][0].date())

    def concatenateDataList(self):
        """converts data storage from list to big DataFrame to avoid costly copying
        """
        self.data = pd.concat([self.data] + self.df_list, ignore_index=True)
        self.df_list = [] # reset DF's since storage is now in self.data after import

    def addCruiseToShapfile(self, shapefile):
        """adds a cruise's geodataframe to a feature in an ESRI shapefile. This generally would come after the cropping and conversion from point to line data
        """
        # self.dataToGeodata()
        self.assignPorts()
        port = self.getPortAfterGlacierBay()

    def shouldGroupBeAdded(self, group: pd.DataFrame) -> bool:
        """
        Determine if an unassigned group matches a given cruise based on a time threshold.
        """
        max_timestamp = self.data['bs_ts'].max()
        min_timestamp = group['bs_ts'].min()

        if (min_timestamp - max_timestamp) <= cls.TIMELAPSE_THRESHOLD:
        #if unassigned_group.name.mode()[0] == cruise.data.name.mode()[0]:
            return True
        return False