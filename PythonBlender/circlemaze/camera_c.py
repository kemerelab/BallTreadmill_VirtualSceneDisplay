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
    GameLogic.Object['reward_done'] = False 
    controller = GameLogic.getCurrentController()
    obj = controller.owner
    ori = obj.localOrientation
    pos = obj.localPosition
    
    dropboxdao = dao.DropboxAccess()
    GameLogic.Object['dao'] = dropboxdao
    trial_file_name = '%strial.txt' % blenderpath
    GameLogic.Object['trial_file'] = trial_file_name
    GameLogic.Object['last_position'] = [pos[0],pos[1]]
    
    if (sys.argv[1] == "-P") or (sys.argv[1] == "-g"):
        print('develop mode')
        subject = "test"
        scene = "test"
        GameLogic.Object['duration'] = 10.0
        GameLogic.Object['timestamp'] = 0.2
    else:
        subject = sys.argv[1]
        scene = "circle_maze"
        GameLogic.Object['duration'] = float(sys.argv[2])
        GameLogic.Object['timestamp'] = float(sys.argv[3])
    
    GameLogic.setLogicTicRate(60)
    
    try:
        print(trial_file_name)
        dropboxdao.download_file('/trial.txt', trial_file_name)
        print("downloading existing trials information file")
    except:
        print("creating trials information file")
        dropboxdao.update_file(trial_file_name, 'id scene subject timestamp duration date\n', 'w')
    
    print('add new trial information')
    
    with open(trial_file_name) as f:
        for i, l in enumerate(f):
            pass
        num_lines = i + 1
    
    GameLogic.Object['trialid'] = num_lines
    line = '%s %s %s %.3f %.3f %s\n' % (str(num_lines), scene, subject, \
                GameLogic.Object['timestamp'], GameLogic.Object['duration'], time.time())
    dropboxdao.update_file(trial_file_name, line, 'a')


    #create and start trial trajectory file
    trajectory_file_name = '%s/trajectory_%s.txt' % (blenderpath, str(num_lines))
    GameLogic.Object['trajectory_file'] = trajectory_file_name
    line = '%s %s %s %s\n' % ('x', 'y', 'cosx_x', 'cosy_x')
    dropboxdao.update_file(trajectory_file_name, line, 'w')
    line = '%.3f %.3f %.3f %.3f\n' % (pos[0],pos[1],ori[0][0],ori[1][0])
    dropboxdao.update_file(trajectory_file_name, line, 'a')
    
    
    #create and start trial event file
    event_file_name = '%s/event_%s.txt' % (blenderpath, str(num_lines))
    GameLogic.Object['event_file'] = event_file_name
    line = '%s %s\n' % ('event', 'time')
    dropboxdao.update_file(event_file_name, line, 'w')
    line = '%s %.3f\n' % ('start', 0)
    dropboxdao.update_file(event_file_name, line, 'a') 
    
            
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
        GameLogic.Object['start'] = time.time()
        GameLogic.Object['last'] = time.time()
        
        try:
            GameLogic.Object['Arduino'] = serial.Serial('/dev/arduino_ethernet', 9600)
            print("Pump Connected")
        except:
            GameLogic.Object['Arduino'] = []
            print("Pump not Connected")
    else:
        GameLogic.Object['m1conn'] = None
        GameLogic.Object['m2conn'] = None

dropboxdao = GameLogic.Object['dao']
conn1 = GameLogic.Object['m1conn']
conn2 = GameLogic.Object['m2conn']
trial_id = GameLogic.Object['trialid']
arduino = GameLogic.Object['Arduino']

def main():
    if GameLogic.Object['closed']:
        return
    else:
        # check if time is up
        proceeding = GameLogic.Object['last'] - GameLogic.Object['start']
        if proceeding > GameLogic.Object['duration'] - 0.005:
            GameLogic.Object['closed'] = True
            print(proceeding)
            dropboxdao.upload_file(GameLogic.Object['trial_file'], '/trial.txt')
            dropboxdao.upload_file(GameLogic.Object['trajectory_file'], \
                '/trajectory&event/trajectory_%s.txt'%str(trial_id))
            
            line = '%s %.3f\n' % ('end', GameLogic.Object['last']-GameLogic.Object['start'])
            dropboxdao.update_file(GameLogic.Object['event_file'], line, 'a')
            dropboxdao.upload_file(GameLogic.Object['event_file'], \
                '/trajectory&event/event_%s.txt'%str(trial_id))
            GameLogic.endGame()
        
        
        gu.keep_conn([conn1, conn2])
        controller = GameLogic.getCurrentController()
        obj = controller.owner
        ori = obj.localOrientation
        pos = obj.localPosition
        
        # check timestampe & if inserting trajectory point 
        current_time = time.time()
        if (current_time - GameLogic.Object['last']) > GameLogic.Object['timestamp'] - 0.005:
            GameLogic.Object['last'] = current_time
            line = '%.3f %.3f %.3f %.3f\n' % (pos[0],pos[1],ori[0][0],ori[1][0])
            dropboxdao.update_file(GameLogic.Object['trajectory_file'], line, 'a')
                
        # check if pumping reward
        if arduino:
            last_pos = GameLogic.Object['last_position']
            area = (pos[0] < 0 and -0.1 <= pos[1] <= 0.1)
            last_area = (last_pos[0] < 0 and -0.1 <= last_pos[1] <= 0.1)

            if not area and not last_area and GameLogic.Object['reward_done']:
                GameLogic.Object['reward_done'] = False

            elif area and not last_area:
                print('enter reward area')
                GameLogic.Object['entry_time'] = time.time()
                line = '%s %.3f\n' % ('enter', GameLogic.Object['entry_time'] - GameLogic.Object['start'])
                dropboxdao.update_file(GameLogic.Object['event_file'], line, 'a')
                
            elif not area and last_area:
                print('exit reward area')
                line = '%s %.3f\n' % ('exit', time.time()-GameLogic.Object['start'])
                dropboxdao.update_file(GameLogic.Object['event_file'], line, 'a')
            
            elif area and last_area and not GameLogic.Object['reward_done']:
                GameLogic.Object['stay_time'] = time.time()
                duration = GameLogic.Object['stay_time'] - GameLogic.Object['entry_time']
                if  duration > 2.995:
                    print('reward: %.3f'%duration)
                    arduino.write(b'L')
                    GameLogic.Object['reward_done'] = True
                    line = '%s %.3f\n' % ('reward', GameLogic.Object['stay_time']-GameLogic.Object['start'])
                                              
            
        GameLogic.Object['last_position'] = [pos[0],pos[1]]

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
            ori_new[0] = ori[0][0]*math.cos(zrotate) - ori[1][0]*math.sin(zrotate)
            ori_new[1] = ori[1][0]*math.cos(zrotate) + ori[0][0]*math.sin(zrotate)
            
            pos_new[0] = 1.41*ori_new[0]
            pos_new[1] = 1.41*ori_new[1]
            act_xytranslate.dLoc = [pos_new[0]-pos[0], pos_new[1]-pos[1], 0.0]
            act_zrotate.dRot = [0.0, 0.0, zrotate]
            print('%.2f'%ori_new[0],'%.2f'%ori_new[1])
    controller.activate(act_zrotate)
    controller.activate(act_xytranslate)
main()


