from machine import Pin, I2C, ADC
from rollingaverage import RollingAverage as RollAvg
from filo import Filo
from piotimer import Piotimer
from fifo import Fifo
import ssd1306
import time
import _thread

class isr_adc:
    def __init__(self, adc_pin_nr):
        self.av = ADC(adc_pin_nr) # Sensor AD channel
        self.samples = Fifo(50) # Fifo where ISR will store samples
    def handler(self, tid):
        self.samples.put(self.av.read_u16())

# GPIO PINS --------------------------------------------------------------------
SENSOR_PIN = 26
SDA_PIN = 14
SCL_PIN = 15

# HR SENSOR INITIALIZATION. ----------------------------------------------------
SAMPLE_FREQUENCY = 250
SAMPLE_PERIOD = int(1 / SAMPLE_FREQUENCY * 1000) # REDUNDANT

SENSOR = isr_adc(SENSOR_PIN)
SENSOR_TIMER = Piotimer(mode = Piotimer.PERIODIC,
                        freq = SAMPLE_FREQUENCY,
                        callback = SENSOR.handler)

# DISPLAY INITALIZATION. -------------------------------------------------------

# Initialize I2C pin and channel
i2c = I2C(1, sda=Pin(SDA_PIN), scl=Pin(SCL_PIN), freq=400000)
i2c.scan()

# Initialize OLED with I2C pin
OLED = ssd1306.SSD1306_I2C(128, 64, i2c)

# Global vars ------------------------------------------------------------------
max_value = None							# Max value of current peak
sample_n = 0								# Total amount of samples
peaks = []									# All recorded peaks
last_samples_avg_10 = RollAvg(size=10)		# Rolling average of last 10 samples
last_samples_avg_40 = RollAvg(size=40)		# Rolling average of last 40 samples
last_samples_raw = Filo(250, typecode = "i")# Last 250 raw sample values
bpm = 0										# Current BPM
lts_min = None								# Last second lowest value
lts_max = None								# Last second highest value
ppi_roll_avg = RollAvg(size=10)				# Rolling average of last 10 PPI(ms)
TRESHOLD = 0.7								# Peak detection treshold
cur_cooldown = 0							# Time since artifact(ms)
COOLDOWN = 500								# Total cooldown(ms)
last_artifact_timestamp = 0					# Last artifact timestamp(tick)
thread_running = True						# Global flag for stopping 2. thread

# Loading screen ---------------------------------------------------------------
OLED.fill(0)
OLED.text("Searching for a pulse...", 0, 0, 1)	# DEBUG
OLED.show()


# Function for 2. core. --------------------------------------------------------
def draw_graph():
    global OLED, last_samples_avg_10, sample_n, thread_running, bpm
    print("[Core 2] Running...")
    
    # Buffer for graph line dots.
    line_buffer = [32] * 64
    
    # Add sample value to graph line buffer.
    def add_to_line(value):
        line_buffer.pop(0)
        line_buffer.append(value)
        return
    
    while thread_running:
        if last_samples_avg_10.count > 0:
            OLED.fill(0)
            
            OLED.text(f"BPM:{bpm}", 0, 0)					# Current BPM
            y = int(64 - (63 * last_samples_avg_10.get()))	# Sample Y coord
            
            add_to_line(y)
            
            # Threshold line for debugging.
#             OLED.line(0, 19, 127, 19, 1)
            
            # Draw graph to screen.
            for x in range(1, len(line_buffer)):
                OLED.line((x - 1) * 2, line_buffer[x - 1],
                          (x * 2), line_buffer[x], 1)
            OLED.show()

# Find min and max values of recent values
def find_min_max():
    global lts_min, lts_max
    # max and min functions may be slow.
    lts_max = max(last_samples_raw.data)
    lts_min = min(last_samples_raw.data)

# Normalize any sample value to 0-1
def normalize(sample_value):
    global lts_min, lts_max, sample_n
    # Find min and max values every second.
    if sample_n % 250 == 0:
        find_min_max()
    # Apply min max normalization to raw sample value.
    normalized_sample = (sample_value - lts_min) / (lts_max - lts_min)
    
    # Check for out of bounds values.
    if normalized_sample > 1:
        normalized_sample = 1	# Clamp value to max
        lts_max = sample_value	# Move max to value
    if normalized_sample < 0:
        normalized_sample = 0
        lts_min = sample_value
    return normalized_sample
    
