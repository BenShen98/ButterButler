# Project

TODO: intro

# Architecture Overview
For every set of solution we provide to our customer, will include
- many sensors and motors modules
- one reliable master collect data from all sensors and command motors

If customer want and willing to pay additional subscription, their master will be able to connect to our cloud, to backup data and provide further features.

# Operational Model
As we are creating network of connected devices in people's home. It is important to put security and privacy first. This is way in our `location model`, we placed all components in their home.

- hub -> raspberry pi 2 running docker
- models -> raspberry zero, ESP8266

wifi models connect to hub using MQTT over TSL encryption.


# Git Branch Layout

- `master` branch for completed version
- `hub` branch for completed hub
- `models/{modelname}` branch for completed model
- `dev/{modelname}/{featurename}` branch for dev

# Team
...