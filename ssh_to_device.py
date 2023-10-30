import paramiko
import json

class ssh_to_device:
    """
    Class for defining connections to the device via SSH.
    Attributes:
        client: The SSH client as defined by the Paramiko library.
        connected: A boolean describing whether a connection has been opened.
    """
    def __init__(self):
        self.client = None
        self.connected = False
        self.cmd = ""

    def connect(self, IP_address, port=22):
        try:
            self.disconnect()
        finally:
            pass
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self.client.connect(hostname=IP_address,username='root',password='')
            self.connected = True
            return True
        except Exception as e:
            print("Unable to establish SSH connection to " + IP_address)
            print(f"Reason: {e}")
            return False

    def disconnect(self):
        if self.client:
            self.client.close()
        self.connected = False

    def execute(self, command):
        if not self.client:
            print("Client is not connected. Need to connect first.")
            return None
        stdin, stdout, stderr = self.client.exec_command(command)
        return stdout

    def collect_data(self, firmware_file, file_name = "", mode = "BASELINE"):
        cmd = f"sudo nice -n 1 python3 {firmware_file} {file_name} {mode}"
        self.cmd = cmd
        print(f"RUNNING COMMAND: `{cmd}`")
        resp = self.execute(cmd)

    def upload_firmware(self, local_firmware, remote_firmware):
        if not self.client:
            print("Client is not connected. Need to connect first.")
            return False
        try:
            ftp_client = self.client.open_sftp()
            ftp_client.put(local_firmware, remote_firmware)
            ftp_client.close()
            return True
        except Exception as e:
            print("Could not upload firmware to device")
            print(f"Reason: {e}")
            return False

    def get_device_id(self):# This is for collecting the calib.json from remote device to local
        if not self.client:
            print("Client is not connected. Need to connect first.")
            return False
        try:
            ftp_client = self.client.open_sftp()
            ftp_client.get('/home/root/calib.json','calib.json')
            ftp_client.close()
            return True
        except Exception as e:
            print(f"Could not obtain calib.json file")
            print(f"Reason: {e}")
            return False

    def download_file(self, file, dest):
        if not self.client:
            print("Client is not connected. Need to connect first.")
            return False
        try:
            ftp_client = self.client.open_sftp()
            ftp_client.get(file, dest)
            ftp_client.close()
            return True
        except Exception as e:
            print(f"Could not download file {file} to device")
            print(f"Reason: {e}")
            return False

    def delete_file(self, file):
        if not self.client:
            print("Client is not connected. Need to connect first.")
            return False
        try:
            stdin, stdout, stderr = self.client.exec_command(f"rm -rf {file}")
            return True
        except Exception as e:
            print(f"Could not delete file {file} from device")
            print(f"Reason: {e}")
            return False

    def kill_script(self):
        if not self.client:
            print("Client is not connected. Need to connect first.")
            return False
        try:
            stdin, stdout, stderr = self.client.exec_command(f'pkill -f "{self.cmd}"')
            return True
        except Exception as e:
            print("Could not kill script from device")
            print(f"Reason: {e}")
            return False