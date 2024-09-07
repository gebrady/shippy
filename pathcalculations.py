import geopandas as gpd
from geopy.distance import distance
from shapely.geometry import Point, LineString
from geopy.distance import geodesic
from PortManager import PortManager

import pandas as pd
import os

class PathCalculations:
    @staticmethod
    def distanceAlongPath(geometry, start_index, end_index):
        """returns the distance along the path that connects points in self.gdf between start and end indices, inclusive
           returns the list of individual distances in meters and then the total distance in kilometers
        """
        distances = []
        for i in range(start_index, end_index):
            point1 = geometry.iloc[i]
            point2 = geometry.iloc[i + 1]
            distances.append(geodesic((point1.y, point1.x), (point2.y, point2.x)).meters)
        return distances, round(sum(distances)/1000,2) #distance in km
    
    @staticmethod
    def distanceAlongPath_nm(geometry, start_index, end_index):
        """returns the distance along the path that connects points in self.gdf between start and end indices, inclusive
           returns the list of individual distances in meters and then the total distance in kilometers
        """
        distances = []
        for i in range(start_index, end_index):
            point1 = geometry.iloc[i]
            point2 = geometry.iloc[i + 1]
            distances.append(geodesic((point1.y, point1.x), (point2.y, point2.x)).meters/1852)
        return distances, round(sum(distances), 2) #distance in nm (nautical miles)

    @staticmethod
    def timelapseAlongPath(timestamps, start_index, end_index):
        times = []
        for i in range(start_index, end_index):
            point1 = timestamps.iloc[i]
            point2 = timestamps.iloc[i + 1]
            times.append((point2-point1).total_seconds()/3600)
        return round(sum(times), 3) # time in hours
    

    def calculate_sinuosity(data, start_index, end_index):
        actual_distance = PathCalculations.distanceAlongPath_nm(data.geometry, start_index, end_index)[1]
        straight_line_distance = data.geometry.iloc[start_index].distance(data.geometry.iloc[end_index])
        return actual_distance / straight_line_distance if straight_line_distance > 0 else 1.0
    
    @staticmethod
    def get_transit_distances(boatData):
        """calculate all the actual ais path lengths """
        data = boatData.flattenedCruises()
        data = data.sort_values(by='bs_ts')

        data = PortManager.populate_status_and_ports(data)
        data = PortManager.identify_status_changes(data)

        ports = pd.DataFrame(columns = ['segment_id', 'port', 'start_index', 'end_index',
                                        'port_duration', 'timelapse', 'time_in', 'time_out'])
        transits = pd.DataFrame(columns = ['segment_id', 'from_port', 'to_port', 'start_index', 'end_index',
                                          'distance_nm', 'duration_hrs', 'average_sog', 'start_time', 'end_time'])
        port_data_list = []
        transit_data_list = []
        segments = data.groupby('segment_id')
        for segment_id, segment in segments:
            start_index = segment.index[0]
            end_index = segment.index[-1]
            if segment.status.iloc[0] == 'inPort':
                time_in = segment.bs_ts.iloc[0]
                time_out = segment.bs_ts.iloc[-1]
                try:
                    timelapse_to_next_port = PathCalculations.timelapseAlongPath(data.bs_ts, start_index, end_index)
                except IndexError:
                    print(f"Warning: end_index {end_index} is out of bounds. Assigning default values for timelapse.")
                    timelapse_to_next_port = None

                new_port = {'segment_id' : segment_id,
                            'port' : segment.port.iloc[0],
                            'start_index' : start_index,
                            'end_index' : end_index,
                            'port_duration' : (time_out-time_in).total_seconds() / 3600,
                            'timelapse' : timelapse_to_next_port,
                            'time_in' : time_in,
                            'time_out' : time_out}
                port_data_list.append(new_port)

            elif segment.status.iloc[0] == 'inTransit':
                try:
                    timelapse_to_next_port = PathCalculations.timelapseAlongPath(data.bs_ts, start_index, end_index)
                    _, distance_to_next_port = PathCalculations.distanceAlongPath_nm(data.geometry, start_index, end_index)
                    #mean_sog = timelapse_to_next_port/distance_to_next_port
                except IndexError:
                    print(f"Warning: end_index {end_index} may be out of bounds, or there may be division by 0. Assigning default values for distance and timelapse.")
                    timelapse_to_next_port = None
                    distance_to_next_port = None
                    #mean_sog = None

                new_transit = {'segment_id' : segment_id,
                            'from_port' : segment.previous_port.iloc[0],
                            'to_port' : segment.next_port.iloc[0],
                            'start_index' : start_index,
                            'end_index' : end_index,
                            'distance_nm' : round(distance_to_next_port, 3),
                            'duration_hrs' : round(timelapse_to_next_port, 3),
                            'start_time' : segment.bs_ts.iloc[0],
                            'end_time' : segment.bs_ts.iloc[-1]}
                transit_data_list.append(new_transit)

            else:
                print('error in get_transit_distances')

        if len(port_data_list) > 0:
            ports = pd.concat([ports, pd.DataFrame(port_data_list)]).sort_values('segment_id').reset_index()
        if len(transit_data_list) > 0:
            transits = pd.concat([transits, pd.DataFrame(transit_data_list)]).sort_values('segment_id').reset_index()

        return ports, transits
            
            


