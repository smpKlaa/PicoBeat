from machine import Pin, ADC
from fifo import Fifo
import time

"""peripherals library simplifies the use of a few third party devices on the
raspberry pi pico.
"""

class RotaryEncoder:
    """
    RotaryEncoder class is used to interface a rotary encoder. The class has an
    internal fifo that can be interfaced with the methods of the class.
    
    PARAMS:
    rot_a(int): GPIO pin of the rotary encoders a pin.
    rot_b(int): GPIO pin of the rotary encoders b pin.
    flip(bool: False):  Boolean for flipping the direction of the rotary encoder.
    scroll_speed(int): How many actions before scroll event happens. Bigger is slower.
    """
    def __init__(self, rot_a, rot_b, flip=None, scroll_speed=None):
        self.scroll_direction = 1		# Scrolling direction
        if flip:
            # If flip is true, scrolling direction is reversed
            self.scroll_direction = -1
        
        if not scroll_speed:
            scroll_speed = 1 
#         if not rot_a:
#             rot_a = 10
#         if not rot_b:
#             rot_b = 11
          
        self.a = Pin(rot_a, mode = Pin.IN)
        self.b = Pin(rot_b, mode = Pin.IN)
        self._i = 0
        self.scroll_speed = scroll_speed
        self.fifo = Fifo(30, typecode = 'i')
        self.a.irq(handler = self.handler, trigger = Pin.IRQ_RISING, hard = True)
        
    def handler(self, pin):
        if self.b():
            self._i += -self.scroll_direction
        else:
            self._i += self.scroll_direction
        
        if self._i >= self.scroll_speed:
            self.fifo.put(1)
            self._i = 0
        elif self._i <= -self.scroll_speed:
            self.fifo.put(-1)
            self._i = 0
            
    def get(self):
        if self.fifo.has_data():
            return self.fifo.get()


class IRS_ADC:
    """
    IRS_ADC class for siplifying the use of ADC devices with continuous
    data streams. IRS_ADC has it's internal fifo list that can be interfaced
    with the class.
    
    PARAMS:
    adc_pin_nr(int): GPIO pin of the ADC device.
    """
    def __init__(self, adc_pin_nr):
        self.av = ADC(adc_pin_nr) 		# Sensor ADC channel
        self.fifo = Fifo(50) 			# Interval fifo where samples are stored
        
    def handler(self, tid):
        self.fifo.put(self.av.read_u16())
        
    def get(self):
        """get just calls the internal fifo's method."""
        return self.fifo.get()
    
    def has_data(self):
        """has_data just calls the internal fifo's method."""
        return self.fifo.has_data()