#!/usr/bin/python3

# GENERAL IMPORTS
import os
import base64
import config

# NETMIKO
from netmiko import ConnectHandler


class execConfigure:

    async def execConf(request, hosts, file):

        ###################
        # BACKEND
        blacklistHosts = os.path.join(config.blackListFile)  # Blacklist from config.py
        ############################

        # Setting standard Request Message
        responseData = []

        # READ THE DATA FROM FILE
        configurationFileContentBytes = await file.read()
        confugrationFileContent = configurationFileContentBytes.decode('utf-8')

        if confugrationFileContent == '':
            raise Exception('No configuration file found.')

        for host in hosts:

            # CHECK IF PASSWORD IS BASE64
            try:
                base64.b64encode(base64.b64decode(host['password'])) == host['password']
            except Exception:
                return {'success': False, 'host': host['host'], 'software': host['device_type'], 'output': 'Password has to be encoded with base64 before process.'}

            with open(blacklistHosts, 'r') as blacklist:
                try:
                    if host['host'] not in blacklist.read():

                        # CHECK THAT ALL KEYS ARE IN DATA
                        if all(key in host for key in ('username', 'password', 'device_type', 'port', 'host')):

                            # CREATE AND SAVE FILE LOCALY
                            savePath = os.path.dirname(__file__) + file.filename
                            with open(savePath, "w") as temp_file:
                                temp_file.write(confugrationFileContent)

                            # CONNECTION DATA
                            connectData = {
                                'device_type': host['device_type'],
                                'host': host['host'],
                                'username': host['username'],
                                'password': base64.b64decode(host['password']).decode('ascii'),
                                'port': host['port']
                            }

                            try:
                                # OPERATION
                                net_connect = ConnectHandler(**connectData)
                                response = net_connect.send_config_from_file(config_file=savePath)
                                net_connect.disconnect()
                                responseData.append({'success': True, 'host': host['host'], 'software': host['device_type'], 'output': response})

                            except Exception as error_message:
                                info = str(error_message)
                                print(host['host'] + " - " + info)
                                responseData.append({'success': False, 'host': host['host'], 'output': info})

                            # Close and remove file.
                            os.remove(savePath)

                        else:
                            responseData.append({'success': False, 'host': host['host'], 'output': 'Missing data in request.'})
                    else:
                        responseData.append({'success': False, 'host': host['host'], 'output': 'Host blacklisted.'})

                except Exception as error_message:
                    info = str(error_message)
                    print(host['host'] + " - " + info)
                    responseData.append({'success': False, 'host': host['host'], 'output': info})

        return responseData
