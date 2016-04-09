# AppMsgBridge
AppMessage Tools for Pebble Emulator
Send AppMessages from Android , File, or Simple Web Interface to Emu

Updated: 9 April 2016

Instructions
------------

AppMsgBridge and these instructions assume you are using libpebble2 (all recent SDKs) and Pebble Tool 4 (see https://developer.getpebble.com/blog/2015/12/01/A-New-Pebble-Tool/)

* Start the emulator

`pebble install --emulator basalt`

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

For Android Bridge
-
* Build and Install the APK
* THIS IS IMPORTANT : Ensure your real Pebble and Phone are not connected (e.g turn of BT on your Pebble)
* Start the Android side of the bridge and note the ws uri e.g. ws://192.168.0.6:9011


* Run the Bridge with the relevant option and the emulator type (or a ws endpoint for advanced use)  
```
usage: appmsgbridge.py [-h] -i source -o dest
optional arguments:
  -h, --help  show this help message and exit
  -i source   Source of Input data 
              server = Start WSS server (for web page)
              ws://192.168.1.102:9011 = Connect to ws endpoint
               (e.g. the Bridge Android app)
              filename = Read from a file with JSON messages one per line
              - = Read from stdin with JSON messages one per line
  -o dest     Destination address of pebble / emu
              aplite | basalt | chalk = Find the relevant Pebble emu
              ws://localhost:52377 = Connect to ws endpoint
```
Known Limitations
-
* The Android side only sends through app messages and ack and nack
* If your app stops communicating when it thinks the Pebble is disconnected you will have to override this.
* Reliabilty is not 100% - there are a fair few SendFails from the Pebble...
* If things stop working, you may need to restart your pebble app and/or the emu
