import network
import mip
from time import sleep
from umqtt.simple import MQTTClient

# :21883

# Replace these values with your own
SSID = ""
PASSWORD = ""
BROKER_IP = ""

# Function to connect to WLAN
def connect_wlan():
    # Connecting to the group WLAN
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)

    # Attempt to connect once per second
    while wlan.isconnected() == False:
        print("Connecting... ")
        sleep(1)

    # Print the IP address of the Pico
    print("Connection successful. Pico IP:", wlan.ifconfig()[0])

# Function to install MQTT
def install_mqtt():
    try:
        mip.install("umqtt.simple")
    except Exception as e:
        print(f"Could not install MQTT: {e}")

def connect_mqtt():
    mqtt_client = MQTTClient("", BROKER_IP)
    mqtt_client.connect(clean_session=True)
    return mqtt_client