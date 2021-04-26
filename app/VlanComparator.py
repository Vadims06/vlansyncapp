import pandas as pd
import json

class Comparator:
    def __init__(self, dev_con, db_collection_con):
        self.dev_con = dev_con
        self.db_collection_con = db_collection_con
        self.device_vlan_df = self._get_device_vlan_df()
        self.db_vlan_df = self._get_db_vlan_df()
        #
        self.dev_db_vlan_df = self.deviceAndDBVlans()

    def _get_device_vlan_df(self):
        """
        dev_vlan_dd_ll = [
{'vlan_id': 1, 'name': 'default'}, 
{'vlan_id': 3, 'name': 'TEST3'}, 
{'vlan_id': 4, 'name': 'DEV_from_sw_201_NEW'}]
        """
        device_vlan_dd_ll = self.dev_con.get_vlans()
        if device_vlan_dd_ll is None:
            raise ValueError("we did not get vlans from the device. Please check connection logs.")
        device_vlan_df = pd.DataFrame(device_vlan_dd_ll)
        if device_vlan_df.empty:
            device_vlan_df = pd.DataFrame(columns = ['vlan_id', 'name'])
        return device_vlan_df
    
    def _get_db_vlan_df(self):
        """
        db_vlan_dd_ll = [
{'vlan_id': 1, 'name': 'default'}, 
{'vlan_id': 2, 'name': 'TEST33'}, 
{'vlan_id': 4, 'name': 'DEV_from_sw_201'}]
        """
        db_vlan_dd_ll = self.db_collection_con.objects.get_db_vlan_dd_ll()
        db_vlan_df = pd.DataFrame(db_vlan_dd_ll)
        if db_vlan_df.empty:
            db_vlan_df = pd.DataFrame(columns = ['vlan_id', 'name'])
        return db_vlan_df
    def deviceAndDBVlans(self):
        return pd.merge(self.device_vlan_df, self.db_vlan_df, on=['vlan_id'], how='outer', indicator='dev_db_diff', suffixes=('_dev', '_db'))
    
    def get_dev_vlans_only(self):
        """
        name_dev  vlan_id name_db dev_db_diff
         TEST3        3     NaN   left_only
        """
        dev_vlans_only_df = self.dev_db_vlan_df.query('dev_db_diff == "left_only"')
        dev_vlans_only_df = dev_vlans_only_df.rename(columns={'name_dev': 'name'})
        return json.loads(dev_vlans_only_df.to_json(orient='records'))
    
    def get_db_vlans_only(self):
        """
          name_dev  vlan_id name_db dev_db_diff
            NaN        2    TEST33  right_only
        """
        db_vlans_only_df = self.dev_db_vlan_df.query('dev_db_diff == "right_only"')
        db_vlans_only_df = db_vlans_only_df.rename(columns={'name_db': 'name'})
        return json.loads(db_vlans_only_df.to_json(orient='records'))

    def getVlanNameDiffWithDbDF(self):
        # when we received DB watch event - we rely on DB info
        dev_and_db_vlan_for_updates_df = pd.merge(self.device_vlan_df, self.db_vlan_df, on=['vlan_id', 'name'], how='right', indicator='dev_db_diff') # we can update only those vlans which has already exists in DB
        not_updated_vlans_on_db = dev_and_db_vlan_for_updates_df.query('dev_db_diff == "right_only"')
        return json.loads(not_updated_vlans_on_db.to_json(orient='records'))
    
    def getVlanNameDiffWithDeviceDF(self):
        # when we received SNMP trap - we rely on device info
        dev_and_db_vlan_for_updates_df = pd.merge(self.device_vlan_df, self.db_vlan_df, on=['vlan_id', 'name'], how='left', indicator='dev_db_diff')
        not_updated_vlans_on_db = dev_and_db_vlan_for_updates_df.query('dev_db_diff == "left_only"')
        return json.loads(not_updated_vlans_on_db.to_json(orient='records'))