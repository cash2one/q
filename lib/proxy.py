# encoding: utf8

"""

"""

from json import loads, dumps
from struct import pack, unpack

import etcp as tcp
import log
import weakref

class Proxy(object):

    def __init__(self, host, port, tarhost, tarport):
        self.host = host
        self.port = port
        self.tarhost = tarhost
        self.tarport = tarport

        self.sock = tcp.listen(host, port, self._on_server_data, self._on_server_close)

        self.to_ = {}
        self.from_ = {}

    def _on_server_data(self, sock):
        data = "".join(sock.read_buff)
        #print "~~~~~~~~~", repr(data)
        sock.read_buff = []
        try:
            to_= self.to_[sock]
        except KeyError:
            to_ = self.to_[sock] = tcp.connect(self.tarhost, self.tarport, self.on_c_data, self.on_c_close)
            self.from_[to_] = sock
        to_.send(data)

    def _on_server_close(self, to_):
        pass

    def on_c_data(self, to_):
        data = "".join(to_.read_buff)
        #print "~~~~", repr(data)
        to_.read_buff = []

        from_ = self.from_[to_]
        from_.send(data)

    def on_c_close(self, sock):
        pass

class Client(object):

    inst = weakref.WeakValueDictionary()

    def __init__(self, host, port):
        self.name = "rpcc(%s:%d)" % (host, port)
        self.sock = tcp.connect(host, port, self.on_client_data, self.on_client_close)

        self.nextreqid = 1
        self.maxreqid = 0xffffffff

        self.requests = {}

        self.inst[host, port] = self

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

    def req(self, service, method, args=(), kw=None, on_resp=None):
        if kw is None: kw = {}
        # print "req", self, service, method, args, kw, on_resp
        reqid = self.nextreqid
        self.nextreqid += 1
        if self.nextreqid >= self.maxreqid:
            self.nextreqid = 1
            # TODO error check
        need_result = 0
        if on_resp:
            need_result = 1
            self.requests[reqid] = on_resp
        req = [reqid, service, method, args, kw, need_result]
        json = dumps(req)
        # print "~~", repr(json)
        n = len(json)
        buff = pack(">H%ds" % n, n, json)
        # print buff, len(buff), len(json)
        self.sock.send(buff)
        return reqid

    def on_client_data(self, sock):
        data = "".join(sock.read_buff)
        sock.read_buff = []
        resps = []
        while True:
            n = len(data)
            if n <= LENGTH:
                break
            length,  = unpack(">H", data[:LENGTH])
            end = length + LENGTH
            if n >= end:
                json = data[LENGTH:end]
                resps.append(loads(json))
                data = data[end:]
            else:
                break
        if data:
            sock.read_buff.append(data)
        for reqid, rs, ret in resps:
            try:
                on_resp = self.requests.pop(reqid)
            except KeyError:
                log.error("%s not found %s %s %s", self, reqid, rs, ret)
                continue
            on_resp(rs, ret)
    
    def on_client_close(sock):
        pass

class LocalProxy(object):

    def __init__(self, service):
        self._service = service

    def __getattr__(self, attr):
        def _func(args=(), kw=None, on_resp=None):
            if kw is None: kw = {}
            try:
                ret = getattr(self._service, attr)(*args, **kw)
                on_resp(1, ret)
            except Exception, err:
                on_resp(0, ret)
        self.__dict__[attr] = _func
        return _func

class RemoteProxy(object):

    def __init__(self, client, servicename):
        self._client = client
        self._name = servicename

    def __getattr__(self, attr):
        def _func(args=(), kw=None, on_resp=None):
            if kw is None: kw = {}
            return self._client.req(self._name, attr, args, kw, on_resp)
        self.__dict__[attr] = _func
        return _func

def get_service_of_client(host, port, servicename):
    client = get_client(host, port)
    if isinstance(client, Server):
        return LocalProxy(client.get_service(servicename))
    return RemoteProxy(client, servicename)

def get_client(host, port):
    try:
        return Server.inst[host, port]
    except KeyError:
        pass
    try:
        return Client.inst[host, port]
    except KeyError:
        return Client(host, port)

def get_server(host, port):
    try:
        return Server.inst[host, port]
    except KeyError:
        return Server(host, port)

if __name__ == "__main__":

    import sys; print sys.argv
    iss = "c" not in sys.argv
    isc = "s" not in sys.argv

    if iss and 0: 
        import profile; profile.install()
    
    host, port = "127.0.0.1", 8888
    tarhost, tarport = "127.0.0.1", 6379

    rs = Proxy(host, port, tarhost, tarport)
    
    while True:
        tcp.poll()

