import pandas as pd
import matplotlib.pyplot as plt

# Load the data
path = r'./calendar/allyears_allports_claa.csv'

df = pd.read_csv(path)

df = df[df.portName == 'GLACIER BAY']

# Convert date column to datetime
df['date'] = pd.to_datetime(df['date'])

# Count total occurrences of each location
total_counts = df['nextPort'].value_counts()

# Get the top 5 locations
top_locations = total_counts.head(10).index

# Filter the DataFrame to include only rows with top 5 locations
filtered_df = df[df['nextPort'].isin(top_locations)]
filtered_df = df[df['nextPort'].isin(['HAINES', 'ICY STRAIT POINT', 'JUNEAU', 'SKAGWAY', 'KETCHIKAN', 'WRANGELL', 'SITKA'])]


# Set 'date' as the index for resampling
filtered_df.set_index('date', inplace=True)

# Resample data by week and count occurrences
weekly_counts = filtered_df.groupby('nextPort').resample('Y').size().unstack(fill_value=0)

# Transpose the DataFrame to have time on the x-axis and port names on the y-axis
weekly_counts = weekly_counts.T

# Plot the change in frequency for each portName over time
weekly_counts.plot(kind='line', linestyle='-', marker='', linewidth=2)
plt.title('Change in Frequency of Top 5 Ports After GLBA Over Time')
plt.xlabel('Date')
plt.ylabel('Frequency Per Year')
plt.legend(title='Next Port')
plt.grid(True)
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

