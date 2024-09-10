import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

class Plotter:

    @staticmethod
    def plot_4a():
        # SHIP VISITS AND AVERAGE DISTANCE TO PORT CALLS ####
        attributed_claa_df_no2021 = attributed_claa_df[attributed_claa_df.year != 2021]
        df_grouped = attributed_claa_df_no2021.groupby('year').agg({
            'boatName': 'nunique',  # Count unique ships
            'distance_nm_mean': 'mean'   # Calculate average distance
        }).reset_index()

        plt.style.use('dark_background')

        fig, ax1 = plt.subplots(figsize=(10, 6))

        ax1.plot(df_grouped['year'], df_grouped['boatName'], color='cyan', label='Number of Ships', linewidth=2)
        ax1.scatter(df_grouped['year'], df_grouped['boatName'], color='cyan', edgecolor='white', zorder=5)  
        ax1.set_xlabel('Year', fontsize=14)
        ax1.set_ylabel('Number of Ships', color='cyan', fontsize=14)
        ax1.tick_params(axis='y', labelcolor='cyan')

        ax2 = ax1.twinx()
        ax2.plot(df_grouped['year'], df_grouped['distance_nm_mean'], color='magenta', label='Average Distance (nm)', linewidth=2, linestyle='--')
        ax2.scatter(df_grouped['year'], df_grouped['distance_nm_mean'], color='magenta', edgecolor='white', zorder=5)
        ax2.set_ylabel('Average Distance (nm)', color='magenta', fontsize=14)
        ax2.tick_params(axis='y', labelcolor='magenta')


        plt.title('Trends in Ship Arrivals and Average Distance (2008 - 2024)', fontsize=16, color='white')
        ax1.grid(False)  
        ax2.grid(False) 
        fig.legend(loc='lower left', bbox_to_anchor=(0.1, 0.13), fontsize=12) 

        plt.tight_layout()
        plt.show()

    def plot4b():
        # AVERAGE SOG AND DURATION TO NEXT PORTS ####
        attributed_claa_df['mean_sog'] = np.where(
            attributed_claa_df['duration_hrs_mean'] != 0, 
            attributed_claa_df['distance_nm_mean'] / attributed_claa_df['duration_hrs_mean'],
            np.nan  
        )

        df_grouped = attributed_claa_df.groupby('year').agg({
            'boatName': 'nunique',  # Count unique ships
            'mean_sog': 'mean',  # Calculate average distance
            'duration_hrs_mean' : 'mean'
        }).reset_index()

        plt.style.use('dark_background')

        fig, ax1 = plt.subplots(figsize=(10, 6))

        ax1.plot(df_grouped['year'], df_grouped['mean_sog'], color='green', label='Mean sog (kt)', linewidth=2)
        ax1.scatter(df_grouped['year'], df_grouped['mean_sog'], color='green', edgecolor='white', zorder=5) 
        ax1.set_xlabel('Year', fontsize=14)
        ax1.set_ylabel('Mean sog', color='green', fontsize=14)
        ax1.tick_params(axis='y', labelcolor='green')
        ax2 = ax1.twinx()
        ax2.plot(df_grouped['year'], df_grouped['duration_hrs_mean'], color='red', label='Average Duration (hrs)', linewidth=2, linestyle='--')
        ax2.scatter(df_grouped['year'], df_grouped['duration_hrs_mean'], color='red', edgecolor='white', zorder=5)
        ax2.set_ylabel('Average Duration (hrs)', color='red', fontsize=14)
        ax2.tick_params(axis='y', labelcolor='red')


        plt.title('Trends in Ship Arrivals and Average Distance (2008 - 2024)', fontsize=16, color='white')
        ax1.grid(False)
        ax2.grid(False)

        fig.legend(loc='lower left', bbox_to_anchor=(0.1, 0.13), fontsize=12) 

        plt.tight_layout()
        plt.show()

    def plot4c():
        port_counts = attributed_claa_df['portName'].value_counts()
        ports_over_5_visits = port_counts[port_counts > 5].index
        filtered_df = attributed_claa_df[attributed_claa_df['portName'].isin(ports_over_5_visits)]
        filtered_df = filtered_df[filtered_df['year'] != 2021]

        filtered = False

        if filtered:
            df_grouped_ports = filtered_df.groupby('year').agg({
                'portName': 'nunique'
            }).reset_index()
        else:
            df_grouped_ports = attributed_claa_df.groupby('year').agg({
                'portName': 'nunique'
            }).reset_index()
            

        df_grouped_ports.columns = ['year', 'unique_ports']

        plt.style.use('dark_background')  # Set dark mode
        plt.figure(figsize=(10, 6))
        plt.plot(df_grouped_ports['year'], df_grouped_ports['unique_ports'], color='yellow', label='Unique Port Calls > 5 Visits', linewidth=2, linestyle='--')
        plt.scatter(df_grouped_ports['year'], df_grouped_ports['unique_ports'], color='yellow', edgecolor='white', zorder=5)  # Adding points
        plt.xlabel('Year', fontsize=14)
        plt.ylabel('Unique Ports with > 5 Visits', color='yellow', fontsize=14)
        plt.tick_params(axis='y', labelcolor='yellow')
        plt.title('Unique Ports with More Than 5 Visits per Year (2008 - 2024)', fontsize=16, color='white')
        plt.grid(False)

        plt.tight_layout()
        plt.show()