import logging

import smbus
from time import sleep
import json
from collections import deque
class Gesture:
    def __init__(self, mqtt, light, topic):
        command_topic=f"{topic}/set"

        # init gesture
        config = json.dumps({
            "name": "gesture topic",
            "state_topic": topic,
            "availability_topic": topic,
            "command_topic": command_topic,
            "icon": "mdi:hand"
        })
        mqtt.publish(f"homeassistant/switch/{topic.rsplit('/',1)[1]}/config", config)
        mqtt.message_callback_add(command_topic,self.get_gesture_callback())

        # init state
        self.active="ON"
        self.light=light
        self.topic=topic
        self.mqtt=mqtt

        # state machine
        self.start=None # None means not start, number means first number
        self.reads=deque([0]*3)
        self.sum=0
        self.start_bright=0

        mqtt.publish(topic, "online")
        sleep(0.01)
        mqtt.publish(topic,self.active)

    def reading(self, reading):
        # CONFIGS
        MIN_DIS = 30
        MAX_DIS = 260
        DIS_SCALE = 1.5

        mid_dis=(MIN_DIS+MAX_DIS)/2
        half_dis=(MAX_DIS-MIN_DIS)/2

        # update value
        self.sum += reading - self.reads.popleft()
        self.reads.append(reading)

        mean=self.sum/3
        if self.active=="ON": # master control

            if self.start is None:
                # idel state
                if ( abs(reading-mid_dis)<half_dis and abs(mean-reading)<10 ):
                    # start between MIN_DIS and MAX_DIS, stable for 5 readings (1s)
                    self.start=reading
                    self.start_bright=self.light.brightness

            else:
                # running state
                if abs(mean - reading)>150 or reading > MAX_DIS:
                    # hand left, exit control
                    self.start = None
                else:
                    # control light, use mean to smooth change
                    target_b = (mean - self.start)*DIS_SCALE + self.start_bright
                    if abs(target_b-self.light.brightness) > 1:
                        logging.debug(f"gesture update:{self.start} mean:{mean} bright:{self.light.brightness}")
                        self.light.setbright(target_b)

    def set_active(self, active):
        self.active=active
        self.mqtt.publish(self.topic, active)
        if self.active=="OFF":
            self.start=None

    def get_gesture_callback(self):

        def gesture_callback(client,userdata,message):
            self.set_active(message.payload.decode('utf-8'))

        return gesture_callback




def str_error(code):
    # 11=good ,1,2,3 =HW Fail 6,9=Phase Fail 8,10=Min Range Fail 4=Signal Fail 0,5 not specified
    if code == 11:
        return None
    elif code in [1,2,3]:
        return "HW Fail"
    elif code in [6, 9]:
        return "Phase Fail"
    elif code in [8, 10]:
        return "Min Range Fail"
    elif code == 4:
        return "Signal Fail"
    else:
        return "not specified"

def u16(lsb, msb):
    return ((msb & 0xFF) << 8)  | (lsb & 0xFF)
def VL53L0X_decode_vcsel_period(vcsel_period_reg):
    vcsel_period_pclks = (vcsel_period_reg + 1) << 1
    return vcsel_period_pclks

def main(mqtt, idstr, base):
    state_topic=f"{base}/sensor/{idstr}"
    gesture_topic=f"{base}/switch/{idstr}_gesture"
    sensorname="distance"

    # gesture config
    light=None
    sleep(2)
    for name, instance in mqtt._userdata.items():
        if "light" in name:
            light=instance
            break

    if light:
        gesture=Gesture(mqtt, light,gesture_topic)
    else:
        logging.warning("unable find light instance, no gesture support")

    # sensor config
    VL53L0X_REG_IDENTIFICATION_MODEL_ID	= 0x00c0
    VL53L0X_REG_IDENTIFICATION_REVISION_ID	= 0x00c2
    VL53L0X_REG_PRE_RANGE_CONFIG_VCSEL_PERIOD = 0x0050
    VL53L0X_REG_FINAL_RANGE_CONFIG_VCSEL_PERIOD	= 0x0070
    VL53L0X_REG_SYSRANGE_START = 0x000
    VL53L0X_REG_RESULT_RANGE_STATUS = 0x0014

    address = 0x29

    # init sensor
    bus = smbus.SMBus(1)
    Revision_ID = bus.read_byte_data(address, VL53L0X_REG_IDENTIFICATION_REVISION_ID)
    Device_ID = bus.read_byte_data(address, VL53L0X_REG_IDENTIFICATION_MODEL_ID)
    # PRE_RANGE_CONFIG_VCSEL_PERIOD_DECODE = bus.read_byte_data(address, VL53L0X_REG_PRE_RANGE_CONFIG_VCSEL_PERIOD)
    # FINAL_RANGE_CONFIG_VCSEL_PERIOD_DECODE = bus.read_byte_data(address, VL53L0X_REG_FINAL_RANGE_CONFIG_VCSEL_PERIOD)

    # register to server
    config = json.dumps({
        "name": sensorname,
        "state_topic": state_topic,
        "json_attributes_topic": state_topic,
        "unit_of_measurement": "mm",
        "icon": "mdi:arrow-collapse-vertical",
        "value_template": "{{ value_json.distance }}",
        "device":{
            "sw_version": Revision_ID,
            "identifiers": Device_ID
        }
    })
    mqtt.publish(f"homeassistant/sensor/{idstr}_{sensorname}/config",config)

    while True:

        bus.write_byte_data(address, VL53L0X_REG_SYSRANGE_START, 0x01)
        for _ in range(100):
            sleep(0.001)
            val = bus.read_byte_data(address, VL53L0X_REG_RESULT_RANGE_STATUS)
            if (val & 0x01):
                break

        data = bus.read_i2c_block_data(address, VL53L0X_REG_RESULT_RANGE_STATUS, 12)
        status = (data[0] & 0x78) >> 3

        if status==11:
            SPAD_Rtn_count = u16(data[3], data[2])
            signal_count = u16(data[7], data[6])
            ambient_count = u16(data[9], data[8])
            distance = u16(data[11], data[10])

            reading={
                "SPAD_Rtn_count": SPAD_Rtn_count,
                "signal_count": signal_count,
                "ambient_count": ambient_count,
                "distance": distance
            }

            gesture.reading(distance)

            mqtt.publish(state_topic, json.dumps(reading))
        else:
            logging.debug(f"TOF sensor error {status} {str_error(status)}")

        sleep(0.2)
