'''
Created on Aug 18, 2017
'''
import paramiko
import subprocess
import platform
import socket
import time
import random
import os
import datetime
import threading

class ssh:
    
    def __init__(self, ip, username, password, enablePassword=None):
        self.ip = socket.gethostbyname(ip) #  if name=ipaddress format (ex 127.0.0.1) then it will just return the address format :)
        self.username = username
        self.password = password
        self.connection = None
        self.ePassword = enablePassword
    
    def createConection(self):
        if self.__checkIP(self.ip):
            if self.__checkCred(self.username, self.password):
                pass
            else:
                raise self.SSHException
        else:
            raise Exception('IPError')
        if self.connect():
            return True
        else:
            raise Exception("Weird SSH Exception")

    def __checkCred(self, u, p):  #
            try:
                print("\nTesting access to: ", str(self.ip))
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(self.ip, username=u, password=p, timeout=10)
                ssh.close()
                return True
            except Exception as e:
                self.SSHException = e
                return False  # username or password are incorrect 

    def __checkIP(self, ip):
        """
        Returns True if host responds to a ping request
        """
        if platform.system().lower() == "windows":
            ping_str = "-n 2"
        else: 
            ping_str = "-c 2"
        args = "ping " + " " + ping_str + " " + ip
        if  platform.system().lower() == "windows":
            need_sh = False  
        else: 
            True
        # Ping
        if subprocess.run(args, shell=need_sh).returncode == 0:
            return True
        else:
            return False

    def connect(self):
        try:
            print("\nTrying to connect...")
            time.sleep(random.random()*3)
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy()) 
            ssh.connect(self.ip, username=self.username, password=self.password, timeout=10)
            self.connection = ssh
            print("Successfully connected to "+ str(self.ip)+"\n")
            return True
        except Exception as e: 
            self.__errLogging(self.ip,str(e))
            raise e
          
    def runCommand(self, commands, readyToSendFlag="#"): # you get one shot at running these commands if the shell is closed you will need to open a new channel/session
        try:
            if self.connection != None:
                c = self.connection
                shell = c.invoke_shell()
                output=str(shell.recv(9999))
                if ">" in output and self.ePassword is not None:
                    cmds = commands
                    cmds.insert(0,str(self.ePassword))
                    cmds.insert(0,"enable")
                elif ">" in output and self.ePassword is None and ">" not in readyToSendFlag:
                    cmds = commands
                    cmds.insert(0,"enable")
                else:
                    cmds = commands
                logOutput = [[],commands]
                for cmd in cmds:
                        while True:
                            if True:
                                sentBytes = shell.send(str(cmd + '\n'))
                                if len(str(cmd + '\n').encode('utf-8')) == sentBytes:
                                    if (self.ePassword is not None) or (str(self.ePassword) not in str(cmd)):
                                        print('Running: ', cmd)
                                    while True:
                                        output = str(shell.recv(9999))
                                        logOutput[0].append(output)
                                        if readyToSendFlag in output or "ssword:" in output: # i am using "#" to notify the script that it is ready for more input; Change as needed. Password: provides legacy support to enable the user account on cisco equipment
                                            break
                                        else:
                                            time.sleep(.5)
                                    break
                                else:
                                    raise('Dropped Commands Exception')
                self.__stdLogging(self.ip, logOutput)
                shell.close()
                return True
            elif self.connect():
                self.runCommand(commands)
                self.close()
            else:
                raise Exception('SSH RunCmd Exception')
        except Exception as e:
            self.__errLogging(self.ip,str(e))
            raise e
        
    def getStreams(self, command):
        try:
            if self.connection != None:
                c = self.connection
                print('Expecting Output from: ', command)
                self.__stdLogging(self.ip, [str('Expecting Output from: '+command)])
                return c.exec_command(command)  # returns 3 file-like streams stin, stout, sterr 
            elif self.connect():
                return self.getStreams(command)  # returns 3 file-like streams stin, stout, sterr 
                self.close()
            else:
                raise Exception('SSH Stream Exception')
        except Exception as e:
            self.__errLogging(self.ip,str(e))
            raise e

    def continuousShell(self, cmd, ty='cisco', mode='c', readyToSendFlag="#"):
        try:
            if self.connection != None:
                c = self.connection
                shell = c.invoke_shell()
                if ty is 'cisco':
                    shell.send(str('term length 0\n'))
                #open tread
                t = threading.Thread(target=self.__continueShell_inputManager)
                t.daemon = False
                t.start()
                shell.send(str('\n'))
                shell.recv(1)
                while t.is_alive():
                    os.system('cls')
                    shell.send(str(cmd)+'\n')
                    print(str(shell.recv(9999).decode('utf-8')).replace("\"", '').replace("'", '').replace('[','').replace(']','').replace('\\n','\n').replace('\\r','\r')+'\n')
                    time.sleep(1.5)
        except Exception as e:
            self.__errLogging(self.ip,str(e))
            raise e

    def __continueShell_inputManager(self):
            input()

    def close(self):  # make sure to close the connection when done
        if self.connection != None:
            self.connection.close()
            self.connection = None
            return True
        else:
            return False
        
    def __stdLogging(self,ip,data):
        directory = "./Debug_Logs"
        if not os.path.exists(directory):
            os.makedirs(directory)
        with open(str(directory)+'/{0}_Distribution_{1}.txt'.format(ip,str(datetime.datetime.fromtimestamp(19800801).strftime('%m%d'))),'a') as file:
            if len(data) != 0:
                file.write('\n\n\nLog Time: {0}\n\n'.format(str(datetime.datetime.today())))
                for i in data:
                    if type(i) is str:
                        file.write((str(i).replace("\"", '').replace("'", '').replace('[','').replace(']','').replace('\\n','\n').replace('\\r','\r')+'\n'))
                    else:
                        hold = None
                        for j in i:
                            if (len(j.replace('b','')) == 1) and (hold is None):
                                hold = j.replace('b','')
                            else:
                                file.write((str(j).replace("\"", '').replace("'", '').replace('[','').replace(']','').replace('\\n','\n').replace('\\r','\r')+'\n'))
                            if hold != None:
                                file.write((hold+str(j).replace("\"", '').replace("'", '').replace('[','').replace(']','').replace('\\n','\n').replace('\\r','\r')+'\n'))
                                hold = None

            file.close()

    def __errLogging(self,ip,data):
        directory = "./Error_Logs"
        if not os.path.exists(directory):
            os.makedirs(directory)
        with open(str(directory)+'/Error_{0}_Distribution_{1}.txt'.format(ip,str(datetime.datetime.fromtimestamp(19800801).strftime('%m%d'))),'a') as file:
            if len(data) != 0:
                file.write('\n\n\nLog Time: {0}\n\n'.format(str(datetime.datetime.today())))
                file.write((str(data)+'\n'))
            file.close()
