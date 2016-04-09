# The MIT License (MIT)
# Copyright (c) 2016 finebyte
# AppMsgTools for Pebble App Message
# Allows AppMessages to be sent to the Pebble emu (and other ws endpoints)
# from Android (needs Android side of bridge to be installed)
# from File / Stdin
# from Simple Web Interface
#
# Pre Reqs
# pebble tool and libpebble2
# SimpleWebSocketServer for the Web interface (will only load when using -server)
# See: https://github.com/dpallot/simple-websocket-server
#
# To Run:
# Set your Pebble PYTHON_PATH (see inside the pebble tool using cat `which pebble`)
#
# Message format is as used internally by Pebble Android Intents
# e.g.
# {"uuid":"XXX","txid":3,"msg_data":[
#  {"key":"1", "type":"string", "width":0, "value":"I am a string"},
#  {"key":"2", "type":"int", "width":1, "value":"1"},
#  {"key":"3", "type":"int", "width":4, "value":"1"}
# ]}
# where type = string, int, uint and width = width of the int/uint (1,2,4)
# e.g. int8 = type:int, width:1 uint32 = type:uint, width:4
#

from libpebble2.communication import PebbleConnection
from libpebble2.communication.transports.websocket import WebsocketTransport
from libpebble2.services.appmessage import *
from libpebble2.protocol.appmessage import *
from libpebble2.events.mixin import EventSourceMixin
from uuid import UUID
import argparse
import websocket
import sys
import logging
import json
import struct
import base64
import time
import tempfile
import os
import threading
import SimpleHTTPServer
import SocketServer
from BaseHTTPServer import BaseHTTPRequestHandler
from argparse import RawTextHelpFormatter
import cgi


# Subclass of the standard Pebble AppMessageService
# to access the meta data on Integer types
# The initial version was copied directly from
# https://github.com/pebble/libpebble2/blob/master/libpebble2/services/appmessage.py
#
class BridgeAppMessageService(AppMessageService):
    def _handle_message(self, packet):
        assert isinstance(packet, AppMessage)
        if isinstance(packet.data, AppMessagePush):
            message = packet.data
            # Break out message and send onto bridge
            msg_data=[]
            out={'txid':packet.transaction_id,'uuid':str(message.uuid), 'msg_data':msg_data}
            for t in message.dictionary:
                assert isinstance(t, AppMessageTuple)
                if t.type == AppMessageTuple.Type.CString:
                    v=t.data.split(b'\x00')[0].decode('utf-8', errors='replace')
                    msg_data.append({'key':t.key,'value':v, 'type':'string','length':0})
                if t.type == AppMessageTuple.Type.ByteArray:
                    v=base64.b64encode(t.data)
                    msg_data.append({'key':t.key,'value':v, 'type':'bytes','length':0})
                if t.type == AppMessageTuple.Type.Int:
                    v= struct.unpack(self._type_mapping[(t.type, t.length)], t.data)
                    msg_data.append({'key':t.key,'value':v, 'type':'int','length':t.length})
                if t.type == AppMessageTuple.Type.Uint:
                    v= struct.unpack(self._type_mapping[(t.type, t.length)], t.data)
                    msg_data.append({'key':t.key,'value':v, 'type':'uint','length':t.length})
            ws_send(json.dumps(out))
            # End Bridge Code
            result = {}
            for t in message.dictionary:
                assert isinstance(t, AppMessageTuple)
                if t.type == AppMessageTuple.Type.ByteArray:
                    result[t.key] = bytearray(t.data)
                elif t.type == AppMessageTuple.Type.CString:
                    result[t.key] = t.data.split(b'\x00')[0].decode('utf-8', errors='replace')
                else:
                    result[t.key], = struct.unpack(self._type_mapping[(t.type, t.length)], t.data)
            self._broadcast_event("appmessage", packet.transaction_id, message.uuid, result)
            # This is an auto ACK which might want to be removed
            self._pebble.send_packet(AppMessage(transaction_id=packet.transaction_id, data=AppMessageACK()))
        else:
            if packet.transaction_id in self._pending_messages:
                uuid = self._pending_messages[packet.transaction_id]
                del self._pending_messages[packet.transaction_id]
            else:
                uuid = None
            if isinstance(packet.data, AppMessageACK):
                self._broadcast_event("ack", packet.transaction_id, uuid)
            elif isinstance(packet.data, AppMessageNACK):
                self._broadcast_event("nack", packet.transaction_id, uuid)

# Handlers for Pebble AppMessageService
def pb_handle_message(tid, uuid, dictionary):
    # This handler does nothing apart from print
    # As the ws send is done in the code above
    # (i.e. it could be removed)
    print("pb rx %s" % dictionary)

def pb_handle_ack(tid, uuid):
    msg={'txid':tid,'acknack':'ack'}
    ws_send(json.dumps(msg))

def pb_handle_nack(tid, uuid):
    msg={'txid':tid,'acknack':'nack'}
    ws_send(json.dumps(msg))

