# Custom class representing AIS functionality

import os
import secrets
import time
import matplotlib.pyplot as plt
from datetime import datetime
from pathcalculations import *
import pytz

class AIS():

    def __repr__(self):
        return 'AIS: Testing worked'