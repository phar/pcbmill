#!/usr/bin/python2.7
import linuxcnc
import socket
import select
import json
import struct
import time
import select, socket, sys

try:
	import linuxcnc
except:
	print("cant load cnc libs..  things may not go well")


class CNCWrapper():
	def __init__():
		pass
			
	def getPosition(self):
		pass
		
	def modeMDI(self):
		pass
		
	def MDICommand(self, command):
		pass
		
	def modeAuto(self):
		pass
	
	def setMaxVelocity(self,ipm):
		pass
		
		
class LinuxCNCWrapper(CNCWrapper):
	def __init__(self):
		#super
		self.cncs = linuxcnc.stat()
		self.cncc = linuxcnc.command()
		
	def getPosition(self):
		self.cncc.wait_complete()
		self.cncs.poll()
		(x,y,z) = self.cncs.position[:3]
		(xx,yy,zz) = self.cncs.g92_offset[:3]
		(xxx,yyy,zzz) = self.cncs.g5x_offset[:3]
		return (((x-xx) - xxx),((y-yy)-yyy),((z-zz)-zzz))


	def modeMDI(self):
		self.cncc.mode(linuxcnc.MODE_MDI)
		self.cncc.wait_complete()
		return 0
		
	def modeAuto(self):
		self.cncc.mode(linuxcnc.MODE_MANUAL)
		self.cncc.wait_complete()
		return 0
		
	def setMaxVelocity(self,ipm):
		self.cncc.maxvel(ipm)

	def _ok_for_mdi(self):
	        self.cncs.poll()
	        return not self.cncs.estop and self.cncs.enabled and self.cncs.homed and (self.cncs.interp_state == linuxcnc.INTERP_IDLE) and  (self.cncs.state == 1)

	def jogAxis(self,axis):
		if axis == 'X':
			axis = 0
		elif axis == 'Y':
			axis = 1
		elif axis == 'Z':
			axis = 2
		self.cncc.jog(linuxcnc.JOG_CONTINUOUS, axis, 20) #fixme

	def jogStop(self,axis):
		if axis == 'X':
			axis = 0
		elif axis == 'Y':
			axis = 1
		elif axis == 'Z':
			axis = 2
		self.cncc.jog(linuxcnc.JOG_STOP, axis)
	
	def MDICommand(self,cmd):
		self.cncc.mdi(cmd)
	
	def HomeMill(self):
		self.cncc.mode(linuxcnc.MODE_MANUAL)
		self.cncc.wait_complete()
		self.cncc.reset_interpreter()
		self.cncc.override_limits()

#		while not (self.cncs.axis[0]['homed'] == 0 and not self.cncs.estop and self.cncs.enabled):
#			time.sleep(1)
#			self.cncs.poll()
		self.cncc.home(0)
		self.cncc.wait_complete()
		self.cncc.home(1)
		self.cncc.wait_complete()
		self.cncc.home(2)
		self.cncc.wait_complete()
		self.cncs.poll()
	
	        self.cncs.poll()

		time.sleep(3) #fixme! hacky
	        self.cncs.poll()

		while self.cncs.state != 1:
		        self.cncs.poll()
		print ("moo",self.cncs.state)

		self.cncc.mode(linuxcnc.MODE_MDI)
		while not self._ok_for_mdi():	
			self.cncc.wait_complete()

		self.cncc.mdi("G92 X1 Y1 Z%f" % 41.5) #fixme hardcoded 
		self.cncc.mdi("G0 X2.0 Y2.0 Z%f"  % 39.5)
		self.cncc.mdi("G92 X0 Y0")
		self.cncc.wait_complete()
		time.sleep(3)
		self.cncs.poll()
		while self.cncs.state != 1:
		        self.cncs.poll()
		self.cncc.wait_complete()
		self.cncc.mode(linuxcnc.MODE_MANUAL)
		self.cncc.wait_complete()







		
class cncproxyserver():
	def __init__(self,cncwrapper, host,port):
		self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.server.bind((host, port))
		self.server.listen(5)
		self.cncwrapper = cncwrapper
		self.inputs = [self.server]
		self.outputs = []

		

	def process_command(self, cmd):
		ret =  {"status":"NOP"}
		print(cmd)
		if cmd['cmd'] == 'MDI':
			self.cncwrapper.MDICommand(cmd['cmd'])
			ret =  {"status":"OK"}
			
		elif cmd['cmd'] == 'SPINDLE':
			ret =  {"status":"OK"}
			
		elif cmd['cmd'] == 'GETPOS':
			ret =  {"status":"OK","ret":self.cncwrapper.getPosition()}
					
		elif cmd['cmd'] == 'MODEMDI':
			self.cncwrapper.modeMDI()
			ret =  {"status":"OK"}
			
		elif cmd['cmd'] == 'MODEAUTO':
			self.cncwrapper.modeAuto()
			ret =  {"status":"OK"}

		elif cmd['cmd'] == 'JOG':
			self.cncwrapper.jogAxis(cmd['axis'])
			ret =  {"status":"OK"}

		elif cmd['cmd'] == 'JOGSTOP':
			self.cncwrapper.jogStop(cmd['axis'])
			ret =  {"status":"OK"}

		elif cmd['cmd'] == 'HOMEMILL':
			self.cncwrapper.HomeMill()
			ret =  {"status":"OK"}
		else:
			ret =  {"status":"NO SUCH COMMAND"}

		ret = json.dumps(ret)
		return struct.pack(">L", len(ret)) + ret
	
	
	def run(self):
		while self.inputs:
			readable, writable, exceptional = select.select(self.inputs, self.inputs, self.inputs)
			
			for s in readable:
				if s is self.server:
					connection, client_address = s.accept()
					self.inputs.append(connection)
				else:
#					try:
						r1 = struct.unpack(">L", s.recv(struct.Struct(">L").size))[0]
						r2 = s.recv(r1)
						r2 = json.loads(r2)
						s.send(self.process_command(r2))
#					except:
#						self.inputs.remove(s)
#						s.close()
#						continue
				
			for s in exceptional:
				self.inputs.remove(s)
				s.close()


lcw = LinuxCNCWrapper()
srv = cncproxyserver(lcw, 'localhost', 5005)
srv.run()
