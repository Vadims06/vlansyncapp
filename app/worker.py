import time

def runTask(vlan_id):
    print(f'starting runTask. Received: {vlan_id}') # in place of actual logging
    
    time.sleep(15) # simulate long running task
    print('finished runTask')
    return {vlan_id: 'task complete'}