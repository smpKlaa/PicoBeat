from machine import Pin, I2C,
from rollingaverage import RollingAverage as RollAvg
from peripherals import IRS_ADC
from filo import Filo
from piotimer import Piotimer
from fifo import Fifo
import ssd1306
import time
import _thread
        
class HRA:
    # GPIO PINS
    SENSOR_PIN = 26								# Heart rate sensor pin
    SDA_PIN = 14								# OLED SDA pin
    SCL_PIN = 15								# OLED SCL pin
    
    # ALGORITHM PARAMETERS
    COOLDOWN = 500								# Total cooldown(ms)
    TRESHOLD = 0.7								# Peak detection treshold
    SAMPLE_FREQUENCY = 250						# HR sensor sample frequency
    #SAMPLE_PERIOD = int(1 / SAMPLE_FREQUENCY * 1000) # REDUNDANT
    
    
    def __init__(self, display=None):
        """
        PARAMS:
        display(SSD1306 object): if for passing OLED object.
        """
        
        # INITALIZE DISPLAY. ---------------------------------------------------
        if not display:
            # Initialize I2C pin and channel
            i2c = I2C(1, sda=Pin(HRA.SDA_PIN), scl=Pin(HRA.SCL_PIN), freq=400000)
            i2c.scan()
            # Initialize OLED with I2C pin
            display = ssd1306.SSD1306_I2C(128, 64, i2c)
            
        self.OLED = display        
        
        # INITIALIZE HR SENSOR. ------------------------------------------------
        self.sensor = IRS_ADC(HRA.SENSOR_PIN)
        
        # GPIO PINS ------------------------------------------------------------
        self.rot_button = Pin(12, mode = Pin.IN, pull = Pin.PULL_UP)

        # Algorithm vars -------------------------------------------------------
#         self.max_value = None							# Max value of current peak
#         self.sample_n = 0								# Total amount of samples
#         self.peaks = []									# All recorded peaks
#         self.last_samples_avg_10 = RollAvg(size=10)		# Rolling average of last 10 samples
#         self.last_samples_avg_40 = RollAvg(size=40)		# Rolling average of last 40 samples
#         self.last_samples_raw = Filo(250, typecode = "i")# Last 250 raw sample values
#         self.last_peak = None 							# Last peak timestamp(tick)
#         self.bpm = 0									# Current BPM
#         self.lts_min = None								# Last second lowest value
#         self.lts_max = None								# Last second highest value
#         self.ppi_roll_avg = RollAvg(size=10)			# Rolling average of last 10 PPI(ms)
#         self.cur_cooldown = 0							# Time since artifact(ms)
#         self.last_artifact_timestamp = 0				# Last artifact timestamp(tick)
#         self.artifact_count = 0							# Total amount of artifacts
#         self.thread_running = True						# Global flag for stopping 2. thread
        
#         self.fill_buffer()
        
#     def execute(self):
#         self._function()

    def start_recording(self, mode=None):
        self.OLED.fill(0)
        self.OLED.text("Initializing...", 0, 0, 1)
        self.OLED.show()
        
        # Algorithm vars -------------------------------------------------------
        self.max_value = None							# Max value of current peak
        self.sample_n = 0								# Total amount of samples
        self.peaks = []									# All recorded peaks
        self.last_samples_avg_10 = RollAvg(size=10)		# Rolling average of last 10 samples
        self.last_samples_avg_40 = RollAvg(size=40)		# Rolling average of last 40 samples
        self.last_samples_raw = Filo(250, typecode = "i")# Last 250 raw sample values
        self.last_peak = None 							# Last peak timestamp(tick)
        self.bpm = 0									# Current BPM
        self.lts_min = None								# Last second lowest value
        self.lts_max = None								# Last second highest value
        self.ppi_roll_avg = RollAvg(size=10)			# Rolling average of last 10 PPI(ms)
        self.cur_cooldown = 0							# Time since artifact(ms)
        self.last_artifact_timestamp = 0				# Last artifact timestamp(tick)
        self.artifact_count = 0							# Total amount of artifacts
        self.thread_running = True						# Global flag for stopping 2. thread
        
        # Set mode to 0 by default
        if not mode or (mode != 1 and mode != 2):
            mode = 0
        self.mode = mode
        print("Recording starting...")
        print(f"Mode {mode} selected.")
        
        self.sensor_timer = Piotimer(mode = Piotimer.PERIODIC,
                                     freq = HRA.SAMPLE_FREQUENCY,
                                     callback = self.sensor.handler)
        
        self.fill_buffer()
        return self.record_hrv()

    
    def fill_buffer(self):
        # Find pulse and min-max values.
        print("Initializing...")
        while True :
            if self.sensor.has_data():
                smpl = self.sensor.get()
                # Check if pulse found
                if smpl > 1000:
                    self.sample_n += 1
                    # Restart if pulse is lost
                    if self.sample_n > 500:
                        break
                else:
                    self.sample_n = 0
                self.last_samples_raw.put(smpl)	# Store value for min-max

        print("Init done")
