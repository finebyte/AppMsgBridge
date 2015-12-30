# AppMsgBridge
AppMessage Bridge for Pebble Emulator to Android

Updated: 30 December 2015

Instructions
------------

* Start the emulator with -v

`pebble install --emulator basalt -v`

* Review the output:

INFO:requests.packages.urllib3.connectionpool:Starting new HTTP connection (1): 209.118.208.39
INFO:pebble_tool.sdk.emulator:Spawning QEMU.
INFO:pebble_tool.sdk.emulator:Qemu command: qemu-pebble -rtc base=localtime -serial null -serial tcp::52375,server,nowait -serial tcp::52376,server -pflash "/Users/turcja/Library/Application Support/Pebble SDK/SDKs/3.7/sdk-core/pebble/basalt/qemu/qemu_micro_flash.bin" -machine pebble-snowy-bb -cpu cortex-m4 -pflash "/Users/turcja/Library/Application Support/Pebble SDK/3.7/basalt/qemu_spi_flash.bin"
INFO:pebble_tool.sdk.emulator:Waiting for the firmware to boot.
INFO:requests.packages.urllib3.connectionpool:Starting new HTTPS connection (1): td.getpebble.com
INFO:pebble_tool.sdk.emulator:Firmware booted.
INFO:pebble_tool.sdk.emulator:Spawning pypkjs.
INFO:requests.packages.urllib3.connectionpool:Starting new HTTPS connection (1): td.getpebble.com
INFO:pebble_tool.sdk.emulator:pypkjs command: /usr/bin/python /usr/local/Cellar/pebble-sdk/4.0/libexec/vendor/bin/pypkjs --qemu localhost:52375 --port 52377 --persist "/Users/turcja/Library/Application Support/Pebble SDK/3.7/basalt" --layout "/Users/turcja/Library/Application Support/Pebble SDK/SDKs/3.7/sdk-core/pebble/basalt/qemu/layouts.json" --debug --oauth 995fe7eba0cec49aaa68074f27d923e6e712bd41200a2e7908e08579809f0860
Installing app...
App install succeeded.

* Note the port number from the pypkjs --port argument

`52377`

Android
-
* Build and Install the APK
* THIS IS IMPORTANT : Ensure your real Pebble and Phone are not connected (e.g turn of BT on your Pebble)
* Start the Android side of the bridge and note the ws uri e.g. ws://192.168.0.6:9011

Linux / Mac
-
* Find your local Pebble PYTHON_PATH and set it

`which pebble`

/usr/local/bin/pebble

`cat /usr/local/bin/pebble`

PYTHONPATH="/usr/local/Cellar/pebble-sdk/4.0/libexec/vendor/lib/python2.7/site-packages:/usr/local/Cellar/pebble-sdk/4.0/libexec/lib/python2.7/site-packages" PHONESIM_PATH="/usr/local/Cellar/pebble-sdk/4.0/libexec/vendor/bin/pypkjs" PEBBLE_TOOLCHAIN_PATH="/usr/local/Cellar/pebble-toolchain/2.0/arm-cs-tools/bin" PEBBLE_IS_HOMEBREW="1" exec "/usr/local/Cellar/pebble-sdk/4.0/libexec/bin/pebble" "$@"

```
export PYTHONPATH="/usr/local/Cellar/pebble-sdk/4.0/libexec/vendor/lib/python2.7/site-packages:/usr/local/Cellar/pebble-sdk/4.0/libexec/lib/python2.7/site-packages"
```

* Run the Bridge with the uri to your Android device and the emulator on localhost  

`python appmsgbridge.py ws://192.168.0.6:9011 ws://localhost:52377`


Known Limitations
-
* The Android side only sends through app messages and ack and nack
* If your app stops communicating when it thinks the Pebble is disconnected you will have to override this.
* Reliabilty is not 100% - there are a fair few SendFails from the Pebble...
* If things stop working, you may need to restart your pebble app
and/or the emu
