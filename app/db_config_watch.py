import asyncio
import motor.motor_asyncio
from config import DB
import json
from Connector import Connector
con = Connector()
from routes import Vlans, app_redis
from VlanComparator import Comparator
vlan_comparator = Comparator(con, Vlans)

def parse_db_update(change_dd, db_collection):
    """
    Accept DB change from watch process and parse VlanID and VlanName 
    """
    oper_type = change_dd['operationType'] # 'insert', 'update', 'delete'
    vlan_id = int(change_dd.get('fullDocument', {}).get('vlan_id', -1))
    vlan_name = change_dd.get('fullDocument', {}).get('name', '')
    if oper_type == 'update':
        db_key = change_dd.get('documentKey', {}).get('_id', '')
        '''
        {'_id': ObjectId('6077532db0d6448822c159dd'),
         'vlan_id': 11,
         'name': 'Vlan 11 -> 111'}
        '''
        vlan_obj = db_collection.objects.get(id = db_key )
        vlan_id = vlan_obj.vlan_id
        vlan_name = vlan_obj.name
    return vlan_id, vlan_name

def get_db_vs_device_diff():
    '''{'_id': {'_data': '82608089ADF0004'}, 'operationType': 'delete', 'clusterTime': Timestamp(1619036649, 1), 'ns': {'db': 'vlans', 'coll': 'vlans'}, 'documentKey': {'_id': ObjectId('60807ef05a61f0d195ba7adf')}}'''
    vlan_comparator = Comparator(con, Vlans)
    dev_vlan_only_df = vlan_comparator.get_dev_vlans_only() # could be diff more than one vlan
    vlan_attr_dd_ll = json.loads(dev_vlan_only_df.to_json(orient='records'))
    return vlan_attr_dd_ll

def parse_db_action(change_dd):
    return change_dd['operationType'] # 'insert', 'update', 'delete'

async def main_watcher():
    client = motor.motor_asyncio.AsyncIOMotorClient(DB.MONGO_HOST, replicaset='mongo-rs')
    db = client.vlans
    print('start main_watcher')
    async for change in db.vlans.watch():
        print(change)
        db_action = parse_db_action(change)
        if db_action == 'insert' or db_action == 'update':
            vlan_id, vlan_name = parse_db_update(change, Vlans)
            if f'{vlan_id}' in app_redis:
                print(f'vlan {vlan_id} in cache. Skip this db listen event')
                continue
            print(f'vlan {vlan_id} not in cache')
            vlan_comparator = Comparator(con, Vlans)
            if db_action == 'insert':
                vlan_attr_dd_ll = vlan_comparator.get_db_vlans_only() # we add on device only those vlans which exist only on DB
            elif db_action == 'update':
                vlan_attr_dd_ll = vlan_comparator.getVlanNameDiffWithDbDF() 
            con.post_vlans(vlan_attr_dd_ll)
        elif db_action == 'delete':
            # 'operationType': 'delete'
            vlan_comparator = Comparator(con, Vlans)
            vlan_attr_dd_ll = vlan_comparator.get_dev_vlans_only() # return diff after comparing between DB and Device. Old VLANs on a device should be removed
            print(f'vlans {vlan_attr_dd_ll} for removing')
            con.remove_vlans(vlan_attr_dd_ll)

if __name__ == '__main__':
    asyncio.run(main_watcher())
    """
    loop_watcher = asyncio.get_event_loop()
    try:
        loop_watcher.run_until_complete(main_watcher())
    finally:
        loop_watcher.close()
    """