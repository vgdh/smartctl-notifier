import os
import subprocess
import re
from typing import List


class Device:
    def __init__(self, path:str) -> None:
        self.__path = path
        self.__attributes = None
        self.__filename = None

    def set_attributes(self, attribuses:list):
        if self.__attributes is None:
            self.__attributes = []
            
        attr_started = False
        for attr in attribuses:
            if 'ID# ATTRIBUTE_NAME' in attr or 'SMART/Health Information' in attr:
                    attr_started = True
                    continue
            if attr_started is False or len(attr) < 5:
                continue
            self.__attributes.append(attr.strip())
    
    def get_attributes(self):
        if self.__attributes is None:
            self.update_attributes()
        for_return = []
        for attr in self.__attributes:
            name = None
            value = None
            if "nvme" in self.__path:
                name = attr.split(':', 1)[0].strip()
                value = attr.split(':', 1)[1].strip()
            else:
                match = re.search(r'\b\d+\s+(.*?)\s+', attr)
                name = match.group(1).strip()
                value = self.find_value_after_separation(attr,9)
                
            for_return.append((name,value))
            
        return for_return
    
    def find_first_occurrence(self, strings:list, substring:str):
        for string in strings:
            if substring.lower() in string.lower():
                return string
        return None 

    def update_attributes(self):
        attr = run_command(['smartctl', '--attributes', self.__path])
        self.set_attributes(attr)

    def find_value_after_separation(self, string:str, separation_num:int):
        separation_end_indexes = []
        in_separation_now = False
        for char_id in range(len(string)):
            if string[char_id] is " ":
                in_separation_now = True
            elif in_separation_now is True:
                in_separation_now = False
                separation_end_indexes.append(char_id)

        return string[separation_end_indexes[separation_num-1]:] 


    def get_attribute(self, attribute:str) -> str:
        if attribute is None:
            self.update_attributes()
        
        return self.find_first_occurrence(self.__attributes, attribute)

    def get_device_file_name(self):
        if self.__filename:
            return self.__filename 
        
        info = run_command(['smartctl', '-i', self.__path])
        name = None
        sn = None
        for line in info:
            # Define regular expressions for model number and serial number
            model_pattern = r"(Model Number|Device Model):\s+([^\n]+)"
            serial_pattern = r"Serial Number:\s+([^\n]+)"

            # Search for model number and serial number
            model_match = re.search(model_pattern, line)
            serial_match = re.search(serial_pattern, line)
            
            # Extract values if found
            model_number = model_match.group(2).strip() if model_match else None
            serial_number = serial_match.group(1).strip() if serial_match else None
            
            if model_number:
                name = model_number
            if serial_number:
                sn = serial_number

        self.__filename = f"{name} - {sn}"
        return self.__filename
        

def run_command(command_and_args:list) -> list:
    result = subprocess.run(command_and_args, capture_output=True, text=True, check=True)
    output_lines = result.stdout.strip().split('\n')
    return output_lines
 
    
def read_file(path:str):
    with open(path, 'r') as file:
        return file.read().splitlines()



def get_devices() -> List[Device]:
    smartctl_scan_output = run_command(['smartctl', '--scan'])
    devices = []
    for line in smartctl_scan_output:
        match = re.search(r'(/dev/\S+)', line)
        if match:
            device_string = match.group(1)
            print(f"found {device_string}")
            devices.append(Device(device_string))
        else:
            print("Device string not found.")
        
    return devices


def main():
    devices = get_devices()
    for dev in devices:
        dev_stor_path = f'./{dev.get_device_file_name()}'
        if os.path.exists (dev_stor_path) is False and os.path.isdir(dev_stor_path) is False:
            os.mkdir(dev_stor_path)
        for attr in dev.get_attributes():
            with open(f"{dev_stor_path}/{att}", 'a') as file:
                # Write the text to the file
                file.write(text_to_append + '\n')
        
        
    dev_hdd = Device('test')
    dev_hdd.set_attributes(read_file('attributes-example.txt'))
    dev_hdd_val = dev_hdd.get_attribute('cels')
    dev_hdd_val1 = dev_hdd.get_attributes()
    
    dev_nvme = Device('nvme')
    dev_nvme.set_attributes(read_file('attributes-example-nvme.txt'))
    dev_nvme_val1 = dev_nvme.get_attributes()
    dev_nvme_val = dev_nvme.get_attribute('cels')
    
    print (devices)


if __name__ == "__main__":
    main()

    
