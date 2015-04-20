import math
import dao
import numpy as np
import serial
import xinput
import gnoomutils as gu
import sys
import time
import GameLogic

x_out = 1.89
y_out = 0.94
x1_in = 1.71
x2_in = 0.09
y_in = 0.81

try:
    GameLogic.Object
    init = 0
except:
    init = 1

blenderpath = GameLogic.expandPath('//')

if init:
    print(blenderpath)
    GameLogic.Object = {}
    print("BLENDER: GameLogic object created")
    GameLogic.Object['closed'] = False
    
    GameLogic.setLogicTicRate(60)
    
    mice = xinput.find_mice(model="Mouse")
    m = [mice[0],mice[1]]
    for mouse in m:
        xinput.set_owner(mouse) # Don't need this if using correct udev rule
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

        GameLogic.Object['m1conn'] = conn1
        GameLogic.Object['m2conn'] = conn2


    else:
        GameLogic.Object['m1conn'] = None
        GameLogic.Object['m2conn'] = None


conn1 = GameLogic.Object['m1conn']
conn2 = GameLogic.Object['m2conn']


def main():
    if GameLogic.Object['closed']:
        return
    else:

        gu.keep_conn([conn1, conn2])
        controller = GameLogic.getCurrentController()
        obj = controller.owner
        ori = obj.localOrientation
        pos = obj.localPosition
        
        if conn1 is not None:
            t1, dt1, x1, y1 = gu.read32(conn1)
            t2, dt2, x2, y2 = gu.read32(conn2)
        else:
            t1, dt1, x1, y1 = np.array([0,]), np.array([0,]), np.array([0,]), np.array([0,])
            t2, dt2, x2, y2 = np.array([0,]), np.array([0,]), np.array([0,]), np.array([0,])
    movement(controller, (x1, y1, x2, y2, t1, t2, dt1, dt2))

def movement(controller, move):

    # Note that x is mirrored if the dome projection is used.
    xtranslate = 0
    ztranslate = 0
    zrotate = 0
    gain = 1/1000
    # y axis front mouse
    if len(move[3]):
        # pass
        zt = (float(move[1].sum())-float(move[3].sum())) * gain/2  #forward distance
        ztranslate = zt*2.54/100
    # x axis front mouse / side mouse
    if len(move[0]) and len(move[2]):
        zr = (float(move[0].sum())+float(move[2].sum()))* gain/2
        zrotate = zr/7
        
    print("rotate", "%.3f" % zrotate, "translate", "%.3f" % ztranslate)
    # Get the actuators
    act_ztranslate = controller.actuators[0]
    act_zrotate    = controller.actuators[1]

    obj = controller.owner
    pos = obj.localPosition
    ori = obj.localOrientation

    print("current position", "%.3f" % pos[0], "%.3f" % pos[1], "%.3f" % ori[1][2], "%.3f" % ori[0][2])

    pos_n = [ztranslate*ori[0][2]+pos[0], ztranslate*ori[1][2]+pos[1]]
    
    if pos_n[0] >= x_out or pos_n[0]<=-x_out:
	    print('wall')
	    ztranslate = 0
    elif pos_n[1] >= y_out or pos_n[1] <= -y_out:
	    print('wall')
	    ztranslate = 0
    elif -x2_in >= pos_n[0] >= -x1_in and y_in >= pos_n[1] >= -y_in:
	    print('wall')
	    ztranslate = 0
    elif x1_in >= pos_n[0] >= x2_in and y_in >= pos_n[1] >= -y_in:
	    print('wall')
	    ztranslate = 0
    
    act_ztranslate.dLoc = [0, 0, ztranslate]
    act_ztranslate.useLocalDLoc = True
    
    act_zrotate.dRot = [0.0, 0.0, zrotate]
    act_zrotate.useLocalDRot = False
    
    controller.activate(act_zrotate)
    controller.activate(act_ztranslate)
main()

