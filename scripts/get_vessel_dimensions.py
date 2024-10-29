import requests
import xml.etree.ElementTree as ET

# API endpoint for getting vessel dimensions (replace with the correct endpoint)
url = 'https://cgmix.uscg.mil/xml/PSIXData.asmx/getVesselDimensions'

# Example parameters (you need to replace with the actual VesselID)
params = {
    'VesselID': 9751509,  # Replace with the actual VesselID you want to query
}

# Send the GET request
response = requests.get(url, params=params)

# Check if the request was successful
if response.status_code == 200:
    print("Request successful!")

    # Print the raw XML response to verify its contents
    print(response.text)  # This allows you to inspect the data

    # Parse the XML response
    root = ET.fromstring(response.content)

    # Extract and print vessel dimensions
    for dimension in root.findall('.//Dimension'):
        dimension_type = dimension.find('DimensionTypeLookupName').text
        breadth = dimension.find('BreadthInFeet').text
        depth = dimension.find('DepthInFeet').text
        length = dimension.find('LengthInFeet').text
        
        print(f'Dimension Type: {dimension_type}, '
              f'Breadth: {breadth} ft, '
              f'Depth: {depth} ft, '
              f'Length: {length} ft')
else:
    print(f"Failed to retrieve data. Status code: {response.status_code}")