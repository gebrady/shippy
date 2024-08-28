class Slicer():

    def __init__(self, cruise_data):
        self.cruise = cruise_data
        self.thinned = None

    def thinCruiseData(self, n): # Resample data to every n entries
        if not self.thinned:
            self.thinned = self.cruise.data.iloc[::n]
  
    
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

    def getPortAfterGlacierBay(self):
        if self.visitsGlacierBay():
            first_index_outside_GLBA = self.fillPointsWithinGlacierBay()
            next_port = self.getNextPort(first_index_outside_GLBA)
            if next_port is not None:
                return next_port


    