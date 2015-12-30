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
            ws.send(json.dumps(out))
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
    ws.send(json.dumps(msg))

def pb_handle_nack(tid, uuid):
    msg={'txid':tid,'acknack':'nack'}
    ws.send(json.dumps(msg))


# Handlers for WebSocket events
def ws_on_message(ws, message):
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

def ws_on_error(ws, error):
    print(error)

def ws_on_close(ws):
    print("### AppMsgBridge Connection closed ###")

def ws_on_open(ws):
    print("### AppMsgBridge Connection open ###")

# main
print("AppMsg Bridge\n arg1 = Android ws://PhoneIP:Port (default 9011)\n arg2 = ws://PebbleEmuIP:Port (see output from pebble install --emulator basalt -v)");
print("e.g. python bridge.py ws://192.168.1.102:9011 ws://localhost:52377")
if len(sys.argv)!=3:
    exit()

logging.basicConfig()

# connect to the pebble and register for AppMessage events
pebble = PebbleConnection(WebsocketTransport(sys.argv[2]))
pebble.connect()
print("### Pebble Connection open ###")
appmessage = BridgeAppMessageService(pebble)
appmessage.register_handler("appmessage", pb_handle_message)
appmessage.register_handler("ack", pb_handle_ack)
appmessage.register_handler("nack", pb_handle_nack)
pebble.run_async()

# connect to the Android side of the bridge
# websocket.enableTrace(True)
ws = websocket.WebSocketApp(sys.argv[1],
                            on_message = ws_on_message,
                            on_error = ws_on_error,
                            on_close = ws_on_close)
ws.on_open = ws_on_open
ws.run_forever()



