from App import *

import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
import matplotlib.cm as cm
import numpy as np

# Using the App read method #

data_folder = r'/Users/Graham/cruise/data/examples'  # Replace with the path to your data folder

a = App(data_folder)
# Access the parsed data
print(a)

# You can also access specific parts of the data directly
for boat_name, boat_data in a.boatsData.boatsDataDictionary.items():
    print(f"Boat: {boat_name}")
    for cruise_id, cruise_data in boat_data.cruisesDataDictionary.items():
        print(f"  Cruise ID: {cruise_id}")
        print(f"  Data:\n{cruise_data.data}")


# Example point data
data = [
    {"name": "Location 1", "latitude": 58.3556, "longitude": -136.6626},
    {"name": "Location 2", "latitude": 59.0469, "longitude": -135.3359},
    {"name": "Location 3", "latitude": 58.3019, "longitude": -134.4197},
    {"name": "Location 4", "latitude": 58.4550, "longitude": -135.8970},
]

# Color map for different names
names = [point['name'] for point in data]
unique_names = list(set(names))
colors = cm.rainbow(np.linspace(0, 1, len(unique_names)))
name_color_map = dict(zip(unique_names, colors))

# Create a map
fig, ax = plt.subplots(figsize=(10, 7))
m = Basemap(projection='aea', lat_1=55, lat_2=65, lon_0=-140, lat_0=58, width=1.5e6, height=1.5e6, ax=ax)

# Draw coastlines and country boundaries
m.drawcoastlines()
m.drawcountries()

# Plot the points with color coding
for point in data:
    x, y = m(point['longitude'], point['latitude'])
    color = name_color_map[point['name']]
    m.plot(x, y, 'o', markersize=8, color=color, label=point['name'] if point['name'] not in plt.gca().get_legend_handles_labels()[1] else "")

# Create legend
handles, labels = ax.get_legend_handles_labels()
ax.legend(handles, labels, loc='best', title="Locations")

# Show the map
plt.title('Point Data on Map (Alaska Albers Projection)')
plt.show()
