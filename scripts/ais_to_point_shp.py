a = App(r'./ais_data')

cruises_shp_filepath = r'./cruises_shp/processed_cruises.shp'

# After data install, iterate through all data, subselect cruises that visit GLBA, write as features to shapefile
count_total = 0
count_glba = 0
for boat_name, boat_data in a.boatsData.boatsDataDictionary.items():
            for cruise_id, cruise_data in boat_data.cruisesDataDictionary.items():
                count_total += 1
                if cruise_data.visitsGlacierBay():
                    count_glba += 1
                    cruise_data.dataToGeodata()
                    cruise_data.assignPorts()
                    cruise_data.boatName = boat_name
                    start_index = cruise_data.fillPointsWithinGlacierBay()
                    port_after_glba = cruise_data.getPortAfterGlacierBay()
                    #cruise_data.sub = cruise_data.subset(first_index, last_index)
                    cruise_data.appendToPointShapefile(cruises_shp_filepath)
                    print(f'Added {cruise_data.cruiseID}')

