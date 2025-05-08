from machine import Pin, I2C, ADC
from piotimer import Piotimer
from fifo import Fifo
import ssd1306
import time
import math
import json
import historian

# OLED Display Setup
i2c = I2C(1, sda=Pin(14), scl=Pin(15), freq=400000)
oled = ssd1306.SSD1306_I2C(128, 64, i2c)

button = Pin(12, Pin.IN, Pin.PULL_UP)

#Test values
# peaks need to be RR intervals (in milliseconds).
#peaks =  [820, 830, 840, 830, 840, 850, 860, 870, 860, 850]


# --- HRV Analysis Functions ---

def calculate_hrv(peaks):
    if len(peaks) < 2: return None  # Absolute minimum
    if len(peaks) < 5: print("Warning: Low reliability")  # Still calculate
    
    # Calculate mean PPI (peak-to-peak interval)
    # Mean PPI (ms) = average interval between heartbeats
    mean_ppi = sum(peaks) / len(peaks)
    if mean_ppi <= 0: return None
    
    # Calculate mean HR (beats per minute)
    # Heart rate (bpm) = 60000 ms (1 min) divided by average interval
    mean_hr = 60000 / mean_ppi  # 60000ms = 1 minute
    
    # Calculate SDNN (standard deviation of of all PPI values)
    squared_diffs = [(x - mean_ppi)**2 for x in peaks]
    variance = sum(squared_diffs) / len(peaks)
    sdnn = math.sqrt(variance)
    
    # Calculate RMSSD (root mean square of successive differences)
    diffs = [peaks[i+1] - peaks[i] for i in range(len(peaks)-1)]
    squared_diffs = [d**2 for d in diffs]
    rmssd = math.sqrt(sum(squared_diffs)/len(squared_diffs)) if len(diffs) >=1 else 0
    
    # Timestamp. Not displayed on Oled due to space concerns. adjusted for local time (e.g., UTC+3)
    timestamp = time.time() + 3 * 3600
    
    return {
        "analysis_type": "basic",
        "id": timestamp,
        "time": timestamp,
        "mean_hr": round(mean_hr, 1),
        "mean_ppi": round(mean_ppi, 1),
        "rmssd": round(rmssd, 1),
        "sdnn": round(sdnn, 1)
    }

def display_results(results):
    oled.fill(0)
    
    # Display header and each HRV metric
    oled.text(f"BASIC ANALYSIS:", 0, 0)
    oled.text(f"HR: {results['mean_hr']:.0f}bpm", 0, 12)
    oled.text(f"PPI: {results['mean_ppi']:.0f}ms", 0, 24)
    oled.text(f"SDNN: {results['sdnn']:.0f}ms", 0, 36)
    oled.text(f"RMSSD: {results['rmssd']:.0f}ms", 0, 48)
    
    oled.show()

def analyze_and_display(peaks, historian_instance, networker=None):
    global button
    # Calculate HRV metrics
    results = calculate_hrv(peaks)
    
    if results:
        if networker:
            # Save results to history and display on screen
            historian_instance.add_measurement(results, networker=networker)
        else:
            # Save results to history and display on screen
            historian_instance.add_measurement(results)
        display_results(results)
        
        # Print to console for debugging
        print("\nHRV Analysis Results:")
        for key, value in results.items():
            print(f"{key}: {value}")
        
    else:
        # Show error message on OLED
        oled.fill(0)
        oled.text("Analysis failed", 0, 16)
        oled.text("Not enough data", 0, 32)
        oled.show()
    
    # Wait for user to press and release button to continue
    while True:
        if button.value() == 1:
            time.sleep(0.05)
            if button.value() == 0:
                return

# --- Test Entry Point ---

if __name__ == "__main__":
    analyze_and_display(peaks)