#         self.record_hrv()
        
    
    def record_hrv(self):
        
        # Main program =========================================================
        print("Main program start")
        
        # Reset total samples recorded
        self.sample_n = 0
        # Start timer
        self.start_time = time.ticks_ms()
        # Start thread 1
        _thread.start_new_thread(self.core_1_func, ())

        # Buffer for graph line dots.
        line_buffer = [32] * 64
        
        # Add sample value to graph line buffer.
        def add_to_line(value):
            line_buffer.pop(0)
            line_buffer.append(value)
            return
        
        self.measurement_ready = False
        btn_pressed = False
        while True:
            # Rotary button stops recording.
            if self.rot_button() == 0:
                btn_pressed = True
            if btn_pressed and self.rot_button() == 1:
                self.stop()
                break
            if self.last_samples_avg_10.count > 0:
                
                if self.mode == 1 or self.mode == 2:
                    # If measurement is not ready, update progress.
                    if not self.measurement_ready:
                        progress = time.ticks_diff(time.ticks_ms(), self.start_time) / 30000
                        if progress >= 1:
                            self.measurement_ready = True
                            progress = 1
                
                self.OLED.fill(0)
                
                if self.measurement_ready:
                    self.OLED.text("READY", 87, 0)
                self.OLED.text(f"BPM:{self.bpm}", 0, 0)				# Current BPM
                y = int(60 - (52 * self.last_samples_avg_10.get()))	# Sample Y coord
                
                add_to_line(y)
                
                # Threshold line for debugging.
#                self.OLED.line(0, 25, 127, 25, 1)
                
                # Draw graph to screen.
                for x in range(1, len(line_buffer)):
                    self.OLED.line((x - 1) * 2, line_buffer[x - 1],
                                  (x * 2), line_buffer[x], 1)
                
                if self.mode == 1 or self.mode == 2:
                    self.OLED.fill_rect(0, 60, int(127 * progress), 3, 1)
                self.OLED.show()
        
#         if (self.mode != 0):
        if (self.mode != 0) and (not self.measurement_ready):
            self.OLED.fill(0)
            self.OLED.text("Not enough data", 5, 24, 1)
            self.OLED.show()
            time.sleep(2)
            return None
        return self.peaks


    # Function for 1. core. ----------------------------------------------------
    def core_1_func(self):
        print("[Core 1] Running...")
        
        while self.thread_running:
            if self.sensor.has_data():
                sample = self.sensor.get()	# Get sample from sensor fifo.
                
                # Check for movement artifacts
                self.cur_cooldown = time.ticks_diff(time.ticks_ms(), self.last_artifact_timestamp)
                if (sample < 10000 or sample > 60000) and self.cur_cooldown > HRA.COOLDOWN:
                    print("Pulse artifact")
                    self.artifact_count += 1
                    self.last_artifact_timestamp = time.ticks_ms()
                    continue
                
                self.last_samples_raw.put(sample)	# Store raw sample to fifo.
                
                sample = self.normalize(sample)		# Normalize raw sample to 0-1.
                self.update_rolling_averages(sample)	# Update rolling averages.
                
                self.sample_n += 1					# Keep track of total recorded samples
                
                # Calculate peak-to-peak interval. -----------------------------
                interval = 0	# Time since last peak, in milliseconds
                if self.last_peak != None :
                    # Calculate the time since last peak in milliseconds
                    interval = time.ticks_diff(time.ticks_ms(), self.last_peak)
                else:
                    # If there is no peaks so far, interval is time since start
                    # Not the best approach. Maybe FIX.
                    interval = time.ticks_diff(time.ticks_ms(), self.start_time)
                
                # Check for peak. ----------------------------------------------
                if self.is_peak(sample):
                    print("PEAK")
                    self.last_peak = time.ticks_ms()
                    
                    # Filter heart beat echo
                    if interval < 300:
                        continue
                    elif interval > 1700:
                        continue
                    self.peaks.append(interval)
                    # Calculate current PPI
                    self.ppi_avg = self.ppi_roll_avg.update(interval)
                    # Calculate current BPM
                    self.bpm = int(60 / (self.ppi_avg / 1000))

    # Find min and max values of recent values
    def find_min_max(self):
        # max and min functions may be slow.
        self.lts_max = max(self.last_samples_raw.data)
        self.lts_min = min(self.last_samples_raw.data)


    # Normalize any sample value to 0-1
    def normalize(self, sample_value):
        # Find min and max values every second.
        if self.sample_n % 250 == 0:
            self.find_min_max()
        # Apply min max normalization to raw sample value.
        normalized_sample = (sample_value - self.lts_min) / (self.lts_max - self.lts_min)
        
        # Check for out of bounds values.
        if normalized_sample > 1:
            normalized_sample = 1		# Clamp value to max
            self.lts_max = sample_value	# Move max to value
        if normalized_sample < 0:
            normalized_sample = 0
            self.lts_min = sample_value
            
        return normalized_sample
    
    
    # Check if sample value is peak
    def is_peak(self, sample_value):
        
        # Filter noisy samples with last 10 sample average.
        sample_value = self.last_samples_avg_10.get()
        
        # Check if sample is over treshold.
        if sample_value > HRA.TRESHOLD:
            # If no max value or value is bigger than max.
            if self.max_value is None or sample_value > self.max_value:
                self.max_value = sample_value	# Make value new max.
        # Check if value drops below treshold.
        elif sample_value <  HRA.TRESHOLD and self.max_value is not None:
            self.max_value = None		# Reset max value for new peak
            return True					# Return true
        return False


    # Update all rolling averages with new value
    def update_rolling_averages(self, val):
        self.last_samples_avg_10.update(val)	# Last 10 sample average value
        self.last_samples_avg_40.update(val)	# Last 40 sample average value


    # Stop program
    def stop(self):
        
        # Print total samples recorded.
        # DEBUG
        print(f"Total samples recorded: {self.sample_n}")
        # Print total time elapsed.
        # DEBUG
        time_since_start = time.ticks_diff(time.ticks_ms(), self.start_time) / 1000
        print(f"Total time elapsed: {time_since_start}s")
        
        # Stop timer.
        self.sensor_timer.deinit()
        # Stop 2. thread.
        self.thread_running = False
        # Empty sensor fifo
        self.sensor.reset_fifo()


if __name__ == "__main__":
    hra = HRA()
    hra.start_recording(mode=1)
