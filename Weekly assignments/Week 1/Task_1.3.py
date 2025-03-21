from machine import Pin, I2C
from ssd1306 import SSD1306_I2C
import time

# Define OLED screen dimensions
oled_width = 128
oled_height = 64

# Current "Pen" Y position
current_y = 32


# Initialize switches
sw0 = Pin("GP9", Pin.IN, Pin.PULL_UP)
sw1 = Pin("GP8", Pin.IN, Pin.PULL_UP)
sw2 = Pin("GP7", Pin.IN, Pin.PULL_UP)

# Initialize I2C bus
i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)

# Initialize OLED object
oled = SSD1306_I2C(oled_width, oled_height, i2c)


# Main program loop
while True:
    # Go through every pixel in X axis
    for current_x in range(0, 127): 
        oled.pixel(current_x, current_y, 1) # Light up a pixel
        
        # Move "Pen" up or down with switch 1 and 2
        if sw0() == 0:
            current_y += 1
        if sw2() == 0:
            current_y -= 1
        
        # Switch 1 clears the screen and resets the "Pen"
        if sw1() == 0:
            current_y = 32
            oled.fill(0)
            break # Stop for loop so drawing continues from the left
        
        oled.show() # Refresh screen