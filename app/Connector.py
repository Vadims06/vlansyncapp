from scrapli.driver.core import IOSXEDriver
from scrapli.helper import textfsm_parse
from scrapli.exceptions import * # 'CouldNotAcquirePrivLevel', 'KeyVerificationFailed', 'MissingDependencies', 'ScrapliAuthenticationFailed', 'ScrapliCommandFailure', 'ScrapliException', 'ScrapliKeepaliveFailure', 'ScrapliTimeout', 'TransportPluginError', 'UnknownPrivLevel'
from config import Device


class Connector:
    def __init__(self):  
        self._scrapli_device = {
            "host": Device.NET_DEVICE_HOST,
            "auth_username": Device.NET_DEVICE_USERNAME,
            "auth_password": Device.NET_DEVICE_PASSWORD,
            "auth_strict_key": False,
        }
    '''
    def _scrapli_open(self):
        try:
            self.device = self._scrapli_device.open()
            return self.device
        except ScrapliAuthenticationFailed:
            print("Authentication connection failed to {}".format(self._scrapli_device.host))
        except ScrapliTimeout:
            print("Connection timeout to {}".format(self._scrapli_device.host))
    
    def _scrapli_close(self):
        if getattr(self, "_scrapli_device", None):
            self._scrapli_device.close()
            self._scrapli_device = None
        self.scrapli_device = None
        self.device = None
   
    def __enter__(self):
        """Open a connection to the device."""
        self.device = self._scrapli_open()

    def __exit__(self):
        self._scrapli_close()
    '''
    def get_vlans(self):
        """
        return a list of vlans if connection is sucessful or None
        """
        try:
            with IOSXEDriver(**self._scrapli_device) as conn:
                if conn:
                    response = conn.send_command("show vlan")
                    structured_result = textfsm_parse("./textfsm/cisco_ios_show_vlan.tpl", response.result)
                    '''
                    structured_result = [
                        {'vlan_id': '1', 'name': 'default', 'status': 'active', 'interfaces': ['Et0/1', 'Et0/2', 'Et3/2', 'Et3/3']}, 
                        {'vlan_id': '1002', 'name': 'fddi-default', 'status': 'act/unsup', 'interfaces': []}]
                    '''
                    for vlan_attr_dd in structured_result:
                        vlan_attr_dd['vlan_id'] = int(vlan_attr_dd['vlan_id'])
                    return structured_result
        except ScrapliAuthenticationFailed as e:
            print(e)
        except ScrapliTimeout  as e:
            print(e)
    
    def post_vlans(self, vlans_attr_dd_ll):
        try:
            with IOSXEDriver(**self._scrapli_device) as conn:
                if conn:
                    response = conn.send_command("conf t")
                    if not isinstance(vlans_attr_dd_ll, list):
                        vlans_attr_dd_ll = [vlans_attr_dd_ll]
                    for vlan_attr_dd in vlans_attr_dd_ll:
                        vlan_id = vlan_attr_dd.get('vlan_id', -1)
                        name = vlan_attr_dd.get('name', '')
                        if vlan_id < 0:
                            continue
                        conn.send_command(f"vlan {vlan_id}")
                        conn.send_command(f"name {name}")
                        print(f'vlan:{vlan_id} has been added')
        except ScrapliAuthenticationFailed as e:
            print(e)
        except ScrapliTimeout  as e:
            print(e)
    
    def remove_vlans(self, vlans_attr_dd_ll):
        try:
            with IOSXEDriver(**self._scrapli_device) as conn:
                if conn:
                    response = conn.send_command("conf t")
                    if not isinstance(vlans_attr_dd_ll, list):
                        vlans_attr_dd_ll = [vlans_attr_dd_ll]
                    for vlan_attr_dd in vlans_attr_dd_ll:
                        vlan_id = vlan_attr_dd.get('vlan_id', -1)
                        if vlan_id < 0:
                            continue
                        conn.send_command(f"no vlan {vlan_id}")
                        print(f'vlan:{vlan_id} has been removed')
        except ScrapliAuthenticationFailed as e:
            print(e)
        except ScrapliTimeout  as e:
            print(e)