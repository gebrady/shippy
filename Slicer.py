import pandas as pd
import pytz

class Slicer():
    def __init__(self, cruise_data):
        self.cruise = cruise_data
        self.thinned = None

    ####### SORT AND CONVERT TIME STAMPS ######

    @staticmethod
    def orderGroupByTime(group):
        """Sorst the input group chronologically (timestamps) and returns the group 
           in the new order with AKDT timestamps.
        """
        group['bs_ts'] = pd.to_datetime(group['bs_ts'], utc = True).dt.tz_convert(pytz.timezone('US/Alaska'))
        group.sort_values(by='bs_ts', inplace=True)
        return group.reset_index(drop=True)
    
    ####### WRANGLING #######

    def subset(self, start_index, end_index):
        """returns a subset of the geodataframe
        """
        print(f'start_index: {start_index}, end_index: {end_index}')
        return self.cruise.data.iloc[start_index:end_index]

    def subsetCruiseByIndex(start_index, end_index):
        pass

    def subsetCruiseByPort(start_port, end_port):
        pass

    def subsetIndexToNextPort(start_index):
        pass

    ####### AGGREGATION #######
    def thinCruiseData(self, n): # Resample data to every n entries
        """Resamples data for quick looks
        """
        if not self.thinned:
            self.thinned = self.cruise.data.iloc[::n]
  








    ########## SCRATCH AREA #########
    def getPortAfterGlacierBay(self):
        if self.visitsGlacierBay():
            first_index_outside_GLBA = self.fillPointsWithinGlacierBay()
            next_port = self.getNextPort(first_index_outside_GLBA)
            if next_port is not None:
                return next_port


    