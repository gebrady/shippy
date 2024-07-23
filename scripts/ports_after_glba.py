from app import *

data_folder = r'/Users/Graham/cruise/ais_data'

a = App(data_folder)

cruises = {}

result = pd.DataFrame(columns=['port','cruise_id'])

big_line_gdf = gpd.GeoDataFrame()

for boat_name, boat_data in a.boatsData.boatsDataDictionary.items():
    print(f"Boat: {boat_name}")
    for cruise_id, cruise_data in boat_data.cruisesDataDictionary.items():
        print(f"  Cruise ID: {cruise_id}")
        print(f"    {min(cruise_data.days).strftime('%Y/%m/%d')} - {max(cruise_data.days).strftime('%Y/%m/%d')}")
        print(f"       data points: {len(cruise_data.data)}")
        if cruise_data.visitsGlacierBay():
            cruises[cruise_id] = cruise_data
            cruise_data.appendToLineShapefile(os.path.join('out_shp', 'cruises_subset_to_glba.shp'))

rows_to_append = []

for cruise_id, cruise_data in cruises.items():
    cruise_data.dataToGeodata()
    cruise_data.assignPorts()
    port = cruise_data.getPortAfterGlacierBay()

    # Create a dictionary for the new row
    new_row = {'port': port, 'cruise_id': cruise_id}
    rows_to_append.append(new_row)

# Append all new rows to the result DataFrame at once
result = pd.concat([result, pd.DataFrame(rows_to_append)], ignore_index=True)

print(result)
print(result.port.value_counts())

juneau_after = result[result.port == 'Juneau']

print(juneau_after.cruise_id)

for row in juneau_after.cruise_id:
    print(f"  Cruise ID: {row}")
    print(f"    {min(cruises[row].days).strftime('%Y/%m/%d')} - {max(cruises[row].days).strftime('%Y/%m/%d')}")




