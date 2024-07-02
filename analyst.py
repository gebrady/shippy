import matplotlib.pyplot as plt
from qgis.core import QgsApplication, QgsProject, QgsVectorLayer

class Analysis:
    def __init__(self, boatsData):
        self.boatsData = boatsData
        self.qgs = QgsApplication([], False)
        self.qgs.initQgis()

    def __del__(self):
        self.qgs.exitQgis()

    def plot_data(self):
        for boat_name, boat_data in self.boatsData.boatsDataDictionary.items():
            for cruise_id, cruise_data in boat_data.cruisesDataDictionary.items():
                plt.figure(figsize=(10, 6))
                plt.plot(cruise_data.data['bs_ts'], cruise_data.data['lat'], label='Latitude')
                plt.plot(cruise_data.data['bs_ts'], cruise_data.data['lon'], label='Longitude')
                plt.title(f"Boat: {boat_name}, Cruise: {cruise_id}")
                plt.xlabel('Timestamp')
                plt.ylabel('Coordinates')
                plt.legend()
                plt.show()

    def load_data_to_qgis(self, data_folder):
        project = QgsProject.instance()
        for dirs, _, files in os.walk(data_folder):
            for f in sorted(files):
                if f.endswith('shp'):
                    layer_path = os.path.join(dirs, f)
                    layer_name = os.path.splitext(f)[0]
                    layer = QgsVectorLayer(layer_path, layer_name, "ogr")
                    if not layer.isValid():
                        print(f"Layer {layer_name} failed to load!")
                    else:
                        project.addMapLayer(layer)
