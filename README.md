# AppMsgBridge
AppMessage Bridge for Pebble Emulator to Android

Updated: 5 March 2015

Instructions
------------

AppMsgBridge and these instructions assume you are using libpebble2 (all recent SDKs) and Pebble Tool 4 (see https://developer.getpebble.com/blog/2015/12/01/A-New-Pebble-Tool/)

* Start the emulator

`pebble install --emulator basalt`

Android
-
* Build and Install the APK
* THIS IS IMPORTANT : Ensure your real Pebble and Phone are not connected (e.g turn of BT on your Pebble)
* Start the Android side of the bridge and note the ws uri e.g. ws://192.168.0.6:9011

Linux / Mac
-
* Find your local Pebble PYTHON_PATH and set it. Recent brew installs can do as follows:

`which pebble`

/usr/local/bin/pebble

`cat /usr/local/bin/pebble`

PYTHONPATH="/usr/local/Cellar/pebble-sdk/4.0/libexec/vendor/lib/python2.7/site-packages:/usr/local/Cellar/pebble-sdk/4.0/libexec/lib/python2.7/site-packages" PHONESIM_PATH="/usr/local/Cellar/pebble-sdk/4.0/libexec/vendor/bin/pypkjs" PEBBLE_TOOLCHAIN_PATH="/usr/local/Cellar/pebble-toolchain/2.0/arm-cs-tools/bin" PEBBLE_IS_HOMEBREW="1" exec "/usr/local/Cellar/pebble-sdk/4.0/libexec/bin/pebble" "$@"

```
export PYTHONPATH="/usr/local/Cellar/pebble-sdk/4.0/libexec/vendor/lib/python2.7/site-packages:/usr/local/Cellar/pebble-sdk/4.0/libexec/lib/python2.7/site-packages"
```

* Older SDK installs will need to find where the SDK and libpebble2 was installed under that.

`export PYTHONPATH=PATH_TO_YOUR_PEBBLE_SDK/.env/lib/python2.7/site-packages`

* Run the Bridge with the uri to your Android device and the emulator type (or a ws endpoint for advanced use)  

`python appmsgbridge.py ws://192.168.0.6:9011 basalt`


Known Limitations
-
* The Android side only sends through app messages and ack and nack
* If your app stops communicating when it thinks the Pebble is disconnected you will have to override this.
* Reliabilty is not 100% - there are a fair few SendFails from the Pebble...
* If things stop working, you may need to restart your pebble app and/or the emu
