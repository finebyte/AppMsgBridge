from pebblecomm.pebble import Pebble, AppMessage
import struct
from uuid import UUID
import json
import sys
import uuid
import base64
from autobahn.twisted.websocket import WebSocketServerProtocol, \
    WebSocketServerFactory

class MyServerProtocol(WebSocketServerProtocol):

    def __init__(self):
        self.p=Pebble()
        self.connect()
        self.register()
    
    def onConnect(self, request):
        print("Client connecting: {0}".format(request.peer))

    def onOpen(self):
        print("WebSocket connection open.")

    def onMessage(self, payload, isBinary):
        if isBinary:
            print("Binary message received: {0} bytes".format(len(payload)))
        else:
            msg=payload.decode('utf8')
            print("ws rx: %s" % msg)
            m=json.loads(msg)
            tid = int(m['txid'].encode("ascii","ignore"))
            # Deal with tid = -1 which is a default in PebbleKit and breaks here
            if (tid==-1):
                    tid=255
            if ('acknack' in m):
                if (m['acknack']=='ack'):
                    self.p._send_message("APPLICATION_MESSAGE", struct.pack('<BB', 0xFF, tid))  # ACK
                    print("pebble tx ack")
                else:
                    self.p._send_message("APPLICATION_MESSAGE", struct.pack('<BB', 0x7F, tid))  # NACK
                    print("pebble tx nack")
            else:
                tuples=[]
                appmessage=AppMessage()
                for t in m['msg_data']:
                    k=t['key']
                    # Check key is an int otherwise convert (bug somewhere in the sender...)
                    if isinstance(k, int)==False:
                        k=int(k)
                    if t['type']=='string':
                        v=t['value'].encode("utf8","ignore")
                        tuples.append(appmessage.build_tuple(k,"CSTRING",v+'\x00'))
                    elif t['type']=='int':
                        widthmap = {
                            1: 'b',
                            2: 'h',
                            4: 'i'}
                        length = t['length']
                        v = struct.pack('<%s' % widthmap[length], int(t['value']))
                        print("ws int "+v+" length "+widthmap[length])
                        tuples.append(appmessage.build_tuple(k,"INT",v))
                    elif t['type']=='uint':
                        widthmap = {
                            1: 'B',
                            2: 'H',
                            4: 'I'}
                        length = t['length']
                        v = struct.pack('<%s' % widthmap[length], int(t['value']))
                        print("ws int "+v+" length "+widthmap[length])
                        tuples.append(appmessage.build_tuple(k,"UINT",v))
                    elif t['type']=='bytes':
                        b = base64.b64decode(t['value'])
                        tuples.append(appmessage.build_tuple(k,"BYTE_ARRAY",b))
                d=appmessage.build_dict(tuples)
                # This is ugly...presumably there is a better way...
                app_uuid=uuid.UUID(m['uuid']).hex.decode('hex')
                pm=appmessage.build_message(d,"PUSH",app_uuid,struct.pack('B',tid))
                self.p._send_message("APPLICATION_MESSAGE",pm)
                print("pebble tx")  
            # echo back message verbatim
            # self.sendMessage(payload, isBinary)

    def onClose(self, wasClean, code, reason):
        print("WebSocket connection closed: {0}".format(reason))

    def connect(self):
        print "Pebble connection starting..."
        self.p.connect_via_websocket('localhost',12342)

    def register(self):
        print "Pebble connection registering..."
        self.p.register_endpoint("APPLICATION_MESSAGE",self.handle_appmessage)
    
    def handle_message(self,tid, uuid, encoded_dict):
        print 'pebble rx appmsg'
        if uuid != uuid: # used to check vs self.uuid
            print "Discarded message for %s (expected %s)" % (uuid, self.uuid)
            self.p._send_message("APPLICATION_MESSAGE", struct.pack('<BB', 0x7F, tid))  # ACK
            return
        try:
            tuple_count, = struct.unpack_from('<B', encoded_dict, 0)
            offset = 1
            msg_data=[]
            out={'txid':tid,'uuid':str(uuid), 'msg_data':msg_data}
            for i in xrange(tuple_count):
                k, t, l = struct.unpack_from('<IBH', encoded_dict, offset)
                offset += 7
                if t == 0:  # BYTE_ARRAY
                    v='array'
                elif t == 1:  # CSTRING
                    v, = struct.unpack_from('<%ds' % l, encoded_dict, offset)
                    try:
                        v = v[:v.index('\x00')]
                        msg_data.append({'key':k,'value':v, 'type':'string'})
                    except ValueError:
                        pass
                elif t in (2, 3):  # UINT, INT
                    widths = {
                        (2, 1): 'B',
                        (2, 2): 'H',
                        (2, 4): 'I',
                        (3, 1): 'b',
                        (3, 2): 'h',
                        (3, 4): 'i',
                    }
                    v, = struct.unpack_from('<%s' % widths[(t, l)], encoded_dict, offset)
                    if t == 2:
                        msg_data.append({'key':k,'value':v, 'type':'uint','length':l})
                    if t == 3:
                        msg_data.append({'key':k,'value':v, 'type':'int','length':l})                        
                else:
                    print 'Received bad appmessage dict.'
                offset += l
        except:
            self.p._send_message("APPLICATION_MESSAGE", struct.pack('<BB', 0x7F, tid))  # NACK
            raise
        else:
            print("ws tx: %s" % json.dumps(out))
            reactor.callFromThread(self.sendMessage,json.dumps(out),False)
            #self.p._send_message("APPLICATION_MESSAGE", struct.pack('<BB', 0xFF, tid))  # ACK
        return

    def handle_ack(self, command, tid):
        print 'pebble rx acknack'        
        msg={'txid':tid}
        if command == 0x7f:  # NACK
            msg['acknack']='nack'
        elif command == 0xff:  # ACK
            msg['acknack']='ack'
        print("ws tx: %s" % json.dumps(msg))
        reactor.callFromThread(self.sendMessage,json.dumps(msg),False)

    
    def handle_appmessage(self,endpoint, data):
        command, tid = struct.unpack_from("BB", data, 0)
        if command in (0x7f, 0xff):
            self.handle_ack(command, tid)
        elif command == 0x01:
            target_uuid = UUID(bytes=data[2:18])
            self.handle_message(tid, target_uuid, data[18:])
        return

if __name__ == '__main__':

    import sys

    from twisted.python import log
    from twisted.internet import reactor
    log.startLogging(sys.stdout)

    factory = WebSocketServerFactory("ws://localhost:9000", debug=False)
    factory.protocol = MyServerProtocol

    reactor.listenTCP(9000, factory)
    reactor.run()
            
