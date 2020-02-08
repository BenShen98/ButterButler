
import smbus
from time import sleep
import json
import logging

def main(mqtt,idstr, base):
    sensordict={0x03:'objtemp', 0x01:'devicetemp'}
    state_topic=f"{base}/sensor/{idstr}"

    # register to server
    for sensorname in sensordict.values():
        config = json.dumps({"device_class": "temperature",
            "name": sensorname,
            "state_topic": state_topic,
            "unit_of_measurement": "°C",
            "value_template": "{{ value_json."+sensorname+"}}"})

        mqtt.publish(f"homeassistant/sensor/{idstr}_{sensorname}/config",config)

    # init sensor
    bus = smbus.SMBus(1)
    data = []
    data.append(0x15)
    data.append(0x40)
    bus.write_i2c_block_data(0x40, 0x02, data)
    datal = []
    datal.append(0x15)
    datal.append(0x15)
    bus.write_i2c_block_data(0x40, 0x02, datal)

    # read data
    reading={}
    while(True):
        for sensoraddr,sensorname in sensordict.items():
            data = bus.read_i2c_block_data(0x40, sensoraddr, 2)
            # Convert temperature to 14-bits
            cTemp = ((data[0] * 256 + (data[1] & 0xFC)) / 4)
            if cTemp > 8191 :
                cTemp -= 16384
            cTemp = cTemp * 0.03125
            reading[sensorname]=round(cTemp,1)

        logging.debug(f"get temp measurement {reading}")
        mqtt.publish(state_topic, json.dumps(reading))
        sleep(1)
