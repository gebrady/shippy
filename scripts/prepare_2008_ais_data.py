import os
import pandas as pd
from pathlib import Path

# Define the directory containing the CSVs
input_folder = r'data/ignored_data/aux_ais_data/2008_ais'
output_folder = r'data/ais_data/2008_ais'

# Define a dictionary for renaming columns
rename_mapping = {
    'Base station time stamp': 'bs_ts',
    'Ship name': 'name',
    'MMSI' : 'mmsi',
    'Latitude': 'lat',
    'Longitude': 'lon',
    'Navigational status': 'nav_status',
    'Course over ground': 'cog',
    'Speed over ground': 'sog',
    'Heading' : 'heading',
    'IMO': 'imo',
    'Callsign' : 'callsign',
    'Destination': 'destination'
}

# Create the output folder if it doesn't exist
Path(output_folder).mkdir(parents=True, exist_ok=True)

# Recursively find all CSV files in the input directory
for subdir, _, files in os.walk(input_folder):
    for file in files:
        if file.endswith('.csv'):
            print(f'processing {file}')
            file_path = os.path.join(subdir, file)

            # Load the CSV file into a DataFrame
            df = pd.read_csv(file_path)

            # Rename columns using the mapping
            df.rename(columns=rename_mapping, inplace=True)

            # Generate a new unique filename based on the original path
            new_filename = os.path.basename(subdir) + '_' + file

            # Ensure no duplicates in the new directory by adding a suffix if needed
            unique_output_path = os.path.join(output_folder, new_filename)
            counter = 1
            while os.path.exists(unique_output_path):
                unique_output_path = os.path.join(output_folder, f"{os.path.basename(subdir)}_{counter}_{file}")
                counter += 1

            # Save the modified CSV to the output folder
            df.to_csv(unique_output_path, index=False)

print("CSV processing and renaming completed.")