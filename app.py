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
        self.boatsData = BoatsData()  # Initialize BoatsData instance
        self.rowsParsedCount = 0
        self.populateBoatsData(dataFolder)  # Populate boatsData with data from CSV files

        self.visit_table, self.ais_data_glba_to_next_port, self.ais_data_within_glba, self.merged = self.boatsData.run_glba_workflow()
        # self.boatsData.initializeStatistics()

    def getAISData(self):
        ais_data = self.boatsData.flatten() # extract all AIS data to one spot
        ais_data.mmsi = ais_data.mmsi.astype(int).astype(str)
        ais_data.imo = ais_data.imo.astype(int).astype(str)
        return ais_data

    def sampleRoutes(self):
        """Combs through the imported boatdatas and gathers actual distances and durations between ports in the AIS data
           Using PathCalculations, generates these lists for each boatdata and concatenates
           returns (1) a big list and (2) summary stats for each port combo
        """
        new_dfs = []
        for boatName, boatData in self.boatsData.boatsDataDictionary.items():
            print(f'processing {boatName}')
            _, transits = PathCalculations.get_transit_distances(boatData)
            new_dfs.append(transits)
        big_transits = pd.concat(new_dfs, ignore_index=True).sort_values('segment_id').reset_index()

        stats_fields = ['distance_nm', 'duration_hrs']
        stats_type = ['mean','std','count']
        agg_dict = {field: stats_type for field in stats_fields}

        stats = big_transits.groupby(['from_port', 'to_port']).agg(agg_dict).reset_index()

        unique_segment_ids = big_transits.groupby(['from_port', 'to_port'])['segment_id'].apply(lambda x: list(x.unique())).reset_index(name='unique_segment_ids')
        stats = pd.merge(stats, unique_segment_ids, on=['from_port', 'to_port'])

        stats.columns = ['_'.join(col).strip() if col[1] else col[0] for col in stats.columns]

        return big_transits, stats

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

    def populateBoatsData(self, dataFolder):
        tik = time.perf_counter()
        count=0
        for dirs, _, files in os.walk(dataFolder):
            for f in sorted(files):
                if f.endswith('csv'):
                    count+=1
                    file_path = os.path.join(dirs, f)
                    rows = pd.read_csv(file_path)  # Read CSV file into DataFrame
                    #print(f'Starting parsing file: {f}')
                    self.boatsData.parseRows(rows)  # Parse rows into boatsData
                    self.rowsParsedCount += len(rows)
                    #print(f'Finished parsing file: {f}')

        tok = time.perf_counter()
        print(f"Imported data from {count} files in {tok - tik:0.4f} seconds")
        print(f"Parsed {self.rowsParsedCount} rows in this import.")

    def getRandomCruise(self):
        """returns a random cruise object for testing
        """
        # Step 1: Get a random boat
        boat_name, boat_data = random.choice(list(a.boatsData.boatsDataDictionary.items()))

        # Step 2: Get a random cruise for the selected boat
        cruise_id, cruise_data = random.choice(list(boat_data.cruisesDataDictionary.items()))

        return cruise_data