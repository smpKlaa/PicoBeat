class RollingAverage:
    """For keeping track of rolling average of continuous data stream"""
    def __init__(self, size):
        """Parameters

        size (int): Size of the buffer for calculating the average.
        """
        self.size = size
        self.buffer = [0] * size
        self.index = 0
        self.sum = 0
        self.count = 0

    def update(self, new_value):
        """Update function to push/overwrite a new value into the buffer."""
        old_value = self.buffer[self.index]
        self.sum = self.sum - old_value + new_value
        self.buffer[self.index] = new_value
        self.index = (self.index + 1) % self.size
        self.count = min(self.count + 1, self.size)
        return self.sum / self.count
    
    def get(self):
        """Return the current average."""
        return self.sum / self.count