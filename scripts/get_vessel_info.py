import requests

url = "https://cgmix.uscg.mil/xml/PSIXData.asmx"
headers = {
    'Content-Type': 'text/xml; charset=utf-8',
    'SOAPAction': 'https://cgmix.uscg.mil/xml/GetVesselInformation'
}
body = '''<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
               xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
               xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <GetVesselInformation xmlns="https://cgmix.uscg.mil/xml/">
      <VesselID>9751509</VesselID>  <!-- Replace with actual vessel ID -->
    </GetVesselInformation>
  </soap:Body>
</soap:Envelope>'''

response = requests.post(url, data=body, headers=headers)
print(response.text)