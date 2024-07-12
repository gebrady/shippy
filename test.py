import pandas as pd

def format_timestamp_range2(timestamps):
    # Extract the dates from the timestamps
    dates = [ts.date() for ts in timestamps]

    # Get the unique dates
    unique_dates = list(set(dates))

    # Sort the unique dates
    unique_dates.sort()

    # Format the dates to month/day
    formatted_dates = [date.strftime('%m/%d') for date in unique_dates]

    return formatted_dates

# Example usage
timestamps = [
    pd.Timestamp('2023-07-01 08:00:00'),
    pd.Timestamp('2023-07-02 09:00:00'),
    pd.Timestamp('2023-07-03 10:00:00'),
    pd.Timestamp('2023-07-04 11:00:00'),
    pd.Timestamp('2023-07-01 12:00:00')  # Adding a duplicate date for demonstration
]

formatted_dates = format_timestamp_range2(timestamps)
print(formatted_dates)
