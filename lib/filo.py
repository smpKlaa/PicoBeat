import array


class Filo:
    """First in last out, fixed size array that writes over itself."""
    def __init__(self, size, typecode = 'H'):
        """Parameters

        size (int): filo size. The maximum number of items stored is one less than the given size
        typecode (char): Type of data stored in filo. (Default is 'H' - unsigned short)
        """        
        self.data = array.array(typecode)
        for i in range(size):
            self.data.append(0)
        self.head = 0
        self.size = size
        self.dc = 0
        
    def put(self, value):
        """Put one item into the filo."""
        nh = (self.head + 1) % self.size
        self.data[self.head] = value
        self.head = nh
        """Dropped count probably not needed."""
        self.dc = self.dc + 1
            
    def get(self, index = None):
        """Get one item from the filo. If the filo is empty raises an exception."""
        """Parameters
        
        index (int): index of the value retreived. If not provided default to last item
        """
        if index == None:
            index = (self.head + 1) % self.size
        
        val = self.data[index]
        if self.empty():
            raise RuntimeError("Filo is empty")
        return val
    
    def dropped(self):
        """Return number of dropped items. A return value that is greater than zero means that filo is emptied too slowly.""" 
        return self.dc

    def has_data(self):
        """Returns True if there is data in the filo"""
        return self.data[self.head - 1] != None
                
    def empty(self):
        """Returns True if the filo is empty"""
        return self.data[self.head - 1] == None

