import geopandas as gpd
from geopy.distance import distance
from shapely.geometry import Point, LineString
from geopy.distance import geodesic

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

