# Main application class
from ship import *
from analyst import *

class App:
    def __init__(self, dataFolder):
        self.boatsData = BoatsData()  # Initialize BoatsData instance
        self.rowsParsedCount = 0
        self.populateBoatsData(dataFolder)  # Populate boatsData with data from CSV files
        self.analyst = Analyst(self.boatsData)

    def __str__(self):
        return str(self.boatsData)  # String representation of boatsData
    
    def populateBoatsData(self, dataFolder):
        tik = time.perf_counter()
        count=0
        for dirs, _, files in os.walk(dataFolder):
            for f in sorted(files):
                if f.endswith('csv'):
                    count+=1
                    file_path = os.path.join(dirs, f)
                    rows = pd.read_csv(file_path)  # Read CSV file into DataFrame
                    print(f'Starting parsing file: {f}')
                    self.boatsData.parseRows(rows)  # Parse rows into boatsData
                    self.rowsParsedCount += len(rows)
                    print(f'Finished parsing file: {f}')
                
        tok = time.perf_counter()
        print(f"Imported data from {count} files in {tok - tik:0.4f} seconds")

    def run_analysis(self):
        self.analysis.plot_data()
        self.analysis.load_data_to_qgis(r'/Users/Graham/cruise/shapes')


##### TESTING #####

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

#a.run_analysis()

