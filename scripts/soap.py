import requests

# API endpoint for the SOAP request
url = 'https://cgmix.uscg.mil/XML/PSIXData.asmx'

# Create the SOAP request XML
vessel_id = 9293399  # Replace with your actual VesselID
soap_request = f'''<?xml version="1.0" encoding="utf-8"?>
<soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
                  xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
                  xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
  <soap12:Body>
    <getVesselCases xmlns="https://cgmix.uscg.mil">
      <VesselID>{vessel_id}</VesselID>
    </getVesselCases>
  </soap12:Body>
</soap12:Envelope>'''

# Set the headers for the SOAP request
headers = {
    'Content-Type': 'application/soap+xml; charset=utf-8',
    'SOAPAction': 'https://cgmix.uscg.mil/getVesselCases'
}

# Send the POST request
response = requests.post(url, data=soap_request, headers=headers)

# Check if the request was successful
if response.status_code == 200:
    print("Request successful!")
    print("Response XML:")
    print(response.text)
else:
    print(f"Failed to retrieve data. Status code: {response.status_code}")
    print("Response text:", response.text)