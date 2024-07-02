from app import *
from ship import *

class CruiseAnalyzer():
    """Holds brain for answering research questions about GLBA Cruising"""
    def __init__(self, dataFolder):
        self.boatsDataEngine = App(dataFolder)