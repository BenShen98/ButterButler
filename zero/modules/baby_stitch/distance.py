import logging

import smbus
from time import sleep
import json

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
    sensorname="distance"

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

            mqtt.publish(state_topic, json.dumps(reading))
        else:
            logging.debug(f"TOF sensor error {status} {str_error(status)}")

        sleep(1)
