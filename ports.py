# Main application class
import os
from ship import *
from app import *

import geopandas as gpd
from geopy.distance import distance
from shapely.geometry import Point, LineString
#from analyst import *

a = App(r'/Users/Graham/cruise/ais_data')

output_shp_folder = r'/Users/Graham/cruise/cruises_shp'

glba_boundary = r'/Users/Graham/cruise/shapes/GLBA_Exit.shp'

boundary = gpd.read_file(glba_boundary)

# ## CALCULATE PORTS OF CALL
# for boat_name, boat_data in a.boatsData.boatsDataDictionary.items():
#     glba_visit = 0
#     for cruise_id, cruise_data in boat_data.cruisesDataDictionary.items():
#         if cruise_data.visitsGlacierBay():
#             glba_visit += 1
#         #ports = cruise_data.listPorts()
#         #print(f'{cruise_id} went to the following ports: {ports}')
#     print(f'Boat: {boat_name} visited GLBA {glba_visit} times in 2023')

        # cruise_data.getPortsOfCall()
        # cruise_data.toPointShapefile(os.path.join(output_shp_folder, cruise_id + '.shp'))
        # ### Subset the GeoDataFrame by the boundary
        # cruise_data.clipBoundary(boundary)
        # cruise_data.gdf_clipped.to_file(os.path.join(r'/Users/Graham/cruise/clipped_cruises', cruise_id + '.shp'))

        # if cruise_id == 'CROWN PRINCESS_04':
        #    cruise_data.plotCruise()
        #    break
        


## READOUT
for boat_name, boat_data in a.boatsData.boatsDataDictionary.items():
    print(f"Boat: {boat_name}")
    for cruise_id, cruise_data in boat_data.cruisesDataDictionary.items():
        print(f"  Cruise ID: {cruise_id}")
        print(f"    {min(cruise_data.days).strftime('%Y/%m/%d')} - {max(cruise_data.days).strftime('%Y/%m/%d')}")
        print(f"       data points: {len(cruise_data.data)}")
        print(f"       ports of call: {cruise_data.listPorts()}")
        cruise_data.populatePortsColumn()
        print(f"       {cruise_data.displayItinerary()}")
        #print(cruise_data.gdf.port.value_counts())
        print()
        #print(f"       ports of call: {cruise_data.getItinerary()}")