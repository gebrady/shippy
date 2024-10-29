from zeep import Client

wsdl = 'https://cgmix.uscg.mil/xml/PSIXData.asmx?WSDL'
client = Client(wsdl=wsdl)

response = client.service.GetVesselInformation(VesselID='9751509')
print(response)