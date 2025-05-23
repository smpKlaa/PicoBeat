from machine import Pin, I2C
import ssd1306
import time

i2c = I2C(1, sda=Pin(14), scl=Pin(15), freq=400000)
oled = ssd1306.SSD1306_I2C(128, 64, i2c)

# --- Bitmap Font Definitions (Each character/shape is 16x16 pixels) ---

# Each character bitmap is made of 16 rows, with two bytes per row = 16x16 pixels
# These represent custom font bitmaps for spelling "PICBEAT" with a heart in the middle

P_bitmap = [
    0b11111111, 0b00000000,
    0b11111111, 0b10000000,
    0b11100001, 0b11000000,
    0b11100000, 0b11000000,
    0b11100000, 0b11000000,
    0b11100001, 0b11000000,
    0b11111111, 0b10000000,
    0b11111111, 0b00000000,
    0b11100000, 0b00000000,
    0b11100000, 0b00000000,
    0b11100000, 0b00000000,
    0b11100000, 0b00000000,
    0b11100000, 0b00000000,
    0b00000000, 0b00000000,
    0b00000000, 0b00000000,
    0b00000000, 0b00000000,
]

I_bitmap = [
    0b11111111, 0b10000000,
    0b11111111, 0b10000000,
    0b00011000, 0b00000000,
    0b00011000, 0b00000000,
    0b00011000, 0b00000000,
    0b00011000, 0b00000000,
    0b00011000, 0b00000000,
    0b00011000, 0b00000000,
    0b00011000, 0b00000000,
    0b00011000, 0b00000000,
    0b00011000, 0b00000000,
    0b00011000, 0b00000000,
    0b11111111, 0b10000000,
    0b11111111, 0b10000000,
    0b00000000, 0b00000000,
    0b00000000, 0b00000000,
]

C_bitmap = [
    0b00111111, 0b11000000,
    0b01111111, 0b11100000,
    0b11110000, 0b11110000,
    0b11100000, 0b01110000,
    0b11100000, 0b00000000,
    0b11100000, 0b00000000,
    0b11100000, 0b00000000,
    0b11100000, 0b00000000,
    0b11100000, 0b00000000,
    0b11100000, 0b00000000,
    0b11100000, 0b01110000,
    0b11110000, 0b11110000,
    0b01111111, 0b11100000,
    0b00111111, 0b11000000,
    0b00000000, 0b00000000,
    0b00000000, 0b00000000,
]

B_bitmap = [
    0b11111111, 0b00000000,
    0b11111111, 0b10000000,
    0b11100001, 0b11000000,
    0b11100000, 0b11000000,
    0b11100001, 0b11000000,
    0b11111111, 0b10000000,
    0b11111111, 0b11000000,
    0b11100000, 0b11100000,
    0b11100000, 0b01100000,
    0b11100000, 0b01100000,
    0b11100000, 0b11100000,
    0b11111111, 0b11000000,
    0b11111111, 0b10000000,
    0b00000000, 0b00000000,
    0b00000000, 0b00000000,
    0b00000000, 0b00000000,
]

E_bitmap = [
    0b11111111, 0b11100000,
    0b11111111, 0b11100000,
    0b11100000, 0b00000000,
    0b11100000, 0b00000000,
    0b11100000, 0b00000000,
    0b11111111, 0b11000000,
    0b11111111, 0b11000000,
    0b11100000, 0b00000000,
    0b11100000, 0b00000000,
    0b11100000, 0b00000000,
    0b11100000, 0b00000000,
    0b11111111, 0b11100000,
    0b11111111, 0b11100000,
    0b00000000, 0b00000000,
    0b00000000, 0b00000000,
    0b00000000, 0b00000000,
]

A_bitmap = [
    0b00001111, 0b00000000,
    0b00011111, 0b10000000,
    0b00111101, 0b11000000,
    0b00111000, 0b11000000,
    0b01110000, 0b11100000,
    0b01110000, 0b11100000,
    0b01111111, 0b11100000,
    0b01111111, 0b11100000,
    0b11100000, 0b01110000,
    0b11100000, 0b01110000,
    0b11100000, 0b01110000,
    0b11100000, 0b01110000,
    0b11100000, 0b01110000,
    0b00000000, 0b00000000,
    0b00000000, 0b00000000,
    0b00000000, 0b00000000,
]

