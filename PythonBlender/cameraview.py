from __future__ import print_function
import math as m
import GameLogic
# first pass?
try:
    GameLogic.Object
    init = 0
except:
    init = 1
import numpy as np
import bpy
import serial
import xinput
import gnoomutils as gu

if init:
    GameLogic.Object = {}
    print("BLENDER: GameLogic object created")
    GameLogic.Object['closed'] = False

    loc = bpy.context.active_object
    print("Original Location:",loc.location) 

    GameLogic.setLogicTicRate(100)


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
        print('0')
    else:
        print('0')
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

    arduino = serial.Serial('/dev/ttyACM0', 9600)

    if 34.2 <= pos[0] <= 37.8 and 16.2 <= pos[1] <= 18.8:
        arduino.write(b'A')
    elif -34.2 >= pos[0] >= -37.8 and -16.2 >= pos[1] >= -18.8:
        arduino.write(b'B')
    else:
        arduino.write(b'L')    

    if conn1 is not None:
        # get mouse movement
        t1, dt1, x1, y1 = gu.read32(conn1)
        #print(gu.read32(conn1))
        t2, dt2, x2, y2 = gu.read32(conn2)
    else:
        t1, dt1, x1, y1 = np.array([0,]), np.array([0,]), np.array([0,]), np.array([0,])
        t2, dt2, x2, y2 = np.array([0,]), np.array([0,]), np.array([0,]), np.array([0,])
        
    
    # move according to ball readout:
    movement(controller, (x1, y1, x2, y2, t1, t2, dt1, dt2))
# define useMouseLook
def movement(controller, move):

    # Note that x is mirrored if the dome projection is used.
    xtranslate = 0
    ytranslate = 0
    zrotate = 0
    gain = 1e-3

    # Simple example how the mice could be read out

    # y axis front mouse
    if len(move[3]):
        # pass
        ytranslate = float(move[3].sum()) * gain  #forward distance
    # x axis front mouse / side mouse
    if len(move[0]) and len(move[2]):
        # pass
        zrotate = float(move[0].sum()+move[2].sum())/2.0 * gain
        z = float(move[0].sum()+move[2].sum())

    # Get the actuators
    act_xtranslate = controller.actuators[0]
    act_ytranslate = controller.actuators[1]
    act_zrotate    = controller.actuators[2]

    obj = controller.owner
    pos = obj.localPosition
    ori = obj.localOrientation
    print(pos[0],pos[1])
    pos_n = [ytranslate*m.sin(m.asin(ori[0][2]))+pos[0], -ytranslate*m.cos(m.acos(ori[0][0]))+pos[1]]
    

    if pos_n[0] >= 37.8 or pos_n[0]<=-37.8:
	    print('wall')
	    ytranslate = 0
    elif pos_n[1] >= 18.8 or pos_n[1] <= -18.8:
	    print('wall')
	    ytranslate = 0
    elif -1.8 >= pos_n[0] >= -34.2 and 16.2 >= pos_n[1] >= -16.2:
	    print('wall')
	    ytranslate = 0
    elif 34.2 >= pos_n[0] >= 1.8 and 16.2 >= pos_n[1] >= -16.2:
	    print('wall')
	    ytranslate = 0
    
    act_ytranslate.dLoc = [0, 0, ytranslate]
    act_ytranslate.useLocalDLoc = True
    act_zrotate.dRot = [0.0, 0.0, zrotate]
    act_zrotate.useLocalDRot = False
    controller.activate(act_zrotate)
    controller.activate(act_ytranslate)
main()
