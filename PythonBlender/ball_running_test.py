#!/usr/bin/python3
import math
import dao
import numpy as np
import serial
import xinput
import gnoomutils as gu
import sys
import time

#python3 ball_running_test.py

mice = xinput.find_mice(model="Mouse")
m = [mice[0],mice[1]]
blenderpath = "/home/kemerelab/git/VR_Ball"
for mouse in m:
    xinput.set_owner(mouse)
    xinput.switch_mode(mouse)

if len(mice):   
    s1, conn1, addr1, p1 = \
      gu.spawn_process("\0mouse0socket", 
                  ['%s/evread/readout' % blenderpath, '%d' % mice[0].evno, '0'])
    s2, conn2, addr2, p2 = \
      gu.spawn_process("\0mouse1socket", 
                  ['%s/evread/readout' % blenderpath, '%d' % mice[1].evno, '1'])

    conn1.send(b'start')
    conn2.send(b'start')

    gu.recv_ready(conn1)
    gu.recv_ready(conn2)

    conn1.setblocking(0)
    conn2.setblocking(0)

try:
    arduino = serial.Serial('/dev/arduino_ethernet', 9600)
    print("Pump Connected")
except:
    print("Pump not Connected")

duration = float(sys.argv[4])

def main(argv=None):
    if argv is None:
        argv = sys.argv
    start = time.time()
    while time.time() - start < duration:
        time.sleep(float(sys.argv[2]))
        gu.keep_conn([conn1, conn2])
        if conn1 is not None:
            t1, dt1, x1, y1 = gu.read32(conn1)
            t2, dt2, x2, y2 = gu.read32(conn2)
        else:
            t1, dt1, x1, y1 = np.array([0,]), np.array([0,]), np.array([0,]), np.array([0,])
            t2, dt2, x2, y2 = np.array([0,]), np.array([0,]), np.array([0,]), np.array([0,])
        z = (float(y1.sum())-float(y2.sum()))/2/1000*2.54 # distance
        dt = float(dt1.sum())
        v = z/dt
        if v > float(sys.argv[1]):
            try:
                arduino.write(b'L')
            except:
                print("no pump")
            print('%.2f'%(time.time()-start), '%.2f'%v, 'cm/s', '%.2f'%dt, 's')
            ct = 0
            while ct < float(sys.argv[3]):
                time.sleep(1)
                ct = ct + 1
                gu.keep_conn([conn1,conn2])
                t1, dt1, x1, y1 = gu.read32(conn1)
                t2, dt2, x2, y2 = gu.read32(conn2)
            print('Ready for next reward')
    print("Finished")

if __name__ == "__main__":
    sys.exit(main())



