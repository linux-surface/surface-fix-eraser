# linux-surface eraser fixer
On Microsoft Surface devices, the touchscreen generates HID events directly in
hardware, which are relayed to the linux HID subsystem via. the IPTS driver.
These hardware events contain a bugged / nonstandard proximity report for the
eraser of the Surface Pen: When you move the eraser into proximity, IPTS will
first report that the pen was moved into proximity, and then report that the
eraser moved in. This means that as far as the kernel is concerned, **both**
devices will be active at the same time, as if you would be holding two
seperate pens onto the screen.

This behaviour is nonstandard, and as of the latest update to `libinput`
actually unsupported. The eraser events will simply be discarded as long as
the pen is still active - which, in the case of IPTS, is always.

The proper solution for this would be to fix the generated HID events, which
is impossible, or to process them in the kernel somehow. Since IPTS is not
upstream however, it could be a bit difficult to do it correctly.

Until a proper fix can happen, this python daemon will capture all HID events
coming from the stylus and forward them to a virtual input device (which then
is seen instead of the real stylus by everything else). When it notices that
the eraser moved near the screen, it will inject an event, telling the system
that the pen moved away from the screen again. Therefor `libinput` and friends
don't see two tools being active at the same time, they only see one.

This should work out of the box for Microsoft Surface devices using IPTS. For
other devices (like the Surface Go), it might be neccessary too, depending on
whether the issue is in the IPTS hardware, or the Surface Pen itself (which is
not tied to IPTS specifically). There is nothing that would stop it from
it from working on non-surface devices in theory, but it may or may not
actually work.

## Quirks
After you suspend and resume the surface, you have to rotate it into normal
position **before** touching the screen. Otherwise GNOME will totally mess up
the mapping and then decide to not map it at all and decide to leave the
virtual stylus unrotated. This can be fixed by restarting or simply suspending
and resuming again, and then following these steps.

## Installation
```bash
$ git clone https://github.com/StollD/linux-surface-fix-eraser
$ cd linux-surface-fix-eraser
$ sudo cp linux-surface-fix-eraser.py /usr/local/bin/
$ sudo cp linux-surface-fix-eraser.service /etc/systemd/system/
$ sudo systemctl enable --now linux-surface-fix-eraser
```

You need to install version 1.2.0 of `python-evdev` or higher. Unfortunately,
most distributions seem to package 1.1.2, so you might have to force an update.
```bash
$ sudo pip3 install -U evdev
```
