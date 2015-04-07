#Instruction
##Prerequisites

* Two Logitech M90/M100 mice
* Ubuntu OS
* Blender 2.7.x:
  `sudo add-apt-repository ppa:irie/blender`
  `sudo apt-get update`
  `$ sudo apt-get install blender`  
* git (to get the code):  
  `$ sudo apt-get install git`  
* xinput:  
  `$ sudo apt-get install xinput`  
* python3.3 numpy & scipy & serial:  
  `$ sudo apt-get install python3-numpy python3-scipy python3-serial python3-setuptools`
* dropbox
  [(Python Core SDK)](https://dl.dropboxusercontent.com/content_link/TZpxbObcAw11yzfZiAc3XDlTckf1HrK1SGfBwjrQu89MaayurngJW4dLUto3sdMh?dl=1)
  `$ python3 setup.py install`
* DisplayLink Driver for Ubuntu
  https://wiki.archlinux.org/index.php/DisplayLink#xrandr
##Install and Run

1. Get the code:  
  `$ git clone https://github.com/kemerelab/VR_Ball`  
2. Set up a group called **vr-users** and add yourself to that group.  
  `$ sudo addgroup vr-users`  
  `$ sudo adduser yourname vr-users`
3. Copy some **udev** rules to your system (**/etc/udev/rules.d/**): (**_$/_** will refer to the directory where you downloaded the code): **$/linux/etc/udev/rules.d/52-events.rules** will set up r/w permissions for when you connect an input device.**$/linux/etc/udev/rules.d/99-persistent-arduino.rules** will keep a persistent device name for arduino.
4. Copy **$/linux/usr/local/bin/findxinput.py** into **/usr/local/bin/**. Make sure they are executable.  
  `$ sudo chmod +x findxinput.py`  
  It is the script for soft detaching the optical mice when the program starts.
5. Copy **xinput.py** somewhere into **/usr/lib/pythonX.X/dist-packages/**)
6. `$ ./standalone device_number`  
  will print the readout from the first optical mouse to stdout. The _readout_ binary is for communicating with Blender through Unix sockets (Make sure they are executable).
7. Open the **$/figure8maze.blend**. Link all **$/pythonblender/*.py** to it. 
8. Plug in the Arduino Pro chip. Upload **$/Arduino/PyArduino** to the chip.
9. If everything went right, when you start the game mode (press 'P'), you can use optical mice to navigate the camera in virtual figure 8 maze and LED on Arduino will turn on. And the LED will be off for 2 seconds as soon as the camera enters 2 white areas in the maze alternatively.

##Reference
https://code.google.com/p/gnoom/
