class Kruise():
    """Represents a cruise with its associated data."""
    
    def __init__(self, data: pd.DataFrame):
        """
        Initialize a Cruise instance.

        Args:
            data (pd.DataFrame): DataFrame containing cruise data.
        """
        self.data = data