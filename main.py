import subprocess
import re


class Device:
    def __init__(self, path:str) -> None:
        self.path = path
        self.attributes = None

    def find_first_occurrence(self, strings:list, substring:str):
        for string in strings:
            if substring.lower() in string.lower():
                return string
        return None 

    def update_attributes(self):
        attr = run_command(['smartctl', '--attributes', self.path])

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
        
        found = self.find_first_occurrence(self.attributes, attribute)
        
        if "nvme" in self.path:
            return self.find_value_after_separation(found,1)
        else:
            return self.find_value_after_separation(found,9)

        

def run_command(command_and_args:list) -> list:
    result = subprocess.run(command_and_args, capture_output=True, text=True, check=True)
    output_lines = result.stdout.strip().split('\n')
    return output_lines
 
    
def read_file(path:str):
    with open(path, 'r') as file:
        return file.read().splitlines()


    
    

def get_devices():
    smartctl_scan_output = run_command(['smartctl', '--scan'])
    #smartctl_scan_output = read_file('scan-example.txt')

    devices = []
    for line in smartctl_scan_output:
        match = re.search(r'^([^ ]+)', line)
        if match:
            device_string = match.group(1)
            print(f"found {device_string}")
            devices.append(device_string)
        else:
            print("Device string not found.")
    return devices

def main():
    devices = get_devices()

    dev_hdd = Device('test')
    dev_hdd.attributes = read_file('attributes-example.txt')
    dev_hdd_val = dev_hdd.get_attribute('cels')

    dev_nvme = Device('nvme')
    dev_nvme.attributes = read_file('attributes-example-nvme.txt')
    dev_nvme_val = dev_nvme.get_attribute('cels')
    
    print (devices)

# Example usage:
if __name__ == "__main__":
    main()

    
