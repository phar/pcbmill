import linuxcnc
import os
import sys
import time
s = linuxcnc.stat()
c = linuxcnc.command()


c.mode(linuxcnc.MODE_AUTO)
c.wait_complete()
c.reset_interpreter()
c.program_open("../../../../../../../../%s" % sys.argv[1])
c.auto(linuxcnc.AUTO_RUN,1)
s.poll()	
wait = True
while s.exec_state == 7:
	time.sleep(.5)
	s.poll()

while s.state != 1:
        s.poll()
c.wait_complete()
c.mode(linuxcnc.MODE_MANUAL)
c.wait_complete()
time.sleep(1)

