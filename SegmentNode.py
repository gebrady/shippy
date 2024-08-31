from PortManager import PortManager

class SegmentNode:
    def __init__(self, data, segmentID = None, prev = None, next = None):
        self.data = data # gpd.GeoDataFrame type
        self.segmentID = segmentID
        self.prev = prev
        self.next = next

    def visitsGlacierBay(self):
        return any(self.data.intersects(PortManager.GLBA_BOUNDARY.unary_union))
     
    