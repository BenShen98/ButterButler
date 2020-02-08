#! /usr/bin/python3
import logging
logging.basicConfig(level=logging.INFO,
    format='%(levelname)s:%(asctime)s %(filename)s:%(funcName)s: %(message)s',
    datefmt='%H:%M'
)

import threading
import yaml
import sys
import ssl

import paho.mqtt.client as mqtt
from random import random
from time import sleep



def on_unmatched_message(client, userdata, msg):
    logging.debug(f"ignore msg {msg.topic} {msg.payload.decode('utf-8')}")

def load_config(cpath):
    with open(cpath) as cfile:
        config=yaml.load(cfile, Loader=yaml.BaseLoader)
        logging.debug(f"parse config {config}")
        return config

def start_mqtt(mqttconfig, log_level='INFO'):
    NAME = 'Paho'

    client = mqtt.Client(userdata={})
    client.tls_set(ca_certs=mqttconfig['cafile'], certfile=mqttconfig['cert'], keyfile=mqttconfig['key'], cert_reqs=ssl.CERT_REQUIRED,
    tls_version=ssl.PROTOCOL_TLS)
    client.on_message = on_unmatched_message
    client.connect(mqttconfig['host'], int(mqttconfig['port']))
    logger = logging.getLogger(NAME)
    logger.setLevel(log_level)
    client.enable_logger(logger)

    # start async listen
    client.loop_start()
    client._thread.name=NAME
    client.subscribe(f"{mqttconfig['topic_perfix']}/#")
    sleep(1) # wait for connection setup

    return client

def start_modules(modulesconfig, mqttclient, topicperfix):
    # init modules3
    for module_name, file_names in modulesconfig.items():
        for file_name in file_names:
            idstr=f"{module_name}_{file_name}"
            mod = __import__(f"{module_name}.{file_name}", fromlist=['main'])
            threading.Thread(name=file_name, target=mod.main, args=(mqttclient,idstr,topicperfix)).start()
            logging.info(f"started {idstr}")

def main():
    threading.current_thread().name = "Daemon"

    # load userconfig
    configs=load_config(sys.argv[1])
    log_levels=configs['log_level']

    # set root logger level
    logging.getLogger().setLevel(log_levels['main'])

    # config mqtt
    client = start_mqtt(configs['mqtt'],log_levels['paho'])

    # register modules
    # publish modules may be blocking, subscribe modules should blocking
    start_modules(configs['modules'], client, configs['mqtt']['topic_perfix'])

    # blocking forever
    client._thread.join()


if __name__ == "__main__":
    main()