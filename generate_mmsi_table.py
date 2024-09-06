import os
import pandas as pd

dataFolder = r'./data/ais_data'

mmsi_table = []
unique_mmsi_entries = set()  # Set to track unique mmsi entries

for dirs, _, files in os.walk(dataFolder):
    for f in sorted(files):
        if f.endswith('csv'):
            file_path = os.path.join(dirs, f)
            rows = pd.read_csv(file_path)  
            rows = rows.dropna(subset=['name'])
            
            grouped = rows.groupby(['mmsi', 'name'])
            for mmsi, data in grouped:
                #print(f'group is at {mmsi}')
                mmsi_table.append(mmsi)

print(f"Total unique mmsi entries: {len(unique_mmsi_entries)}")

mmsi_table = list(set(mmsi_table))

mmsi_table_df = pd.DataFrame(mmsi_table, columns=['mmsi', 'boatName'])
mmsi_table_df.to_csv('./data/mmsi_catalog.csv')

#print(mmsi_table_df.head)