import os
import subprocess
import re
from typing import List
from datetime import datetime
import pathlib

storage_path = "./.smartctl-notifier-storage"
email_credential_path = storage_path+"/email_credential"
email_credentials = []

class Device:
    def __init__(self, path:str) -> None:
        self.path = path
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
            if "nvme" in self.path:
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
        attr = run_command(['/usr/sbin/smartctl', '--attributes', self.path])
        self.set_attributes(attr)

    def find_value_after_separation(self, string:str, separation_num:int):
        separation_end_indexes = []
        in_separation_now = False
        for char_id in range(len(string)):
            if string[char_id] == " ":
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
        
        info = run_command(['/usr/sbin/smartctl', '-i', self.path])
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
    smartctl_scan_output = run_command(['/usr/sbin/smartctl', '--scan'])
    devices = []
    for line in smartctl_scan_output:
        match = re.search(r'(/dev/\S+)', line)
        if match:
            device_string = match.group(1)
            print(f"found {device_string}")
            devices.append(Device(device_string))
        else:
            print(f"Device {device_string} string not found.")
        
    return devices

def write_last_nofy_alive_date(filename):
    with open(filename, 'a') as file:
        dt = datetime.now().strftime("%Y.%m.%d-%H.%M.%S")
        file.write(f"{dt}\n") # Write the text to the file

def get_last_nofy_alive_date(filename) -> datetime:
    try:
        with open(filename, 'r') as file:
            content = file.read().strip()  # Read entire content and strip any extra whitespace
            if not content:
                return "No previous value"  # Handle case where file is empty
            strings = content.split('\n')  # Split content into strings
            last_string = strings[-1]  # Get the last string
            date_format = "%Y.%m.%d-%H.%M.%S"
            converted_date = datetime.strptime(last_string, date_format)
            return converted_date
    except FileNotFoundError:
        print(f"Last notify date file {filename} not found")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None
    
def get_last_attribute_value(filename) -> str:
    try:
        with open(filename, 'r') as file:
            content = file.read().strip()  # Read entire content and strip any extra whitespace
            if not content:
                return "No previous value"  # Handle case where file is empty
            strings = content.split('\n')  # Split content into strings
            last_string = strings[-1]  # Get the last string
            return last_string.split(':', 1)[1].strip()
    except FileNotFoundError:
        print(f"Attribute file {filename} not found")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None
    


def send_email(subject:str, text:str):
    print("Sending email")
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    creds = get_email_credentials()
    # Email configuration
    sender_email = creds[0]
    receiver_email = sender_email
    password = creds[1]
    
    # Create message container - the correct MIME type is multipart/alternative.
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = receiver_email

    # Turn these into plain/html MIMEText objects
    part1 = MIMEText(text, 'plain')
    # Attach parts into the message container
    msg.attach(part1)
    # Send the email (assuming SMTP server is configured)
    try:
        with smtplib.SMTP_SSL('smtp.mail.ru', 465) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email. Error: {str(e)}")

def check_requirements():
    pathlib.Path(storage_path).mkdir(parents=True, exist_ok=True)
    if not os.path.exists(email_credential_path):
        open(email_credential_path, 'a').close()
        print(f"File '{email_credential_path}' created successfully")
        exit()
    _ = get_email_credentials()
        
def get_email_credentials():
    email_credentials = read_file(email_credential_path)
    if len(email_credentials) < 2:
        print(f"File '{email_credential_path}' credentials doesn't contain two lines")
        exit()
    return email_credentials
    
warning_attributes = ["Critical Warning", "Percentage Used", 
                    "Available Spare", "Unsafe Shutdowns", 
                    "Warning", "Critical",
                    "Reallocate_NAND_Blk_Cnt",
                    "Program_Fail_Count", "Erase_Fail_Count",
                    "Unexpect_Power_Loss_Ct","Error_Correction_Count",
                    "Reported_Uncorrect", "Reallocated_Event_Count",
                    "Current_Pending_ECC_Cnt", "Offline_Uncorrectable",
                    "UDMA_CRC_Error_Count", "Percent_Lifetime_Remain",
                    "Write_Error_Rate", ]

                     
              
def check_devices(devices:List[Device]):
    last_notify_path = f"{storage_path}/last-notify"
    last_notify_date = get_last_nofy_alive_date (last_notify_path)
    if last_notify_date:
        time_diff_hours = (datetime.now() - last_notify_date).total_seconds() / 3600
    else:
        time_diff_hours = None
    
    if time_diff_hours and time_diff_hours > 24:
        send_email("Smartctl notifier alive email message", "Smartctl notifier alive email message")
        write_last_nofy_alive_date(last_notify_path)
 

    for dev in devices:
        dev_stor_path = f'{storage_path}/{dev.get_device_file_name()}'
        pathlib.Path(dev_stor_path).mkdir(parents=True, exist_ok=True)
        changed_attributes = []
        changed_warning_attributes = []
        for attr in dev.get_attributes():
            filename = f"{dev_stor_path}/{attr[0]}"
            last_value = get_last_attribute_value(filename)
            
            if last_value and last_value != attr[1]:
                if any(value in attr[0] for value in warning_attributes):
                    changed_warning_attributes.append((attr[0],last_value, attr[1]))
                else:
                    changed_attributes.append((attr[0],last_value, attr[1]))
                    
            with open(filename, 'a') as file:
                dt = datetime.now().strftime("%Y.%m.%d-%H.%M.%S")
                file.write(f"{dt}:  {attr[1]}\n") # Write the text to the file
              
        message = ""  
        if len(changed_warning_attributes)>0:
            msg = f"WARNING Device {dev.path} ERROR attributes have changed ! ! !"
            print (msg) 
            message += msg + '\n' 
            for attr in changed_warning_attributes:
                msg = f"Attribute {attr[0]} has changed from {attr[1]} to {attr[2]}"
                print (msg) 
                message += msg + '\n'  
            send_email("WARNING", message)       
                
        elif len(changed_attributes)>0:
            print(f"Device {dev.path} attributes have changed:")
            for attr in changed_attributes:
                print (f"Attribute {attr[0]} has changed from {attr[1]} to {attr[2]}")   
            

def main():
    devices = get_devices()
    check_requirements()
    check_devices(devices)

def test():   
    check_requirements()
    
    dev_hdd = Device('test')
    dev_hdd._Device__filename = "test1"
    dev_hdd.set_attributes(read_file('attributes-example.txt'))
    dev_hdd_val1 = dev_hdd.get_attributes()
    dev_hdd_val = dev_hdd.get_attribute('cels')
    
    dev_nvme = Device('nvme')
    dev_nvme._Device__filename = "test2"
    dev_nvme.set_attributes(read_file('attributes-example-nvme.txt'))
    dev_nvme_val1 = dev_nvme.get_attributes()
    dev_nvme_val = dev_nvme.get_attribute('cels')
    
    dev_list =[dev_hdd, dev_nvme]
    check_devices(dev_list)
    

if __name__ == "__main__":
    #test()
    main()
    

    
