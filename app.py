# Main application class
#from ship import *
#from BoatData import BoatData
from Cruise import Cruise
from BoatData import BoatData
from BoatsData import BoatsData
from Geoprocessor import Geoprocessor

import os
import secrets
import time
import matplotlib.pyplot as plt
from datetime import datetime
from PathCalculations import PathCalculations
import pytz

#from analyst import *
import random
import time
import os
import pandas as pd



class App:
    def __init__(self, dataFolder):
        self.data_dict = {}  # Dictionary to hold BoatsDatas and associated ais_summary data by ais_ID
        self.rowsParsedCount = 0

        if not os.path.isdir(dataFolder):
            raise ValueError(f"The provided path {dataFolder} is not a directory or does not exist.")

        for subfolder in os.listdir(dataFolder):
            subfolder_path = os.path.join(dataFolder, subfolder)
            if os.path.isdir(subfolder_path):
                self.processFolder(subfolder_path)


    def processFolder(self, folder_path):
        data_id = os.path.basename(folder_path.rstrip('/\\'))
        boatsData = BoatsData()  # Create a new BoatsData instance
        self.data_dict[data_id] = {
            'boatsData': boatsData,
            'glba_visit_table': None,
            'ais_data': {
                'glba_to_next_port': None,
                'within_glba': None,
                'merged': None
            },
            'sampled_routes': {
                'ports': None,
                'transits': None,
                'transit_table': None
            }
        }

        self.populateBoatsData(boatsData, folder_path)
        

        visit_table, ais_data_glba_to_next_port, ais_data_within_glba, merged = boatsData.run_glba_workflow()
        self.data_dict[data_id]['glba_visit_table'] = visit_table
        self.data_dict[data_id]['ais_data']['glba_to_next_port'] = ais_data_glba_to_next_port
        self.data_dict[data_id]['ais_data']['within_glba'] = ais_data_within_glba
        self.data_dict[data_id]['ais_data']['merged'] = merged


        ais_ports, ais_transits, ais_transit_table = boatsData.sampleRoutes()
        self.data_dict[data_id]['sampled_routes']['ports'] = ais_ports
        self.data_dict[data_id]['sampled_routes']['transits'] = ais_transits
        self.data_dict[data_id]['sampled_routes']['transit_table'] = ais_transit_table

    def populateBoatsData(self, boatsData, dataFolder):
        tik = time.perf_counter()
        count=0
        for dirs, _, files in os.walk(dataFolder):
            for f in sorted(files):
                if f.endswith('csv'):
                    count+=1
                    file_path = os.path.join(dirs, f)
                    rows = pd.read_csv(file_path)  # Read CSV file into DataFrame
                    #print(f'Starting parsing file: {f}')
                    boatsData.parseRows(rows)  # Parse rows into boatsData
                    self.rowsParsedCount += len(rows)
                    #print(f'Finished parsing file: {f}')

        tok = time.perf_counter()
        print(f"Imported data from {count} files in {tok - tik:0.4f} seconds")
        print(f"Parsed {self.rowsParsedCount} rows in this import.")

    def getFlattenedAISData(self, ais_id):
        ais_data = self.data_dict[ais_id]['boatsData'].flatten() # extract all AIS data to one spot
        ais_data.mmsi = ais_data.mmsi.astype(int).astype(str)
        ais_data.imo = ais_data.imo.astype(int).astype(str)
        return ais_data

    def getGLBAVisitTable(self, ais_id):
        return self.data_dict[ais_id]['glba_visit_table']



    def getAISTransitTable(self, ais_id):
        return self.data_dict[ais_id]['sampled_routes']['transit_table']
    
    def __str__(self):
        return str(self.boatsData)  # String representation of boatsData
    
    def __repr__(self):
        sum_of_points = 0
        for boat_name, boat_data in self.boatsData.boatsDataDictionary.items():
            print(f"Boat: {boat_name}")
            for cruise_id, cruise_data in boat_data.cruisesDataDictionary.items():
                print(f"  Cruise ID: {cruise_id}")
                print(f"    {min(cruise_data.days).strftime('%Y/%m/%d')} - {max(cruise_data.days).strftime('%Y/%m/%d')}")
                print(f"       data points: {len(cruise_data.data)}")
                sum_of_points += len(cruise_data.data)

        print(f'Expected point count: {self.rowsParsedCount}, actual point count: {sum_of_points}, nan point count: {len(self.boatsData.nanData)}, condition is: {sum_of_points+len(self.boatsData.nanData) == self.rowsParsedCount}')
        return 'here ya go'

    def getRandomCruise(self):
        """returns a random cruise object for testing
        """
        # Step 1: Get a random boat
        boat_name, boat_data = random.choice(list(a.boatsData.boatsDataDictionary.items()))

        # Step 2: Get a random cruise for the selected boat
        cruise_id, cruise_data = random.choice(list(boat_data.cruisesDataDictionary.items()))

        return cruise_data