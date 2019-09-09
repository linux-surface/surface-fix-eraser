# split-stylus
The most recent `libinput` update removed some functionality for having both,
a pen and an eraser on the same hardware device. Effectively, all events coming
from one event node under `/dev/input` are treated as if they were all the same
(either a pen, or an eraser), even though they might emit the signals for both.

This is a band-aid fix that solves the problem while libinput can fix the bugs
introduced by this kind of hardware behaviour properly. This python daemon 
takes full control over the input node of the stylus, and splits it into two 
virtual ones: one for the pen and one for the eraser. This stops libinput from
treating the eraser like a pen, so you can use both without downgrading.

This should work out of the box for Microsoft Surface devices, other devices who
face the same bug might not work out of the box, depending on how their stylus
is set up.

## Installation
```bash
$ git clone https://github.com/StollD/split-stylus
$ cd split-stylus
$ sudo cp split-stylus.py /usr/local/bin/
$ sudo cp split-stylus.service /etc/systemd/system/
$ sudo systemctl enable --now split-stylus
```

You need to install version 1.2.0 of `python-evdev` or higher. Unfortunately,
most distributions seem to package 1.1.2, so you might have to force an update.
```bash
$ sudo pip3 install -U evdev
```
