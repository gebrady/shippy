from ship import *
from app import *

a = App(r'/Users/Graham/cruise/ais_data')

data = {}

for boat_name, boat_data in a.boatsData.boatsDataDictionary.items():
    print(f"Boat: {boat_name}")
    for cruise_id, cruise_data in boat_data.cruisesDataDictionary.items():
        if cruise_data.visitsGlacierBay():
            data[cruise_id] = cruise_data
            print(f"  Cruise ID: {cruise_id}")
            print(f"    {min(cruise_data.days).strftime('%Y/%m/%d')} - {max(cruise_data.days).strftime('%Y/%m/%d')}")
            print(f"       data points: {len(cruise_data.data)}")
        continue



                    
c = data['NORWEGIAN ENCORE_08']

#print(c.days)
c.dataToGeodata()

_, b = c.getDistanceAlongPath(40,400)
print(b)
#c.plotCruise()
