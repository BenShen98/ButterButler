
import smbus
from time import sleep
import json

def main(mqtt,idstr):
    sensordict={0x03:'floortemp', 0x01:'ceilingtemp'} # 0x03:objtemp, 0x01:devicetemp

    # register to server
    for sensorname in sensordict.values():
        config = json.dumps({"device_class": "temperature",
            "name": sensorname,
            "state_topic": f"butterbutler/sensor/{idstr}",
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
            reading[sensorname]=cTemp

        mqtt.publish(f"butterbutler/sensor/{idstr}", json.dumps(reading))
        sleep(1)
