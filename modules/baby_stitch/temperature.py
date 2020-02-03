
import smbus
import time
bus = smbus.SMBus(1)


data = []
data.append(0x15)
data.append(0x40)
bus.write_i2c_block_data(0x40, 0x02, data)
datal = []
datal.append(0x15)
datal.append(0x15)
bus.write_i2c_block_data(0x40, 0x02, datal)
index =0
while(True):
    data = bus.read_i2c_block_data(0x40, 0x03, 2)
    datal = bus.read_i2c_block_data(0x40, 0x01, 2)
    # Convert object temperature to 14-bits
    cTemp = ((data[0] * 256 + (data[1] & 0xFC)) / 4)
    if cTemp > 8191 :
        cTemp -= 16384
    cTemp = cTemp * 0.03125
    #convert die temperature to 14-bits
    cTempl = ((datal[0] * 256 + (datal[1] & 0xFC)) / 4)
    if cTempl > 8191 :
        cTempl -= 16384
    cTempl = cTempl * 0.03125


    print(f'Object Temperature in Celsius :{cTemp} C')
    print(f'local Temperature in Celsius :{cTempl} C')



