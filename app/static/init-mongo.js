let error = true

let config = { "_id" : "mongo-rs", "members" : [ { "_id" : 0, "host" : "mongodb1:27017", "priority": 2}, { "_id" : 1, "host" : "mongodb2:27017", "priority": 1}, { "_id" : 2, "host" : "mongodb3:27017", "priority": 1}] }
rs.initiate(config)
rs.status()


if (error) {
    print('Error, exiting')
    quit(1)
  }