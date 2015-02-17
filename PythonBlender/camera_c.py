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

import GameLogic
try:
    GameLogic.Object
    init = 0
except:
    init = 1

# [1.8 0.85]
x_out = 1.85
y_out = 0.92
x1_in = 1.75
x2_in = 0.05
y_in = 0.83

if init:
    GameLogic.Object = {}
    print("BLENDER: GameLogic object created")
    GameLogic.Object['closed'] = False
    GameLogic.setLogicTicRate(1)
    
    dropboxdao = dao.DropboxAccess()
    manager = DatastoreManager(dropboxdao.api_client)
    datastore = manager.open_default_datastore()

    manager_table = datastore.get_table('manager')
    l = len(manager_table.query())
    try:
        manager_table.insert(id = l+1, taskname='figure 8 maze', completed=False)
        datastore.commit()
    except DatastoreConflictError:
        datastore.rollback()    # roll back local changes
        datastore.load_deltas() # load new changes from Dropbox

    datastore.commit()
        
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
try:
    arduino = serial.Serial('/dev/arduino_ethernet', 9600)
except:
    print("No reward")
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
        if x1_in <= pos[0] <= x_out and y_in <= pos[1] <= y_out:
            arduino.write(b'A')
        elif -x1_in >= pos[0] >= -x_out and -y_in >= pos[1] >= -y_out:
            arduino.write(b'B')
        else:
            arduino.write(b'L')    
    except:
        print("No reward")
    
    if conn1 is not None:
        # get mouse movement
        t1, dt1, x1, y1 = gu.read32(conn1)
        t2, dt2, x2, y2 = gu.read32(conn2)
    else:
        t1, dt1, x1, y1 = np.array([0,]), np.array([0,]), np.array([0,]), np.array([0,])
        t2, dt2, x2, y2 = np.array([0,]), np.array([0,]), np.array([0,]), np.array([0,])   
    # move according to ball readout:
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
        ztranslate = float(move[3].sum()) * gain  #forward distance
        ztranslate = ztranslate*2.54/100
    # x axis front mouse / side mouse
    if len(move[0]) and len(move[2]): #float(move[2].sum()) + 
        zr = (float(move[0].sum()))* gain
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

