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
        ais_data_within_glba = gpd.GeoDataFrame()
        new_rows = []
        filtered_data = []
        within_glba_data = []
        for boatName, boatData in self.boatsDataDictionary.items():
            print(f'processing {boatName}')
            data = boatData.flattenedCruises()
            data = data.sort_values(by='bs_ts')

            data = PortManager.populate_status_and_ports(data)
            data = PortManager.identify_status_changes(data)
            inPort_df = data[data.status == 'inPort'].sort_values('bs_ts')
            #inTransit_df = data[data.status == 'inTransit']

            within_glba = Geoprocessor.clip2(data, Geoprocessor.GLBA_BOUNDARY) # change this to be based on condition set during original check.
            within_glba_data.append(Geoprocessor.dataToGeodata(within_glba))
            grouped = within_glba.groupby('segment_id')
            for segment_id, group in grouped: # create summary row for each segment of points within GLBA
                ### enumerate segments to calculate metrics ###
                start_index, end_index = group.index[0], group.index[-1] # index of last point in GLBA boundary -> specify 'exit line'
                ts_in, ts_out = min(group.bs_ts), max(group.bs_ts)

                mmsi = int(group['mmsi'].unique()[0])
                imo = int(group['imo'].unique()[0])

                try:
                    start_index_next_port = inPort_df[inPort_df['segment_id'] > segment_id].index[0]
                except (IndexError):
                    start_index_next_port = end_index
                    print(f'segment {segment_id} was the first port visited, assigning as end_index (last point in GLBA)')
                try:
                    first_ts_in_next_port = inPort_df.bs_ts.at[start_index_next_port]
                except (KeyError, IndexError):  # Adjust the exception type as needed based on your error
                    first_ts_in_next_port = None
                try:
                    end_index_previous_port = inPort_df[inPort_df['segment_id'] < segment_id].index[-1]
                except (IndexError):
                    end_index_previous_port = start_index
                    print(f'segment {segment_id} was the first port visited, assigning as start_index (first point in GLBA)')
                    
                #PortManager.getFirstIndexInNextPort(data, end_index)
                #end_index_previous_port = PortManager.getLastIndexInPrevPort(data, start_index)

                ###### CALCULATE STATISTICS FROM GLBA EXIT -> NEXT PORT #######

                sub_between_glba_next_port = data.iloc[end_index+1 : start_index_next_port-1] # takes from point after last one in GLBA and up to one before mooring in the next port
                filtered_data.append(Geoprocessor.dataToGeodata(sub_between_glba_next_port))
                #print(f'added data of len {len(filtered_data[-1])} and type {type(filtered_data[-1])}')

                mean_sog = Statistics.mean(sub_between_glba_next_port, 'sog')

                portBefore = data['port'].iloc[end_index_previous_port]
                portAfter = data['port'].iloc[start_index_next_port]

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
                        'mmsi' : str(mmsi),
                        'imo' : str(imo),
                        'portAfter': str(portAfter),
                        'portBefore': str(portBefore),
                        'ts_in': ts_in,
                        'ts_out': ts_out,
                        'timeTo' : timelapse_to_next_port,
                        'distTo' : distance_to_next_port,
                        'first_ts_in_next_port' : first_ts_in_next_port,
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

        if len(within_glba_data) > 0:
            ais_data_within_glba = pd.concat(
                [gpd.GeoDataFrame(df, geometry = 'geometry', crs = "EPSG:4326") for df in within_glba_data],
                ignore_index=True
            )

        merged = BoatsData.merge_ais_claa_data(visit_table, BoatsData.CLAA_DATA)
        
        visit_count_table = visit_table.boatName.value_counts()
        popular_next_ports_table = visit_table.portAfter.value_counts()
        
        #* For 2023 AIS data, generate an accurate (cross checked) table of 
        # next port of call (including ‘at sea’), 
        # toTime, toDist, fromTime, fromDist
        # CLAA attributes where applicable
        # Dataframe will have 258 rows of data 
        # corresponding to each ship visit to the park. 
        
        return visit_table.sort_values(by='ts_in').reset_index(), ais_data_glba_to_next_port, ais_data_within_glba, merged#, count_glba_visits

    def sampleRoutes(self):
        """Combs through the imported boatdatas and gathers actual distances and durations between ports in the AIS data
           Using PathCalculations, generates these lists for each boatdata and concatenates
           returns (1) a big list and (2) summary stats for each port combo
        """
        new_transits = []
        new_ports = []
        for boatName, boatData in self.boatsDataDictionary.items():
            print(f'processing {boatName}')
            ports, transits = PathCalculations.get_transit_distances(boatData)
            new_transits.append(transits)
            new_ports.append(ports)
        big_transits = pd.concat(new_transits, ignore_index=True).sort_values('segment_id').reset_index()
        big_ports = pd.concat(new_ports, ignore_index=True).sort_values('segment_id').reset_index()

        stats_fields = ['distance_nm', 'duration_hrs']
        stats_type = ['mean','std','count']
        agg_dict = {field: stats_type for field in stats_fields}
        transits_stats = big_transits.groupby(['from_port', 'to_port']).agg(agg_dict).reset_index()

        unique_segment_ids = big_transits.groupby(['from_port', 'to_port'])['segment_id'].apply(lambda x: list(x.unique())).reset_index(name='unique_segment_ids')
        transits_stats = pd.merge(transits_stats, unique_segment_ids, on=['from_port', 'to_port'])
        transits_stats.columns = ['_'.join(col).strip() if isinstance(col, tuple) and col[1] else col[0] for col in transits_stats.columns]
        transits_stats = transits_stats.rename(columns={'f' : 'portName', 't' : 'nextPort', 'u' : 'segment_ids'})
        transits_stats['portName'] = transits_stats['portName'].apply(lambda x: str(x).upper())
        transits_stats['nextPort'] = transits_stats['nextPort'].apply(lambda x: str(x).upper())
        
        return big_ports, big_transits, transits_stats

    def assessGlaciers(self):
        for boatName, boatData in self.boatsDataDictionary.items():
            pass

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



