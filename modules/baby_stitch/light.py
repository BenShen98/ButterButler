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

        self.r.value=(260-r)/260
        self.b.value=(255-b)/255
        self.g.value=(255-g)/255

    def setcolour(self,r,g,b):
        self.state=(r,g,b)
        self.update()

    def setbright(self, bright):
        self.brightness=bright
        self.update()

    def __str__(self):
        return f"state {self.state}, brightness {self.brightness}"

    def getstates(self):
        state = "ON" if self.brightness!=0 else "OFF"
        r,g,b=self.state
        return {
            "state": state,
            "color": {"r":r, "g":g, "b":b},
            "brightness":self.brightness
        }


def on_message(client,userdata,message):
    state_topic=message.topic.rsplit('/',1)[0]
    idstr=state_topic.rsplit('/',1)[1]
    light=userdata[idstr]

    data=message.payload.decode('utf-8')
    data=json.loads(data)
    if (data['state']=="ON"):
        if ('color' in data):
            color=data['color']
            light.setcolour(color['r'], color['g'], color['b'])
        elif ('brightness' in data):
            light.setbright(data['brightness'])
        else:
            light.setbright(255)
    else:
       light.setbright(0)

    client.publish(state_topic,json.dumps(light.getstates()))


def main(mqtt, idstr, r_pin=17,g_pin=27,b_pin22=22):

    state_topic=f"butterbutler/light/{idstr}"
    command_topic=state_topic+"/set"

    # register to server
    config=json.dumps({
        "schema": "json",
        "state_topic": state_topic,
        "command_topic": command_topic,
        "json_attributes_topic": state_topic,
        "brightness": True,
        "rgb": True
    })
    mqtt.publish(f"homeassistant/light/{idstr}/light/config",config)

    # init light
    light=Light(17,27,22)
    mqtt._userdata[idstr]=light
    mqtt.publish(state_topic,json.dumps(light.getstates()))

    mqtt.message_callback_add(command_topic,on_message)
