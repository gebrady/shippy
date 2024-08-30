class Segments:
    """Doubly linked list to store Nodes of AIS data. Node is either inPort or inTransit. Used when ordering data into Cruise structures"""
    def __init__(self):
        self.head = None
        self.tail = None

    def extract_glba_segments(self): # WORK FLOW TO IMPORT THAN EXTRACT POINTS WITHIN GLBA AND AT PORT AFTERWARD
        glba_subset = Segments()

        current = self.head
        while current:
            if current.visitsGlacierBay():
                glba_subset.add_node(current.data, current.segmentID) # at transit segment that enters GLBA
                glba_subset.add_node(current.next.data, current.next.segmentID) # within port after GLBA (next segment with state change expected)
            #print(current.data)
            current = current.next
        
        return glba_subset

    ###### UTILITY METHODS ######

    def add_node(self, rows, segment_id):
        """adds a new SegmentNode to the end of the row
           assigns segment_id to that SegmentNode's attributes.
        """
        new_node = SegmentNode(rows, segment_id)
        if self.tail is None: # if Segments is empty
            self.head = self.tail = new_node
        else:
            self.tail.next = new_node
            new_node.prev = self.tail
            self.tail = new_node

    def insert_node_after(self, segmentID, rows):
        """insets new rows after the existing SegmentNode matching segmentID. traverses the DLL to find the match"""
        current = self.head
        while current:
            if current.segmentID == segmentID:
                new_node = SegmentNode(rows, prev = current, next = current.next)
                if current.next: # if not the end of DLL
                    current.next.prev = new_node # put the rows behind row after match
                else:
                    self.tail = new_node # otherwise make end of list new rows
                current.next = new_node # make node after match new rows
                return
            current = current.next # traverse to next element
        print('no match found')

    def remove_segment(self, segmentID):
        """Remove a segment with specified data."""
        current = self.head
        while current:
            if current.data == segmentID:
                if current.prev:
                    current.prev.next = current.next
                else:
                    self.head = current.next
                if current.next:
                    current.next.prev = current.prev
                else:
                    self.tail = current.prev
                return
            current = current.next
        print("no match found to remove")

    def traverse_list(self):
        """Print all segments in the list."""
        current = self.head
        while current:
            print(current.data)
            current = current.next

