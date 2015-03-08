#object rotation according to z axis of global orientation
#object translation according to z axis of local orientation
from __future__ import print_function
from dropbox.datastore import DatastoreManager, Date, DatastoreError

import math
import dao
import numpy as np
import serial
import xinput
import gnoomutils as gu
import sched, time
s = sched.scheduler(time.time, time.sleep)

import GameLogic

try:
    GameLogic.Object
    init = 0
except:
    init = 1

print("start")
if init:
    GameLogic.Object = {}
    print("BLENDER: GameLogic object created")
    GameLogic.Object['closed'] = False
    
    dropboxdao = dao.DropboxAccess()
    taskname = "circle_maze"
    dropboxdao.update_task(taskname)

    GameLogic.setLogicTicRate(5)
    mice = xinput.find_mice(model="Mouse")
    m = [mice[0],mice[1]]
    
    for mouse in m:
        xinput.set_owner(mouse) # Don't need this if using correct udev rule
        xinput.switch_mode(mouse)

    blenderpath = GameLogic.expandPath('//')
    
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

        GameLogic.Object['m1conn'] = conn1
        GameLogic.Object['m2conn'] = conn2
        
        try:
            arduino = serial.Serial('/dev/arduino_ethernet', 9600)
            print("Pump connected")
        except:
            print("No reward")
    else:
        GameLogic.Object['m1conn'] = None
        GameLogic.Object['m2conn'] = None

conn1 = GameLogic.Object['m1conn']
conn2 = GameLogic.Object['m2conn']


# define main program
def main():
    
    if GameLogic.Object['closed']:
        return
    # get controller
    
    controller = GameLogic.getCurrentController()
    gu.keep_conn([conn1, conn2])

    obj = controller.owner
    pos = obj.localPosition
    ori = obj.localOrientation

    try:
        if pos[0] < 0 and -0.1 <= pos[1] <= 0.1:
            arduino.write(b'A')
            print('A')
        else:
            arduino.write(b'L')
            print('L')
    except:
        print("No Pump")
    
    if conn1 is not None:
        # get mouse movement
        t1, dt1, x1, y1 = gu.read32(conn1)
        t2, dt2, x2, y2 = gu.read32(conn2)
    else:
        t1, dt1, x1, y1 = np.array([0,]), np.array([0,]), np.array([0,]), np.array([0,])
        t2, dt2, x2, y2 = np.array([0,]), np.array([0,]), np.array([0,]), np.array([0,])   
    # move according to ball readout:
    movement(controller, (y1, y2, t1, t2, dt1, dt2))
    #GameLogic.logic.endGame()

def movement(controller, move):
    # Note that x is mirrored if the dome projection is used.
    xtranslate = 0
    ztranslate = 0
    zrotate = 0
    gain = 1/1000
  
    act_ztranslate = controller.actuators[0]
    act_zrotate    = controller.actuators[1]
    
    act_ztranslate.dLoc = [0.0, 0.0, 0.0]
    act_ztranslate.useLocalDLoc = False
    
    act_zrotate.dRot = [0.0, 0.0, 0.0]
    act_zrotate.useLocalDRot = False

    obj = controller.owner
    pos = obj.localPosition
    ori = obj.localOrientation
    ori_new = [0,0]
    pos_new = [0,0]    
    # y axis front mouse
    if len(move[0]):
        # pass
        z = (float(move[0].sum())-float(move[1].sum())) * gain/2  #forward distance
        if z > 0:
            zrotate = z*2.54/10/1.41
            ori_new[0] = ori[0][0]*math.cos(zrotate) - ori[1][0]*math.sin(zrotate)
            ori_new[1] = ori[1][0]*math.cos(zrotate) + ori[0][0]*math.sin(zrotate)
            
            pos_new[0] = 1.41*ori_new[0]
            pos_new[1] = 1.41*ori_new[1]
            act_ztranslate.dLoc = [pos_new[0]-pos[0], pos_new[1]-pos[1], 0.0]
            act_zrotate.dRot = [0.0, 0.0, zrotate]
    
    print("%.3f" % ori[0][0], "%.3f" % ori[1][0], "%.3f" % zrotate, "%.3f" % pos[0], "%.3f" % pos[1])    
    controller.activate(act_zrotate)
    controller.activate(act_ztranslate)
main()


