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
		sleep(10)
		pulseCode="$hb "+str(pulseSequence)
		sockClient.send(pulseCode.encode())
		print("[i]\tsending heartbeat("+pulseCode+")")
		pulseSequence+=1
		
def connectServer(hostIp,hostPort):
	sockClient=socket.socket()
	sockClient.connect((hostIp,hostPort))
	
	print("[i]\tconnected. going into loop to preserve connection. ctrl+c to abort")
	
	threadPulse=threading.Thread(target=maintainPulse,args=(sockClient,))
	threadPulse.start()
	
	while(True):
		
		sockBuffer=sockClient.recv(2048).decode()
		if(sockBuffer):
			match sockBuffer:
				case '$req-ident':
					print("[i]\treceived req-ident, sending json package");
					sockClient.send(encodeIdentPackage(buildIdentPackage()).encode())
				case '$ack-ident':
					print("[i]\treceived ack-ident");
				case _:
					print("[i]\tdata received:",sockBuffer);
	
print("[i]\tattempting to connect to",defaultHost+":"+str(defaultPort))
connectServer(defaultHost,defaultPort)
