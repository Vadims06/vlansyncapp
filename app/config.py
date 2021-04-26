import os

class DB:
    MONGO_HOST = os.environ.get('MONGODB_HOSTNAME', "mongodb1")
    MONGO_PORT = 27017
    MONGO_DB = os.environ.get('MONGODB_DATABASE', "vlans")

class Device:
    NET_DEVICE_HOST = os.environ.get('NET_DEVICE_HOST', "192.168.1.1")
    NET_DEVICE_USERNAME = os.environ.get('NET_DEVICE_USERNAME', "cisco")
    NET_DEVICE_PASSWORD = os.environ.get('NET_DEVICE_PASSWORD', "cisco")