
from __future__ import print_function
from dropbox.datastore import DatastoreManager, Date, DatastoreError

import math
import dao
import numpy as np
import serial
import xinput
import gnoomutils as gu
import sys
import sched, time

s = sched.scheduler(time.time, time.sleep)

import GameLogic

try:
    GameLogic.Object
    init = 0
except:
    init = 1
    
dropboxdao = dao.DropboxAccess()

if init:
    print("start")
    GameLogic.Object = {}
    print("BLENDER: GameLogic object created")
    GameLogic.Object['closed'] = False
    
    #update task pool if it's a new task
    scene_name = "circle_maze"
    scene_id = dropboxdao.update_scene(scene_name)    
    #dropboxdao.update_subject()

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
        
    else:
        GameLogic.Object['m1conn'] = None
        GameLogic.Object['m2conn'] = None

conn1 = GameLogic.Object['m1conn']
conn2 = GameLogic.Object['m2conn']
print ("This is the name of the script: ", sys.argv[0])
print ("Number of arguments: ", len(sys.argv))
print ("The arguments are: " , str(sys.argv))
# define main program
def main():
    
    if GameLogic.Object['closed']:
        return
    # get controller
    gu.keep_conn([conn1, conn2])
    
    controller = GameLogic.getCurrentController()
    
    obj = controller.owner
    pos = obj.localPosition
    xy = [pos[0], pos[1]]
    try:
        arduino = serial.Serial('/dev/arduino_ethernet', 9600)
        if pos[0] < 0 and -0.1 <= pos[1] <= 0.1:
            arduino.write(b'L')
        else:
            arduino.write(b'H')
    except:
        print("No Pump")
    
    dropboxdao.update_trajectory(xy)  
    
    
    if conn1 is not None:
        # get mouse movement
        t1, dt1, x1, y1 = gu.read32(conn1)
        t2, dt2, x2, y2 = gu.read32(conn2)
    else:
        t1, dt1, x1, y1 = np.array([0,]), np.array([0,]), np.array([0,]), np.array([0,])
        t2, dt2, x2, y2 = np.array([0,]), np.array([0,]), np.array([0,]), np.array([0,])
    
    # move according to ball readout:
    movement(controller, (y1, y2, t1, t2, dt1, dt2))
    
    print('location:' , "%.3f" % pos[0], "%.3f" % pos[1])


def movement(controller, move):
    # Note that x is mirrored if the dome projection is used.
    xtranslate = 0
    ztranslate = 0
    zrotate = 0
    gain = 1/1000
  
    act_xytranslate = controller.actuators[0]
    act_zrotate    = controller.actuators[1]
    
    act_xytranslate.dLoc = [0.0, 0.0, 0.0]
    act_xytranslate.useLocalDLoc = False
    
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
            zrotate = z*2.54/50/1.41
            ori_new[0] = ori[0][0]*math.cos(zrotate) - ori[1][0]*math.sin(zrotate)
            ori_new[1] = ori[1][0]*math.cos(zrotate) + ori[0][0]*math.sin(zrotate)
            
            pos_new[0] = 1.41*ori_new[0]
            pos_new[1] = 1.41*ori_new[1]
            act_xytranslate.dLoc = [pos_new[0]-pos[0], pos_new[1]-pos[1], 0.0]
            act_zrotate.dRot = [0.0, 0.0, zrotate]
    
    print("%.3f" % ori[0][0], "%.3f" % ori[1][0], "%.3f" % zrotate)    
    controller.activate(act_zrotate)
    controller.activate(act_xytranslate)
    
main()


