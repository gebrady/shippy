from ship import *
from app import *

a = App(r'/Users/Graham/cruise/ais_data')

data = {}

for boat_name, boat_data in a.boatsData.boatsDataDictionary.items():
    #print(f"Boat: {boat_name}")
    for cruise_id, cruise_data in boat_data.cruisesDataDictionary.items():
        #print(f"  Cruise ID: {cruise_id}")
        #print(f"    {min(cruise_data.days).strftime('%Y/%m/%d')} - {max(cruise_data.days).strftime('%Y/%m/%d')}")
        #print(f"       data points: {len(cruise_data.data)}")
        if cruise_data.visitsGlacierBay():
            data[cruise_id] = cruise_data

print(len(data))
# c = data['NORWEGIAN ENCORE_08']

# #print(c.days)
# c.dataToGeodata()
# c.populatePortsColumn()

# print(c.data.head())

# print(c.data.nav_status)

# test = c.gdf

# test = test[test['sog'] <= .5]
# print(test)

# test = c.gdf

# test = test[test['nav_status'] != 'Under way using engine']
# print(test[['sog', 'port', 'lat', 'lon', 'nav_status']])

# print(test['sog'].value_counts())
# print(test['nav_status'].value_counts())
# print(test['port'].value_counts())

# print(c.gdf['port'].value_counts())


#print(c.gdf[c.gdf[c.gdf.sog < 3]])
# _, b = PathCalculations.distanceAlongPath(c.gdf.geometry, 40,400)
# print(b)
# print(c.displayItinerary())
# #c.plotCruise()