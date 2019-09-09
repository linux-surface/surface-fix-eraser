#!/usr/bin/env python3

import os
import os.path
import sys

from argparse import ArgumentParser
from errno import ENOENT
from evdev import InputDevice, UInput
from evdev.ecodes import BTN_TOOL_PEN, BTN_TOOL_RUBBER, EV_KEY
from signal import signal, SIGINT

INPUT_DEVICE_PATH = '/dev/input'

cli = ArgumentParser(description='Split stylus input events into two devices')
cli.add_argument('-d', '--device', metavar='D', help='input device to use')
args = cli.parse_args()

# If no device was specified, we have to autodiscover it
if args.device == None:
	for name in os.listdir(INPUT_DEVICE_PATH):
		if not name.startswith('event'):
			continue
		tmpdev = InputDevice(INPUT_DEVICE_PATH + '/' + name)
		keys = tmpdev.capabilities().get(EV_KEY)
		if keys == None:
			continue
		if BTN_TOOL_PEN in keys and BTN_TOOL_RUBBER in keys:
			args.device = INPUT_DEVICE_PATH + '/' + name

if args.device != None:
	print('Found event: ' + args.device)
else:
	print('No event found! Exiting.')
	sys.exit(-ENOENT)

dev = InputDevice(args.device)
pen = UInput.from_device(dev, name=dev.name + " Pen")
eraser = UInput.from_device(dev, name=dev.name + " Eraser")

# Staging for events where we don't know the target device yet.
staged = list()
toStage = 0
stageHasEraser = False

# Whether the currently active tool is the eraser
eraserActive = False

# Relays the event to the currently active tool
def writeEvent(event):
	if eraserActive:
		eraser.write_event(event)
	else:
		pen.write_event(event)

def handleExit(s, f):
	dev.ungrab()
	sys.exit(0)

# Take over complete control over the device - no events will be passed to
# other listeners. They are relayed to the two virtual devices created above.
dev.grab()
signal(SIGINT, handleExit)

for event in dev.read_loop():
	
	# If we encounter a BTN_TOOL_PEN down event, stage all following events
	# until we can be sure that it is not part of a BTN_TOOL_RUBBER event
	if event.code == BTN_TOOL_PEN:
		staged.append(event)

		# If the stylus was put down on the screen, the BTN_TOOL_RUBBER
		# event will be sent 5 events after BTN_TOOL_PEN. If it was
		# lifted up, it will be sent immideately, but there is a final
		# event that needs to be catched
		if event.value == 1:
			toStage = 5
		elif event.value == 0:
			toStage = 1
		continue

	if event.code == BTN_TOOL_RUBBER:
		# Since there is one final event, we have to capture 
		# one more event
		if toStage == 1:
			toStage = 2

		# We have detected that the eraser is active
		stageHasEraser = True

	# If one event has been staged, keep on staging events. Otherwise, pass
	# them through to the active tool.
	if len(staged) > 0:
		staged.append(event)
	else:
		writeEvent(event)

	# If we have enough events staged, we can be sure that it is not a
	# BTN_TOOL_RUBBER event, so we can continue with processing them.
	if len(staged) <= toStage:
		continue;

	# Choose the tool input device
	eraserActive = stageHasEraser

	# When the eraser moves into proximity, we *only* want to forward the
	# BTN_TOOL_RUBBER event. The reason is that a whole bunch of stuff is
	# done in those 5 events, and libinput interprets these events as a
	# second device, triggering the very bug we want to fix.
	if eraserActive and toStage == 5:
		staged = filter(lambda s: s.code == BTN_TOOL_RUBBER, staged)
		staged = list(staged)

	# Forward all staged events and let libinput handle them
	for e in staged:
		writeEvent(e)

	# Clear the staging queue, and reset the eraser flag
	staged.clear()
	toStage = 0
	stageHasEraser = False

dev.ungrab()
