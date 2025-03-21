from machine import Pin, I2C
from ssd1306 import SSD1306_I2C
import time

# Define OLED screen dimensions
oled_width = 128
oled_height = 64

# Current text row
current_y = 0

# Initialize I2C bus
i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)

# Initialize OLED object
oled = SSD1306_I2C(oled_width, oled_height, i2c)


# Main program loop
while True:
    # Request input, save input to variable
    value = input("Input a word: ")
    
    # Check if all rows are used
    if current_y < 56: # If not, go to next row
        current_y += 8
    else:              # If yes, scroll down
        oled.scroll(0, -8)
    
    oled.fill_rect(0, 56, 128, 63, 0) # Manually clear the lowest row since SSD1306 library copies the last row when scrolling leading to overwritten text.
    
    oled.text(value, 0, current_y, 1) # Print text on screen to current row
    oled.show() # Refresh display
    
    time.sleep(0.1)