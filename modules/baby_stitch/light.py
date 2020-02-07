from gpiozero import PWMLED
import json
from time import sleep

class Light():
    def __init__(self,r_pin,g_pin,b_pin):
        self.state=(255,255,255) # (r,g,b) value
        self.brightness=255
        self.r=PWMLED(r_pin)
        self.g=PWMLED(g_pin)
        self.b=PWMLED(b_pin)

        self.update()

    def update(self):
        r, g, b = self.state
        r,g,b=((r*self.brightness)/255,(g*self.brightness)/255,(b*self.brightness)/255)

        self.r.value=(330-r)/330
        self.b.value=(255-b)/255
        self.g.value=(255-g)/255

    def setcolour(self,r,g,b):
        self.state=(r,g,b)
        self.update()

    def setbright(self, bright):
        self.brightness=bright
        self.update()

light=Light(17,27,22)

def on_message(client,userdata,message):
    data=message.payload.decode('utf-8')
    print(data)
    data=json.loads(data)
    if (data['state']=="ON"):
        if ('color' in data):
            color=data['color']
            light.setcolour(color['r'], color['g'], color['b'])
        elif ('brightness' in data):
            light.setbright(data['brightness'])

    else:
       light.setbright(0)

def main(mqtt, idstr, r_pin=17,g_pin=27,b_pin22=22):

    # register to server
    config=json.dumps({
        "schema": "json",
        "optimistic": True,
        "state_topic": f"butterbutler/light/{idstr}",
        "command_topic": f"butterbutler/light/{idstr}/set",
        "json_attributes_topic": f"butterbutler/light/{idstr}",
        "brightness": True,
        "rgb": True
    })
    mqtt.publish(f"homeassistant/light/{idstr}/light/config",config)

    mqtt.message_callback_add(f"butterbutler/light/{idstr}/set",on_message)