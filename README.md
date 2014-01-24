ev3
===

A Python interface for communicating with a Lego Mindstorms EV3 over RFCOMM.

  Verify that your sdp includes an SP:
```
-> % sdptool browse local
...
Service Name: Serial Port
Service Description: COM Port
...
```

  If you don't see an SP entry add one:
```
-> % sdptool add SP
```

  Then:
```
-> % hcitool scan
...
XX:XX:XX:XX:XX:XX   EV3
...

-> % sudo rfcomm bind /dev/rfcomm0 XX:XX:XX:XX:XX:XX
```

  Now /dev/rfcomm0 can be opened and closed like a normal serial port.
  The opposite action is:
```
-> % sudo rfcomm release /dev/rfcomm0
```
