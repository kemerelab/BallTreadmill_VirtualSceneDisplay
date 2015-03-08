#! /usr/bin/python3
import sys
import xinput as xi

if __name__ == "__main__":
    on = False
    if len(sys.argv) > 1:
        on = sys.argv[1]!='0'

    for mouse in xi.find_mice(model="Mouse"):
        xi.switch_mode(mouse, on)
