import Kruise

from typing import List, Optional
import pandas as pd



class BoatDatuh:
    """Represents data associated with a single boat, including multiple cruises."""
    
    TIME_THRESHOLD = pd.timedelta(hours=1)  # Example threshold for time lapse

    def __init__(self, boat_name: str, cruises: Optional[List[Kruise]] = None):
        """
        Initialize a BoatData instance.

        Args:
            boat_name (str): The name of the boat.
            cruises (Optional[List[Cruise]]): List of cruises associated with the boat.
        """
        self.boat_name = boat_name
        self.cruises = cruises if cruises is not None else []

    def add_cruise(self, cruise: Kruise) -> None:
        """Add a new cruise to the list of cruises."""
        self.cruises.append(cruise)


class BoatsData:
    """Represents a collection of BoatData instances."""
    
    def __init__(self, boats: Optional[List[BoatDatuh]] = None):
        """
        Initialize a BoatsData instance.

        Args:
            boats (Optional[List[BoatData]]): List of BoatData instances.
        """
        self.boats = boats if boats is not None else []

    def add_boat_data(self, boat_data: BoatDatuh) -> None:
        """Add a BoatData instance to the collection."""
        self.boats.append(boat_data)


class CruiseSorter:
    """
    Handles operations related to sorting data into cruises, returning flattened cruises
    for a whole boat, and managing data import and triage.
    """

    TIMELAPSE_THRESHOLD = BoatDatuh.TIME_THRESHOLD

    def __init__(self, boat_data: BoatDatuh):
        """
        Initialize a CruiseSorter instance.

        Args:
            boat_data (BoatData): The BoatData instance to operate on.
        """
        self.boat_data = boat_data
        self.previous_cruise: Optional[Kruise] = None  # Placeholder for the last cruise edited
        self.current_group: Optional[pd.DataFrame] = None  # Placeholder for imported data

    @classmethod
    def is_matching_cruise(cls, unassigned_group: pd.DataFrame, cruise: Kruise) -> bool:
        """
        Determine if an unassigned group matches a given cruise based on a time threshold.

        Args:
            unassigned_group (pd.DataFrame): DataFrame representing the unassigned data group.
            cruise (Cruise): The cruise to compare against.

        Returns:
            bool: True if the unassigned group matches the cruise, False otherwise.
        """
        max_timestamp = cruise.data['bs_ts'].max()
        min_timestamp = unassigned_group['bs_ts'].min()

        if (min_timestamp - max_timestamp) <= cls.TIMELAPSE_THRESHOLD:
            return True
        return False

    def sort_data_into_cruises(self, new_data: pd.DataFrame) -> None:
        """
        Sort new data into existing cruises or create new cruises as needed.

        Args:
            new_data (pd.DataFrame): DataFrame containing the new data to be sorted.
        """
        for index, row in new_data.iterrows():
            matched = False
            for cruise in self.boat_data.cruises:
                if self.is_matching_cruise(pd.DataFrame([row]), cruise):
                    cruise.data = pd.concat([cruise.data, pd.DataFrame([row])])
                    matched = True
                    break
            if not matched:
                new_cruise = Kruise(pd.DataFrame([row]))
                self.boat_data.add_cruise(new_cruise)