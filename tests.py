#### TESTING #####

data_folder = r'/Users/Graham/cruise/ais_data'
test_folder = r'/Users/Graham/cruise/test_data'

isTest = False

a = App(test_folder) if isTest else App(data_folder)

sum_of_points = 0
for boat_name, boat_data in a.boatsData.boatsDataDictionary.items():
    print(f"Boat: {boat_name}")
    for cruise_id, cruise_data in boat_data.cruisesDataDictionary.items():
        print(f"  Cruise ID: {cruise_id}")
        print(f"    {min(cruise_data.days).strftime('%Y/%m/%d')} - {max(cruise_data.days).strftime('%Y/%m/%d')}")
        print(f"       data points: {len(cruise_data.data)}")
        sum_of_points += len(cruise_data.data)

print(f'Expected point count: {a.rowsParsedCount}, actual point count: {sum_of_points}, nan point count: {len(a.boatsData.nanData)}, condition is: {sum_of_points+len(a.boatsData.nanData) == a.rowsParsedCount}')

