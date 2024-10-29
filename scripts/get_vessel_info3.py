import requests
import xml.etree.ElementTree as ET

# Correct endpoint for vessel info
url = 'https://cgmix.uscg.mil/xml/PSIXData.asmx/GetVesselInfo'

# Example parameters (like VesselID)
params = {
    'VesselID': '9751509',  # Replace with actual VesselID
}

# Send GET request
response = requests.get(url, params=params)

# Check response status
if response.status_code == 200:
    print("Request successful!")
    
    # Print the raw XML response to verify it contains vessel info
    print(response.text)  # Verify the data contains vessel info
    
    # Parse the XML and extract desired vessel info
    root = ET.fromstring(response.content)
    
    # Example of extracting and printing vessel details
    for vessel in root.findall('.//Vessel'):
        name = vessel.find('VesselName').text
        vessel_id = vessel.find('VesselID').text
        print(f'Vessel Name: {name}, Vessel ID: {vessel_id}')
else:
    print(f"Failed to retrieve data. Status code: {response.status_code}")