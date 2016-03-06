# encoding: utf8

"""

异步RPC

接口

    c = rpc.Client(host, port)
    reqid = c.req(service, method, *args, **kw, on_resp)

    def on_resp(reqid, resp):
        pass

    ---

    s = rpc.Server(host, port)
    s.add_service(name, service)

TODO
    循环引用

"""

from json import loads, dumps
from struct import pack, unpack

import tcp
import log
import weakref

LENGTH = 2

class Server(object):

    inst = weakref.WeakValueDictionary()

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.name = "rpcs(%s:%d)" % (host, port)
        self.sock = tcp.listen(host, port, self._on_server_data, self._on_server_close)
        self.services = {}

        self.inst[host, port] = self

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name

    def get_service(self, name):
        if name not in self.services:
            log.error("%s get_service %s not in", self, name)
            return 
        return self.services[name]

    def add_service(self, name, service):
        if name in self.services:
            log.error("%s add_service %s %s already", self, name, service)
            return 
        log.info("%s add_service %s %s", self, name, service)
        self.services[name] = service

    def remove_service(self, name):
        if name not in self.services:
            log.error("%s remove_service %s not in", self, name)
            return 
        log.info("%s remove_service %s", self, name)
        return self.services.pop(name)

    def info(self):
        return [self.host, self.port, self.services.keys()]

    def _on_server_data(self, sock):
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

        for reqid, servicename, method, args, kw, need_result in resps:
            try:
                service = self.services[servicename]
            except KeyError:
                log.error("%s not found %s %s %s %s %s", self, servicename, reqid, method, args, kw)
                continue
            try:
                ret = getattr(service, method)(*args, **kw)
                if need_result: self._resp(sock, reqid, 1, ret)
            except Exception, err:
                if need_result: self._resp(sock, reqid, 0, repr(err))

    def _resp(self, sock, reqid, rs, ret):
        req = [reqid, rs, ret]
        json = dumps(req)
        n = len(json)
        buff = pack(">H%ds" % n, n, json)
        sock.send(buff)
        return reqid
    
    def _on_server_close(self, sock):
        pass

    def req(self, service, method, args=(), kw=None, on_resp=None):
        try:
            service = self.services[servicename]
        except KeyError:
            log.error("%s server req not found %s %s %s %s %s", self, servicename, reqid, method, args, kw)
            return 
        try:
            ret = getattr(service, method)(*args, **kw)
            if on_resp: on_resp(1, ret)
        except Exception, err:
            if on_resp: on_resp(0, repr(err))

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
    
    host, port = "127.0.0.1", 10471

    if iss:
        class An(object):

            def ko(self):
                return "o"

            def echo(self, x):
                if self.x != x -1:
                    import pdb; pdb.set_trace() 
                else:
                    self.x = x
                return x

        an = An()
        an.x = 0

        rs = Server(host, port)
        rs.add_service("an", an)
    
    if isc:
        nl = [0]
        def on_resp(reqid, resp):
            # print resp
            nl[0] += 1
            if resp != nl[0]:
                print "err", resp, nl
            if nl[0] % 10000 == 0:
                import time; print time.time(), nl, resp
            # print "on_resp", reqid, resp

        rc = Client(host, port)

    n = 0
    while True:
        # if isc: reqid = rc.req("an", "ko", on_resp=on_resp)
        n += 1
        if isc: reqid = rc.req("an", "echo", (n, ),  on_resp=on_resp)
        tcp.poll()