# Check if sample value is peak
def is_peak():
    global max_value, TRESHOLD, last_samples_avg_10
    
    # Filter noisy samples with last 10 sample average.
    sample_value = last_samples_avg_10.get()
    
    # Check if sample is over treshold.
    if sample_value > TRESHOLD:
        # If no max value or value is bigger than max.
        if max_value is None or sample_value > max_value:
            max_value = sample_value	# Make value new max.
    # Check if value drops below treshold.
    elif sample_value < TRESHOLD and max_value is not None:
        max_value = None	# Reset max value for new peak
        return True			# Return true
    return False

# Update all rolling averages with new value
def update_rolling_averages(val):
    global last_samples_avg_10, last_samples_avg_40
    last_samples_avg_10.update(val)	# Last 10 sample average value
    last_samples_avg_40.update(val)	# Last 40 sample average value

# Stop program
def stop():
    global sample_n, start_time, SENSOR_TIMER, thread_running
    
    # Print total samples recorded.
    # DEBUG
    print("Total samples recorded: {sample_n}")
    # Print total time elapsed.
    # DEBUG
    time_since_start = time.ticks_diff(time.ticks_ms(), start_time) / 1000
    print("Total time elapsed: {time_since_start}s")
    
    # Stop timer.
    SENSOR_TIMER.deinit()
    # Stop 2. thread.
    thread_running = False



# Main program =================================================================

# Find pulse and min-max values.
print("Initializing...")
while True :
    if SENSOR.samples.has_data():
        smpl = SENSOR.samples.get()
        # Check if pulse found
        if smpl > 1000:
            sample_n += 1
            # Restart if pulse is lost
            if sample_n > 500:
                break
        else:
            sample_n = 0
        last_samples_raw.put(smpl)	# Store sample value for finding min-max

print("Init done")

# Reset total samples recorded
sample_n = 0
# Start timer
start_time = time.ticks_ms()
# Start thread 2
_thread.start_new_thread(draw_graph, ())

# Main loop --------------------------------------------------------------------
while True:
    if SENSOR.samples.has_data():
        sample = SENSOR.samples.get()	# Get sample from sensor fifo.
        
        # Check for movement artifacts
        cur_cooldown = time.ticks_diff(time.ticks_ms(), last_artifact_timestamp)
        if (sample < 10000 or sample > 60000) and cur_cooldown > COOLDOWN:
            print("Pulse artifact")
            last_artifact_timestamp = time.ticks_ms()
            continue
        
        last_samples_raw.put(sample)	# Store raw sample to fifo.
        
        sample = normalize(sample)		# Normalize raw sample to 0-1.
        update_rolling_averages(sample)	# Update rolling averages.
        
        sample_n += 1					# Keep track of total recorded samples
        
        # Calculate peak-to-peak interval. -------------------------------------
        interval = 0	# Time since last peak, in milliseconds
        if peaks:
            # Calculate the time since last peak in milliseconds
            interval = time.ticks_diff(time.ticks_ms(), peaks[-1][1])
        else:
            # If there is no peaks so far, interval is time since start
            # Not the best approach. Maybe FIX.
            interval = time.ticks_diff(time.ticks_ms(), start_time)
        
        # Check for peak. ------------------------------------------------------
        if is_peak():
            timestamp = time.ticks_ms()
            #print("PEAK!", sample_n)	# DEBUG
            
            # Filter heart beat echo
            if interval < 300:
                continue
            
            # Create array element to store peak data
            arr = [sample_n, timestamp, interval, max_value]
            peaks.append(arr)
            
            # Calculate current PPI
            ppi_avg = ppi_roll_avg.update(interval)
            # Calculate current BPM
            bpm = int(60 / (ppi_avg / 1000))
        
        
        # DEBUG - Print BPM every 500 samples. ---------------------------------
#         if sample_n % 500 == 0:
#             print("BPM:", bpm)

        # DEBUG - Stop measuring after 10 seconds. -----------------------------
#         if time.ticks_diff(time.ticks_ms(), start_time) >= 10000:
#             stop()
#             print("STOPPED RECORDNING")
