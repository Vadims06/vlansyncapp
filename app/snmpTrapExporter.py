#!/usr/bin/python
import sys
import logging
import logging.handlers
import copy
import pandas as pd
from Connector import Connector
from routes import Vlans, app_redis
con = Connector()
from VlanComparator import Comparator
vlan_comparator = Comparator(con, Vlans)

# logging part
logger = logging.getLogger("snmptrapd-vlansync-app")
logger.setLevel(logging.DEBUG)

f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

syslog_handler = logging.handlers.SysLogHandler()
syslog_handler.setFormatter(f_format)
logger.addHandler(syslog_handler)

out_handler = logging.StreamHandler(sys.stdout)
out_handler.setFormatter(f_format)
logger.addHandler(out_handler)

# adjust logging level from the config file 
numeric_level = "DEBUG"
logger.setLevel(numeric_level)

lines = sys.stdin.readlines()

# Parsing input from snmptrapd
for line in lines[2:]:
    if 'snmpTrapAddress' in line:
        src_addr_ll = line.strip().split(' ', 1) #  ['SNMP-COMMUNITY-MIB::snmpTrapAddress.0', '192.168.1.49']
        src_addr = src_addr_ll[1] if src_addr_ll else ''
        logger.debug(f"Source Trap address {src_addr}")

logger.info("Time to get VLANS")

dev_vlans_only = vlan_comparator.get_dev_vlans_only()
db_vlans_only = vlan_comparator.get_db_vlans_only()

logger.info(f"device_vlan_dd_ll:{dev_vlans_only}")
logger.info(f"db_vlan_dd_ll:{db_vlans_only}")

for row in dev_vlans_only:
    # device-only vlans should be added to the DB
    vlan = Vlans(vlan_id = row['vlan_id'], name = row['name'])
    logger.info(f"add vlan to Database:{vlan.vlan_id}")
    vlan.save()
    # save our action in cache for 2 seconds
    app_redis.set(str(vlan.vlan_id), 'insert', ex=2)

for row in db_vlans_only:
    # Vlans which exist on DB, but not in device. Remove these vlans from DB
    logger.info(f"delete vlan {row['vlan_id']} from DB")
    vlan = Vlans.objects.get(vlan_id = row['vlan_id'] )
    vlan.delete()
    # save our operation in cache for 2 seconds
    app_redis.set(str(vlan.vlan_id), 'delete', ex=2)

if not dev_vlans_only and not db_vlans_only:
    logger.info(f"vlans on Device and in Database are the same")

# Update vlans
vlan_comparator = Comparator(con, Vlans)
not_updated_vlans_on_db = vlan_comparator.getVlanNameDiffWithDeviceDF()
for row in not_updated_vlans_on_db:
    # compare Vlan ID and Vlan Name. We received Trap from a device, so vlan name from Device is the latest and actual - update vlan's name in DB
    vlan = Vlans.objects.get(vlan_id = row['vlan_id'] )
    logger.info(f"update vlan:{vlan.vlan_id}")
    vlan.update(**{'name': row['name']})