from machine import Pin, I2C
from ssd1306 import SSD1306_I2C
import time

# Define OLED screen dimensions
oled_width = 128
oled_height = 64

# Configure UFO
ufo_x_position = 0
ufo_speed = 4

# Initialize switches
sw0 = Pin("GP9", Pin.IN, Pin.PULL_UP)
sw2 = Pin("GP7", Pin.IN, Pin.PULL_UP)

# Initialize I2C bus
i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)

# Initialize OLED object
oled = SSD1306_I2C(oled_width, oled_height, i2c)


# Main program
while True:
    if sw0() == 0: # Switch 0 moves UFO to the right
        ufo_x_position += ufo_speed
        
    elif sw2() == 0: # Switch 2 moves UFO to the left
        ufo_x_position -= ufo_speed
    
    # Check if UFO goes out of bounds
    if ufo_x_position > 104:
        ufo_x_position = 104 # Move UFO back
    elif ufo_x_position < 0:
        ufo_x_position = 0 # Move UFO back
    
    oled.fill(0) # Clear screen
    oled.text("<=>", ufo_x_position, 56, 1) # Draw UFO at current saved coordinates
    oled.show() # Update screen
    
    # I like my programs fast so no sleep