T_bitmap = [
    0b11111111, 0b11110000,
    0b11111111, 0b11110000,
    0b00000110, 0b00000000,
    0b00000110, 0b00000000,
    0b00000110, 0b00000000,
    0b00000110, 0b00000000,
    0b00000110, 0b00000000,
    0b00000110, 0b00000000,
    0b00000110, 0b00000000,
    0b00000110, 0b00000000,
    0b00000110, 0b00000000,
    0b00000110, 0b00000000,
    0b00000110, 0b00000000,
    0b00000000, 0b00000000,
    0b00000000, 0b00000000,
    0b00000000, 0b00000000,
]

# Heart bitmap (16x16, stored as two 8-bit values per row)
heart_bitmap = [
    0b00011000, 0b01100000,
    0b00111100, 0b11110000,
    0b01111111, 0b11111000,
    0b11111111, 0b11111100,
    0b11111111, 0b11111100,
    0b11111111, 0b11111100,
    0b01111111, 0b11111000,
    0b00111111, 0b11110000,
    0b00011111, 0b11100000,
    0b00001111, 0b11000000,
    0b00000111, 0b10000000,
    0b00000011, 0b00000000,
    0b00000000, 0b00000000,
    0b00000000, 0b00000000,
    0b00000000, 0b00000000,
    0b00000000, 0b00000000,
]

# Smaller 8x8 pixel heart for pulsing animation
small_heart_bitmap = [
    0b01100110,
    0b11111111,
    0b11111111,
    0b11111111,
    0b01111110,
    0b00111100,
    0b00011000,
    0b00000000,
]
# --- Bitmap Drawing Functions ---

#   Draws a 16x16 bitmap starting at (x, y).
def draw_bitmap(x, y, bitmap):
    for row in range(16):
        byte1 = bitmap[row * 2]
        byte2 = bitmap[row * 2 + 1]
        combined_row = (byte1 << 8) | byte2
         # Merge into one 16-bit row
        for col in range(16):
            if (combined_row >> (15 - col)) & 1:
                oled.pixel(x + col, y + row, 1)
                 # Check each bit, turn on pixel if bit is 1

#  Draws a 16x16 heart bitmap at position (x, y).
def draw_heart(x, y):
    for row in range(16):
        byte1 = heart_bitmap[row * 2]
        byte2 = heart_bitmap[row * 2 + 1]
        combined_row = (byte1 << 8) | byte2
        for col in range(16):
            if (combined_row >> (15 - col)) & 1:
                oled.pixel(x + col, y + row, 1)

#  Draws an 8x8 heart at (x, y) for pulse effect.
def draw_small_heart(x, y):
    for row in range(8):
        byte = small_heart_bitmap[row]
        for col in range(8):
            if (byte >> (7 - col)) & 1:
                oled.pixel(x + col, y + row, 1)

# Position where the heart icon is drawn in the splash                        
heart_x = 48
heart_y = 25

# Ordered list of all the bitmaps and "heart" placeholder for animation
bitmaps = [P_bitmap, I_bitmap, C_bitmap, "heart", B_bitmap, E_bitmap, A_bitmap, T_bitmap]


# --- Splash Screen Animation ---

#Displays the animated splash screen
def draw_splash_screen():
    # Animation loop
    oled.fill(0)
    x_start = 0  # Starting X position
    
    # Draw each character or heart in sequence
    for bmp in bitmaps:
        if bmp == "heart":
            draw_heart(x_start, 25)
        else:
            draw_bitmap(x_start, 25, bmp)
        oled.show()
        time.sleep(0.1)  # Delay between drawing each item
        x_start += 16  # Move X position for next character

    for _ in range(2):
        time.sleep(0.2)
        
        # Shrink: Clear large heart and draw smaller one centered in its place
        oled.fill_rect(heart_x, heart_y, 16, 16, 0)
        draw_small_heart(heart_x + 4, heart_y + 4)  # Center 8x8 inside 16x16 space
        oled.show()
        time.sleep(0.2)

        # Grow: Clear small heart and redraw large heart
        oled.fill_rect(heart_x, heart_y, 16, 16, 0)
        draw_heart(heart_x, heart_y)
        oled.show()
        time.sleep(0.2)

    # Final message after animation
    time.sleep(0.5)
    oled.fill(0)
    oled.text(f"Feel the Beat", 10, 30)
    oled.show()
