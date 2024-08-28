import cProfile
import pstats

from ship import *
from app import *

def profile_code():
    a = App(r'/Users/Graham/cruise/ais_data')

if __name__ == "__main__":
    profiler = cProfile.Profile()
    profiler.enable()
    profile_code()
    profiler.disable()
    stats = pstats.Stats(profiler).sort_stats(pstats.SortKey.TIME)
    stats.print_stats()
    with open('profiling_results.txt', 'w') as f:
        stats = pstats.Stats(profiler, stream=f).sort_stats(pstats.SortKey.TIME)
        stats.print_stats()