# Utility to send on ws or server ws depending on which is available
def ws_send(msg):
    if (sws is not None):
        #    if (isinstance(sws,WebSocket)):
        try:
            sws.sendMessage(unicode(msg,'utf-8'))
        except:
            pass
    else:
        try:
            ws.send(msg)
        except:
            pass

# Handler for inbound json messages (from ws or file etc)
def ws_on_message(ws, message):
    print("ws rx: %s" % message)
    try:
        msg=message.decode('utf8')
    except:
        msg=message
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

# Handlers for (client) ws
def ws_on_error(ws, error):
    print(error)

def ws_on_close(ws):
    print("### AppMsgBridge Connection closed ###")

def ws_on_open(ws):
    print("### AppMsgBridge Connection open ###")


# Webserver handler
class PostHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    def do_POST(self):
        # Begin the response
        self.send_response(200)
        self.end_headers()
        # read the incoming data
        msg=self.rfile.read(int(self.headers.getheader('Content-Length')))
        # write the incoming data to the filename given as the path
        f=open("."+self.path,"w")
        f.write(msg)
        f.close()
        del msg

def start_webserver():
    print("### WebServer Starting on http://localhost:8080 ###")
    from BaseHTTPServer import HTTPServer
    server = HTTPServer(('localhost', 8080), PostHandler)
    server.serve_forever()


# Check if emu process is running
def is_process_running(process_id):
    try:
        os.kill(process_id, 0)
        return True
    except OSError:
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=RawTextHelpFormatter)
    parser.add_argument('-i', required=True, metavar='source',help='Source of Input data \nserver = Start WSS server (for web page)\nws://192.168.1.102:9011 = Connect to ws endpoint\n (e.g. the Bridge Android app)\nfilename = Read from a file with JSON messages one per line\n- = Read from stdin with JSON messages one per line')
    parser.add_argument('-o', required=True, metavar='dest', help='Destination address of pebble / emu\naplite | basalt | chalk = Find the relevant Pebble emu\nws://localhost:52377 = Connect to ws endpoint')
    args=parser.parse_args()

    if ("ws://" in args.o):
        emu_url=args.o;
    else:
        try:
            e = json.load(open(tempfile.gettempdir()+"/pb-emulator.json"))
            basalt = e[args.o]
        except IOError:
            print("AppMsgBridge: Emu file not found (not running)")
            exit()
        except KeyError:
            print("AppMsgBridge: Emu data not found (not running) : " + args.o)
            exit()
    
        emuvsn=basalt.keys()[0]
        pid=basalt[emuvsn]['pypkjs']['pid']
        port=basalt[emuvsn]['pypkjs']['port']
        if (not is_process_running(pid)):
            print("AppMsgBridge: Emu process not found (not running) : " + args.o)
            exit()
        emu_url = "ws://localhost:"+str(port)

    logging.basicConfig()
    sws = None

    # connect to the pebble and register for AppMessage events
    print("### Connecting to " + args.o + " on " + emu_url + " ###")
    pebble = PebbleConnection(WebsocketTransport(emu_url))
    pebble.connect()
    print("### Pebble Connection open ###")
    appmessage = BridgeAppMessageService(pebble)
    appmessage.register_handler("appmessage", pb_handle_message)
    appmessage.register_handler("ack", pb_handle_ack)
    appmessage.register_handler("nack", pb_handle_nack)
    pebble.run_async()


    if ("server" in args.i):
        # Requires SimpleWebSocketServer from
        # https://github.com/dpallot/simple-websocket-server
        from SimpleWebSocketServer import SimpleWebSocketServer, WebSocket
        #Handler for server ws
        class SimpleWSServer(WebSocket):
            def handleMessage(self):
                ws_on_message(None,self.data)
            def handleConnected(self):
                global sws
                sws=self
                print '### SWS connected ', self.address, ' ###'
    
            def handleClose(self):
                print '### SWS closed ', self.address, ' ###'
        # Start WebServer
        t=threading.Thread(target=start_webserver)
        t.setDaemon(True)
        t.start()
        # Start WebSocketServer
        print("### WebSocket Server Starting on ws://localhost:9000 ###")
        server = SimpleWebSocketServer('', 9000, SimpleWSServer)
        server.serveforever()
    elif ("ws://" in args.i):
        # connect to the Android side of the bridge
        # websocket.enableTrace(True)
        ws = websocket.WebSocketApp(args.i,
                            on_message = ws_on_message,
                            on_error = ws_on_error,
                            on_close = ws_on_close)
        ws.on_open = ws_on_open
        ws.run_forever()
    else:
        if (args.i=='-'):
            f=sys.stdin
            name='stdin'
        else:
            f=open(args.i)
            name=args.i
        print("### Bridge Reading from " + name + " ###")
        while 1:
            msg = f.readline()
            try:
                if msg and msg.strip():
                    ws_on_message(None,msg)
                    # sleep so as not to flood the message queue when piping from a file
                    time.sleep(0.5)
                else:
                    exit()
            except ValueError:
                print("FileMsgBridge: invalid json input " + msg)
                exit()


