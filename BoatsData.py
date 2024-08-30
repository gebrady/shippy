from BoatData import BoatData
from Statistics import Statistics
from PortManager import PortManager
from Cruise import Cruise

import pandas as pd
import geopandas as gpd
from Geoprocessor import Geoprocessor

import os
import secrets
import time
import matplotlib.pyplot as plt
from datetime import datetime
from PathCalculations import PathCalculations
import pytz

#from ship import *

class BoatsData:
    CLAA_DATA = pd.read_csv(r'./data/calendar/allyears_allports_claa.csv')
    ALASKA_COASTLINE = gpd.read_file(r'./data/shapes/Alaska_Coastline/Alaska_Coastline.shp')
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
            df = pd.concat([df, boat_data.flattenedCruises()], ignore_index = True)
        return df

    def run_glba_workflow(self):
        count_glba_visits = 0
        visit_table = pd.DataFrame()
        ais_data_glba_to_next_port = gpd.GeoDataFrame()
        new_rows = []
        filtered_data = []
        for boatName, boatData in self.boatsDataDictionary.items():
            print(f'processing {boatName}')
            data = boatData.flattenCruises()

            data = PortManager.populate_status_and_ports(data)
            data = PortManager.identify_status_changes(data)

            within_glba = Geoprocessor.clip2(data, Geoprocessor.GLBA_BOUNDARY) # change this to be based on condition set during original check.
            
            grouped = within_glba.groupby('segment_id')
            for segment_id, group in grouped: # create summary row for each segment of points within GLBA
                ### enumerate segments to calculate metrics ###
                start_index, end_index = group.index[0], group.index[-1] # index of last point in GLBA boundary -> specify 'exit line'
                ts_in, ts_out = min(group.bs_ts), max(group.bs_ts)

                start_index_next_port = data[data['segment_id'] == segment_id].index[-1] + 1
                end_index_previous_port = data[data['segment_id'] == segment_id].index[0] - 1
                #PortManager.getFirstIndexInNextPort(data, end_index)
                #end_index_previous_port = PortManager.getLastIndexInPrevPort(data, start_index)


                ###### CALCULATE STATISTICS FROM GLBA EXIT -> NEXT PORT #######

                sub_between_glba_next_port = data.iloc[end_index+1 : start_index_next_port-1] # takes from point after last one in GLBA and up to one before mooring in the next port
                filtered_data.append(Geoprocessor.dataToGeodata(sub_between_glba_next_port))
                #print(f'added data of len {len(filtered_data[-1])} and type {type(filtered_data[-1])}')

                mean_sog = Statistics.mean(sub_between_glba_next_port, 'sog')

                portBefore = group['previous_port'].iloc[-1]
                portAfter = group['next_port'].iloc[-1]

                max_speed = sub_between_glba_next_port['sog'].max()

                try:
                    arrival_in_next_port = data.bs_ts.iloc[start_index_next_port]
                    timelapse_to_next_port = PathCalculations.timelapseAlongPath(data.bs_ts, end_index, start_index_next_port)
                    _, distance_to_next_port = PathCalculations.distanceAlongPath_nm(data.geometry, end_index, start_index_next_port)
    
                    timelapse_from_previous_port = PathCalculations.timelapseAlongPath(data.bs_ts, end_index_previous_port, start_index)
                    _, distance_from_previous_port = PathCalculations.distanceAlongPath_nm(data.geometry, end_index_previous_port, start_index)
                except IndexError:
                    print(f"Warning: start_index_next_port {start_index_next_port} is out of bounds. Assigning default values for {boatName}.")
                    arrival_in_next_port = None  # Assigning None or a default value, e.g., pd.Timestamp('NaT')
                    timelapse_to_next_port = None
                    distance_to_next_port = None
                    timelapse_from_previous_port = None
                    distance_from_previous_port = None

                new_row = {
                        'date' : list(set(group.bs_ts.dt.date)),
                        'boatName': boatName,
                        'mmsi' : 'num',
                        'portAfter': str(portAfter),
                        'portBefore': str(portBefore),
                        'ts_in': ts_in,
                        'ts_out': ts_out,
                        'timeTo' : timelapse_to_next_port,
                        'distTo' : distance_to_next_port,
                        'mean_sog' : mean_sog,
                        'max_sog' : max_speed,
                        #'calc_kts' : distance_to_next_port/timelapse_to_next_port
                        #'arrival' : arrival_in_next_port,
                        #'timeFrom' : timelapse_from_previous_port,
                        #'distFrom' : distance_from_previous_port,
                        'segment_id': segment_id
                }
                new_rows.append(new_row)
                count_glba_visits += 1

        if new_rows:
            visit_table = pd.concat([visit_table, pd.DataFrame(new_rows)], ignore_index=True)

        if len(filtered_data) > 0:
            ais_data_glba_to_next_port = pd.concat(
                [gpd.GeoDataFrame(df, geometry='geometry', crs="EPSG:4326") for df in filtered_data], 
                ignore_index=True
            )
            #ais_data_glba_to_next_port = pd.concat([ais_data_glba_to_next_port, gpd.GeoDataFrame(filtered_data)])

        merged = BoatsData.merge_ais_claa_data(visit_table, BoatsData.CLAA_DATA)
        
        visit_count_table = visit_table.boatName.value_counts()
        popular_next_ports_table = visit_table.portAfter.value_counts()
        
        #* For 2023 AIS data, generate an accurate (cross checked) table of 
        # next port of call (including ‘at sea’), 
        # toTime, toDist, fromTime, fromDist
        # CLAA attributes where applicable
        # Dataframe will have 258 rows of data 
        # corresponding to each ship visit to the park. 
        
        return visit_table.sort_values(by='ts_in').reset_index(), ais_data_glba_to_next_port, visit_count_table, popular_next_ports_table, merged, count_glba_visits

    def import_claa_data(self):
        claa_df = pd.read_csv(BoatsData.CLAA_DATA_FILEPATH)
        claa_df['year'] = pd.to_datetime(claa_df['date']).dt.year
        claa_df = claa_df[['date','year','boatName','portName','nextPort','ts_in','ts_out']]
        self.claa_data = claa_df
    
    @staticmethod
    def merge_ais_claa_data(data, claa_df):
        data['date'] = pd.to_datetime(data['date'].apply(lambda x: x[0] if isinstance(x, list) else x))
        #data['date'] = pd.to_datetime(data['date'])
        claa_df['date'] = pd.to_datetime(claa_df['date'])
        merged = data.merge(claa_df,
                            on=['boatName', 'date'], how='inner', suffixes=('_ais', '_claa'))
        return merged[['date', 'boatName',
                       'portAfter', 'nextPort', 'portBefore', #'prevPort',
                       'ts_in_ais', 'ts_in_claa', 'ts_out_ais', 'ts_out_claa']]

    @staticmethod
    def filter_claa_data_by_year(data, year):
        return data[data['year'] == year]
    
    @staticmethod
    def filter_claa_data_by_port(data, port):
        return data[data['portName'] == port]



