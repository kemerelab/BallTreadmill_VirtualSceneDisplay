import math
import dao
import numpy as np
import serial
import xinput
import gnoomutils as gu
import sys
import time
import GameLogic

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
        
        movement(controller, (y1, y2, t1, t2, dt1, dt2))
        
def movement(controller, move):
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

    if len(move[0]):
        z = (float(move[0].sum())-float(move[1].sum())) * gain/2
        if z > 0:
            zrotate = z*2.54/50/1.41
            ori_new[0] = -(ori[0][2]*math.cos(zrotate) - ori[1][2]*math.sin(zrotate))
            ori_new[1] = -(ori[1][2]*math.cos(zrotate) + ori[0][2]*math.sin(zrotate))
            
            pos_new[0] = 1.41*ori_new[0]
            pos_new[1] = 1.41*ori_new[1]
            act_xytranslate.dLoc = [pos_new[0]-pos[0], pos_new[1]-pos[1], 0.0]
            act_zrotate.dRot = [0.0, 0.0, zrotate]
            print('%.2f'%ori_new[0],'%.2f'%ori_new[1])
    controller.activate(act_zrotate)
    controller.activate(act_xytranslate)
main()



