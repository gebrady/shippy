################################################################

##### FORMATTING METHODS #####

def format_timestamp_range(timestamp_list):
    """Converts a list of timestamps to a string describing its range."""
    # Find the minimum and maximum timestamps
    lo = min(timestamp_list)
    hi = max(timestamp_list)
    
    # Format the datetime objects to 'MM/DD HHMM' format
    lo_str = lo.strftime('%-m/%-d %H:%M')
    hi_str = hi.strftime('%-m/%-d %H:%M')
    
    # Create the final formatted string
    formatted_str = f'{lo_str} - {hi_str}'
    
    return formatted_str

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