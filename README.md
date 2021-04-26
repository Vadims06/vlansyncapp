# Vlan Synchronization app

* How to start

The app is used MongoDB watch, which requires a repliset. After first boot - you will need to apply replicaset config manually (it's not automated yet)

### Starting the App
docker-compose up -d

1. Exec into mongodb container `docker exec -it mongodb1 mongo`
2. Apply replicaset config, run `config = { "_id" : "mongo-rs", "members" : [ { "_id" : 0, "host" : "mongodb1:27017", "priority": 2}, { "_id" : 1, "host" : "mongodb2:27017" }, { "_id" : 2, "host" : "mongodb3:27017" }] }
rs.initiate(config)
db.isMaster()`.
3. Wait some time in order to see the following output `mongo-rs:PRIMARY>`

### Stoping the App
docker-compose down

# Logging

1. `docker logs dblistener` for checking events from MongoDB
2. `docker logs snmplistener` for getting info about events from devices

# SNMP configuration on a device
`snmp-server host <this application host> public config`
`snmp-server enable traps config`