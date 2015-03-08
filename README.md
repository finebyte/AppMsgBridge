# AppMsgBridge
AppMessage Bridge for Pebble Emulator to Android

Instructions
------------

All paths should be adjusted to your own SDK location and version  

Start the emulator  
`~/pebble-dev/PebbleSDK-3.0-dp1/bin/pebble install --emulator basalt`

Load your app into the emulator, then stop it (i.e. press the left
arrow)  
`~/pebble-dev/PebbleSDK-3.0-dp1/bin/pebble install --phone localhost:12342 --logs my app.pbw`

Linux / Mac
-
* Bridge assumes the port numbers from the emu have not been changed,
  and runs on 9000 itself
* Copy appmsgbrdge.py into your environment  
`cp appmsgbridge.py ~/pebble-dev/PebbleSDK-3.0-dp1/Pebble/common/phonesim`
* The bridge needs to be running in a Pebble enables python
  environment, e.g.  
`source ~/pebble-dev/PebbleSDK-3.0-dp1/.env/bin/activate`
* The Python bridge requires a newer version of autobahn than comes
  with the Pebble SDK (only do this once)  
`pip install autobahn --upgrade`
* Run:  
`cd  ~/pebble-dev/PebbleSDK-3.0-dp1/Pebble/common/phonesim`  
`python appmsgbridge.py`

Android
-
* Build and Install the APK
* THIS IS IMPORTANT : Ensure your real Pebble and Phone are not connected (e.g turn of BT
on your Pebble)
* Start the Android side of the bridge running by entering your ws uri e.g. ws://192.168.0.6:9000
* Click on Start Bridge - you should see the connection arrive on the python bridge

Known Limitations
-
* The Android side only sends through app messages and ack and nack
* If your app stops communicating when it thinks the Pebble is disconnected you will have to override this.
* Not all data types have been well tested - strings work and byte arrays are implemented but might need more work
* Reliabilty is not 100% - there are a fair few SendFails from the Pebble...


