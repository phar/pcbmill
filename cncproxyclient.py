#!/usr/bin/python3
#import linuxcnc
import socket
import struct
import json
import time
#self.cncc = linuxcnc.command()
#self.cncs = linuxcnc.stat()


TCP_IP = "127.0.0.1"
TCP_PORT = 5005
BUFFER_SIZE = 1024

DEBUG = 1

class linuxCNCBridge():
	def __init__(self, host, port):
		self.host = host
		self.port = port
		self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.s.connect((self.host, self.port))

	def get_response(self):
		t = self.s.recv(struct.Struct(">L").size)
		r1 = struct.unpack(">L",t)[0]
		r2 = json.loads(self.s.recv(r1))
		if DEBUG:
			print("RECV: %s" % r2)
		return r2

	def send_command(self, cmd,args = {}):
		if DEBUG:
			print("SEND: %s" % cmd)
		cmdict ={"cmd":cmd}
		cmdict.update(args)
		c = json.dumps(cmdict)
		self.s.send(struct.pack(">L", len(c)) + bytes(c,'utf-8'))
		return self.get_response()
	


if __name__ == "__main__":
	cb = linuxCNCBridge(TCP_IP,TCP_PORT);

	
	cb.send_command("hello world")
	cb.send_command("GETPOS")
	cb.send_command("HOMEMILL")
	cb.send_command("GETPOS")


