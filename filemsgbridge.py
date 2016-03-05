from libpebble2.communication import PebbleConnection
from libpebble2.communication.transports.websocket import WebsocketTransport
from libpebble2.services.appmessage import *
from libpebble2.protocol.appmessage import *
from libpebble2.events.mixin import EventSourceMixin
from uuid import UUID
import websocket
import sys
import logging
import json
import struct
import base64
import time
import tempfile
import os


# Handlers for Pebble AppMessageService
def pb_handle_message(tid, uuid, dictionary):
    # This handler does nothing apart from print
    # As the ws send is done in the code above
    # (i.e. it could be removed)
    print("pb rx %s" % dictionary)

def pb_handle_ack(tid, uuid):
    msg={'txid':tid,'acknack':'ack'}
    print("pb ack %s" % json.dumps(msg))

def pb_handle_nack(tid, uuid):
    msg={'txid':tid,'acknack':'nack'}
    print("pb nack %s" % json.dumps(msg))


# Handlers for WebSocket events
def processmsg(message):
    msg=message.decode('utf8')
    print("ws rx: %s" % msg)
    m=json.loads(msg)
    tid = int(m['txid'].encode("ascii","ignore"))
    # Deal with tid = -1 which is a default in PebbleKit and breaks here
    if (tid==-1):
        tid=255
    if ('acknack' in m):
        if (m['acknack']=='ack'):
            pebble.send_packet(AppMessage(transaction_id=tid, data=AppMessageACK()))
        else:
            pebble.send_packet(AppMessage(transaction_id=tid, data=AppMessageNACK()))
    else:
        tuples={}
        for t in m['msg_data']:
            k=t['key']
            # Check key is an int otherwise convert (bug somewhere in the sender...)
            if isinstance(k, int)==False:
                k=int(k)
            if t['type']=='string':
                tuples[k]=CString(t['value']);
            elif t['type']=='int':
                widthmap = {
                    1: Int8,
                    2: Int16,
                    4: Int32}
                length = t['length']
                tuples[k]=widthmap[length](int(t['value']))
            elif t['type']=='uint':
                widthmap = {
                    1: Uint8,
                    2: Uint16,
                    4: Uint32}
                length = t['length']
                tuples[k]=widthmap[length](int(t['value']))
            elif t['type']=='bytes':
                b = base64.b64decode(t['value'])
                tuples[k]=ByteArray(b);
        appmessage.send_message(UUID(m['uuid']),tuples)

def is_process_running(process_id):
    try:
        os.kill(process_id, 0)
        return True
    except OSError:
        return False

# main

if len(sys.argv)!=2:
    print("FileMsgBridge\n arg1 = ws endpoint (ws://host:port) or Emulator type (aplite | basalt | chalk)")
    print("e.g. python filemsgbridge.py aplite\n")
    exit()

if ("ws" in sys.argv[1]):
    emu_url=sys.argv[1];
else:
    try:
        e = json.load(open(tempfile.gettempdir()+"/pb-emulator.json"))
        basalt = e[sys.argv[1]]
    except IOError:
        print("FileMsgBridge: Emu file not found (not running)")
        exit()
    except KeyError:
        print("FileMsgBridge: Emu data not found (not running) : " + sys.argv[1])
        exit()

    emuvsn=basalt.keys()[0]
    pid=basalt[emuvsn]['pypkjs']['pid']
    port=basalt[emuvsn]['pypkjs']['port']
    if (not is_process_running(pid)):
        print("FileMsgBridge: Emu process not found (not running) : " + sys.argv[1])
        exit()
    emu_url = "ws://localhost:"+str(port)


logging.basicConfig()

# connect to the pebble and register for AppMessage events
#
print("### Connecting to " + sys.argv[1] + " on " + emu_url + " ###")
pebble = PebbleConnection(WebsocketTransport(emu_url))
pebble.connect()
print("### Pebble Connection open ###")
appmessage = AppMessageService(pebble)
appmessage.register_handler("appmessage", pb_handle_message)
appmessage.register_handler("ack", pb_handle_ack)
appmessage.register_handler("nack", pb_handle_nack)
pebble.run_async()

# Read the input json from stdin
while 1:
    msg = sys.stdin.readline()
    try:
        if msg and msg.strip():
            processmsg(msg)
            # sleep so as not to flood the message queue when piping from a file
            time.sleep(0.5)
        else:
            exit()
    except ValueError:
        print("FileMsgBridge: invalid json input " + msg)
        exit()






