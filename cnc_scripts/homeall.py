import linuxcnc
import os
import sys
import time
s = linuxcnc.stat()
c = linuxcnc.command()

def ok_for_mdi():
	time.sleep(.1)
	s.poll()
	return not s.estop and s.enabled and s.homed and (s.interp_state == linuxcnc.INTERP_IDLE) and  (s.state == 1)


c.mode(linuxcnc.MODE_MANUAL)
c.wait_complete()
c.reset_interpreter()
c.home(0)
c.home(1)
c.home(2)
s.poll()
while not ok_for_mdi():
	c.wait_complete()

c.mode(linuxcnc.MODE_MDI)
c.mdi("G92 X0 Y0 Z41.5")
c.mdi("G0 X0 Y0 Z0")
c.mdi("G10 L2 P1 X0 Y0 Z0")
s.poll()
while s.state != 1:
	s.poll()
c.wait_complete()
c.mode(linuxcnc.MODE_MANUAL)
c.wait_complete()
