#import linuxcnc
import socket
import select
import json
import struct
import time
import select, socket, sys
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(('localhost', 5005))
server.listen(5)

try:
	import linuxcnc
except:
	print("cant load cnc libs..  things may not go well")

inputs = [server]
outputs = []

def process_command(cmd):
	ret =  {"status":"NOP"}
	
	if cmd['cmd'] == 'GCODE':
		ret =  {"status":"OK"}
	
	else:
		ret =  {"status":"NO SUCH COMMAND"}



	ret = bytes(json.dumps(ret), 'utf-8')

	return struct.pack(">L", len(ret)) + ret
	
	
while inputs:
	readable, writable, exceptional = select.select(inputs, inputs, inputs)
	
	for s in readable:
		if s is server:
			connection, client_address = s.accept()
			inputs.append(connection)
		else:
			try:
				r1 = struct.unpack(">L", s.recv(struct.Struct(">L").size))[0]
				r2 = s.recv(r1)
				r2 = json.loads(r2)
				s.send(process_command(r2))
			except:
				inputs.remove(s)
				s.close()
				continue
		
	for s in exceptional:
		inputs.remove(s)
		s.close()
