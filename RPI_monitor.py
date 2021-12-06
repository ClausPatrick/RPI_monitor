import subprocess
from subprocess import Popen, PIPE
import sys
import os
from datetime import datetime
import heart_beat_mailer as hbm
import json
import logging

logging.basicConfig(filename='RPI_heartbeat.log',  level=logging.DEBUG, format='%(asctime)s %(levelname)s %(funcName)s:%(lineno)d %(message)s', datefmt='%Y/%m/%d %H:%M:%S')



class Session():
    def __init__(self):
        self.hostname = self.who_am_i()
        self.active = False # Assumption. Becomes True if there is already a test result (uptime) saved once it is read out.
        #print(f'I am {self.hostname}')
        try: 
            with open('hostlist.json', 'r') as f:
                host_list = json.loads(f.read())
        except FileNotFoundError:
            print('''
                    Expecting a hostlist, a dictionary with the following key/value items:
                    {
                        "somehost" : "192.168.0.11",
                        "someotherhost" : "192.168.0.111",
                        "soverymanyhosts" : "192.168.0.110"
                    }

                    Terminating now.

                ''')
            exit()

        self.active_list = (host for host in host_list if host != self.hostname) # Iterator with all Hosts excluding ourself.
        self.uptime_dict_actual = {}
        for ix, host in enumerate(self.active_list):
            #print('checking host: ', {ix}, {host}, {host_list[host]})
            ip = host_list[host]
            actual_uptime = self.read_uptime(ip)
            #print(f'actual_uptime {actual_uptime}')
            conn = '0'
            if actual_uptime:
                conn = '1' # uptime_dict_actual will be logged later on should this run for the furst time.
            self.uptime_dict_actual[str(ix)] = {'name' : host, 'ip' : ip, 'uptime' : actual_uptime, 'connected' : conn, 'error_count' : '0', 'total_error' : '0', 'reboot_count' : '0'}


        try:
            with open('HeartBeatUptime.log', 'r') as f:
                self.uptime_dict_previous = json.loads(f.read())
                #print(f'Reading uptime logs: {self.uptime_dict_previous} \n')
            self.active = True

        except (json.decoder.JSONDecodeError, FileNotFoundError) as e:
            self.active = False
            self.json_output(self.uptime_dict_actual)
            #print(f'Creating file log: HeartBeatUptime at {os.getcwd()}')
            logging.info(f'No Uptime Log file found. Creating file heart_beat_logs at {os.getcwd()}')

    def json_output(self, data):
        with open('HeartBeatUptime.log', 'w') as f:
            json.dump(data, f)
            
    def who_am_i(self):
        whats_my_name = Popen(['hostname'], stdout=PIPE)
        #whats_my_name = 'deepspace9'
        return whats_my_name.communicate()[0].decode('utf-8').strip()
        #return whats_my_name

    def get_timestamp(self):
        now = datetime.now()
        date_time = str(now.strftime("%Y-%m-%d %H:%M:%S"))
        return date_time
    
    def ping(self, ip):
        command = ["ping", "-c", "1", "-w2", ip]
        response = subprocess.run(args=command, stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL).returncode == 0
        if response == 0:
            logging.warning(f'Ping not returned from {ip}')
        return response                 

    def read_uptime(self, IP):
        HOST = IP # Backwards compability to previous code.
        COMMAND = 'dmesg -T | tail -1'
        received_string = ''


        if self.ping(IP):
            ssh = Popen(['ssh', HOST, COMMAND], 
                shell=False,
                stdout=PIPE,
                stderr=PIPE)
            result = ssh.stdout.readlines()
            if result == []:
                error = ssh.stderr.readlines()
                print(sys.stderr, error)
                logging.warning('No response from SSH: {sys.stderr}, {error}')
            else:
                received_string = result[0].decode('utf-8').split(']')[0][1:] # Converting to Mon Nov 26 10:45:12 2022 format string
            return received_string
        else:
            return 0

    def check(self):
        if self.active: # Active means the Uptime log file was already created and the actual read Uptime can be compared to previous values.
            overwrite_required = False
            for host_ixi, host in enumerate(self.uptime_dict_actual):
                host_ix = str(host_ixi)
                prev = self.uptime_dict_previous[host_ix]['uptime']
                actu = self.uptime_dict_actual[host_ix]['uptime']
                was_up = int(self.uptime_dict_previous[host_ix]['connected'])
                current_error_count = int(self.uptime_dict_previous[host_ix]['error_count'])
                #print(f'Previous uptime: {prev}, Actual uptime: {actu}')
                if actu == 0:
                    print(f"Link dead for {host_ixi}: {self.uptime_dict_actual[host_ix]['name']}@{self.uptime_dict_actual[host_ix]['ip']}")
                    logging.warning(f"Link dead for {host_ixi}: {self.uptime_dict_actual[host_ix]['name']}@{self.uptime_dict_actual[host_ix]['ip']}")
                    current_error_count += 1
                    self.uptime_dict_actual[host_ix]['error_count'] = current_error_count
                    overwrite_required = True
                    self.uptime_dict_actual[host_ix]['uptime'] = prev
                    self.uptime_dict_actual[host_ix]['connected'] = '0'
                    
                    if was_up:
                        now = self.get_timestamp()
                        #print('Link was up but went down.')
                        message = f"Link was up but went down: {host_ixi}: {self.uptime_dict_actual[host_ix]['name']}@{self.uptime_dict_actual[host_ix]['ip']}"
                        logging.warning(message)
                        hbm.notify(1, f' LINK FAILURE {self.uptime_dict_previous[host_ix]["name"]}', now + message)

                else:
                    if prev == 0 or was_up == 0: # Link is restored.
                        now = self.get_timestamp()
                        total_so_far = int(self.uptime_dict_previous[host_ix]['total_error'])
                        self.uptime_dict_actual[host_ix]['total_error'] = str(current_error_count + total_so_far)
                        self.uptime_dict_actual[host_ix]['error_count'] = '0'
                        self.uptime_dict_actual[host_ix]['connected'] = '1'
                        overwrite_required = True
                        message = f"Link came back for {host_ixi}: {self.uptime_dict_previous[host_ix]['name']}@{self.uptime_dict_previous[host_ix]['ip']}, after {total_so_far} failures."
                        #print(message)
                        logging.info(message)
                        hbm.notify(0, f'LINK RESTORED {self.uptime_dict_previous[host_ix]["name"]}', now + message)

                    elif actu == prev:
                        pass
                        #print('All same')
                    else:
                        now = self.get_timestamp()
                        reboot_count_so_far = int(self.uptime_dict_previous[host_ix]['reboot_count'])
                        self.uptime_dict_actual[host_ix]['reboot_count'] =   str(reboot_count_so_far + 1)
                        message1 = f"Uptime difference on {host_ixi}: {self.uptime_dict_previous[host_ix]['name']}@{self.uptime_dict_previous[host_ix]['ip']}. "
                        message2 = f"-Timestamps: {self.uptime_dict_previous[host_ix]['uptime']} - {self.uptime_dict_actual[host_ix]['uptime']}"
                        #print(message1)
                        #print(message2)
                        logging.info(message1)
                        logging.info(message2)

                        overwrite_required = True
                        hbm.notify(1, ' DEVICE REBOOT', now + message1 + message2)


            if overwrite_required:
                self.json_output(self.uptime_dict_actual)
                logging.info(f'Overwriting Uptime data in file heart_beat_logs at {os.getcwd()}')

#some comment
if __name__ == "__main__":
    s = Session()
    s.check()
