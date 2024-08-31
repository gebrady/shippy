import os
import pandas as pd

folder = r'/Users/Graham/cruise/ais_data'

count=0
for dirs, _, files in os.walk(folder):
    for f in sorted(files):
        if f.endswith('csv') and 'CAN' in f:
            count+=1
            file_path = os.path.join(dirs, f)
            rows = pd.read_csv(file_path)
            rows = rows[rows.name != 'EURODAM'] # REMOVE EURODAM DATA FROM THESE FILES
            rows.to_csv(os.path.join(folder,f.replace(' ','_')))