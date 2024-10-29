import requests
import xml.etree.ElementTree as ET


# API endpoint for the SOAP request
url = 'https://cgmix.uscg.mil/xml/PSIXData.asmx'

# Replace with your actual VesselID
vessel_id = '9188037'

# Create the SOAP request XML
soap_request = f'''<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <getVesselDimensions xmlns="https://cgmix.uscg.mil">
      <VesselID>{vessel_id}</VesselID>
    </getVesselDimensions>
  </soap:Body>
</soap:Envelope>'''

# Set the headers for the SOAP request
headers = {
    'Content-Type': 'text/xml; charset=utf-8',
    'SOAPAction': 'https://cgmix.uscg.mil/getVesselDimensions'
}

# Send the POST request
response = requests.post(url, data=soap_request, headers=headers)

# Check if the request was successful
if response.status_code == 200:
    print("Request successful!")
    print("Response XML:")
    print(response.text)

    # Parse the XML response
    root = ET.fromstring(response.text)
    # Find the namespace
    ns = {'soap': 'http://schemas.xmlsoap.org/soap/envelope/', 'xsi': 'http://www.w3.org/2001/XMLSchema-instance'}

    # Navigate to the 'getVesselDimensionsResult'
    result = root.find('.//getVesselDimensionsResult', ns)
    
    if result is not None:
        # Check for 'VesselDimensions' elements
        dimensions = result.findall('.//VesselDimensions')
        if dimensions:
            for dim in dimensions:
                vessel_id = dim.find('VesselId').text
                dimension_type_id = dim.find('DimensionTypeLookupId').text
                dimension_type_name = dim.find('DimensionTypeLookupName').text
                breadth = dim.find('BreadthInFeet').text
                depth = dim.find('DepthInFeet').text
                length = dim.find('LengthInFeet').text
                
                print(f"Vessel ID: {vessel_id}")
                print(f"Dimension Type ID: {dimension_type_id}")
                print(f"Dimension Type Name: {dimension_type_name}")
                print(f"Breadth in Feet: {breadth}")
                print(f"Depth in Feet: {depth}")
                print(f"Length in Feet: {length}")
        else:
            print("No vessel dimensions found for the given VesselID.")
    else:
        print("No results found in the response.")
else:
    print(f"Failed to retrieve data. Status code: {response.status_code}")
