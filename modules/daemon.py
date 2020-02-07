#! /usr/bin/python3

import paho.mqtt.client as mqtt
from random import random
from time import sleep

import logging
import threading
import yaml
import sys
import ssl

def on_unmatched_message(client, userdata, msg):
    logging.debug(f"unmatched msg at {msg.topic} {msg.payload.decode('utf-8')}")

def load_config(cpath):
    with open(cpath) as cfile:
        return yaml.load(cfile, Loader=yaml.BaseLoader)

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

def start_modules(modulesconfig, mqttclient):
    # init modules3
    for module_name, file_names in modulesconfig.items():
        for file_name in file_names:
            idstr=f"{module_name}_{file_name}"
            mod = __import__(f"{module_name}.{file_name}", fromlist=['main'])
            threading.Thread(name=file_name, target=mod.main, args=(mqttclient,idstr,)).start()


def main():
    threading.current_thread().name = "Daemon"

    # load userconfig
    configs=load_config(sys.argv[1])
    log_level=configs['log_level']

    # config loger
    logging.basicConfig(level=log_level['main'],
        # format='%(asctime)s %(threadName)s:%(funcName)s: %(message)s',
        # datefmt='%Y-%m-%d %H:%M'
        format='%(asctime)s %(filename)s:%(funcName)s: %(message)s',
        datefmt='%H:%M'
    )

    # config mqtt
    client = start_mqtt(configs['mqtt'],log_level['paho'])

    # register modules
    # publish modules may be blocking, subscribe modules should blocking
    start_modules(configs['modules'], client)

    # blocking forever
    client._thread.join()


if __name__ == "__main__":
    main()