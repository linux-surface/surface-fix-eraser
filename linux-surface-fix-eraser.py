#!/usr/bin/env python3

import os
import os.path
import sys

from errno import ENOENT
from evdev import InputDevice, UInput
from evdev.events import InputEvent
from evdev.ecodes import BTN_TOOL_PEN, BTN_TOOL_RUBBER, EV_KEY
from signal import signal, SIGINT

# Automatically discover the device
for name in os.listdir('/dev/input'):
	if not name.startswith('event'):
		continue

	tmpdev = InputDevice('/dev/input/' + name)
	if 'uinput' in tmpdev.name or 'Virtual Stylus' in tmpdev.name:
		continue

	keys = tmpdev.capabilities().get(EV_KEY)
	if keys == None:
		continue

	if BTN_TOOL_PEN in keys and BTN_TOOL_RUBBER in keys:
		device = '/dev/input/' + name

if device != None:
	print('Found event: ' + device)
else:
	print('No event found! Exiting.')
	sys.exit(-ENOENT)

dev = InputDevice(device)
virt = UInput.from_device(dev, name=dev.name + ' Virtual Stylus')

def handleExit(s, f):
	dev.ungrab()
	sys.exit(0)

# Take over complete control over the device - no events will be passed to
# other listeners. They are relayed to the virtual stylus created above.
signal(SIGINT, handleExit)
dev.grab()

for event in dev.read_loop():

	# When putting the eraser down, IPTS first sends an event that puts
	# down the Pen, and after that puts down the eraser. As far as the
	# system is concerned, you put down BOTH, the eraser and the pen.
	#
	# To fix this, we wait for all eraser events, and inject an event that
	# lifts up the pen again, before relaying the event to put down the
	# eraser.
	if event.code == BTN_TOOL_RUBBER:
		e = InputEvent(event.sec, event.usec, EV_KEY, BTN_TOOL_PEN, 0)
		virt.write_event(e)
		virt.syn()

	virt.write_event(event)

dev.ungrab()
