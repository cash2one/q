# encoding: utf8

"""

接口
    dist.name.method()
"""


import log
import rpc

class Registor(object):

    def __init__(self):
        self.services ={}

    def add(self, host, port, names):
        key = "%s:%s" % (host, port)
        if key in self.services:
            log.error("register add %s aleady", key)
            return 
        self.services[key] = names

    def remove(self, host, port):
        key = "%s:%s" % (host, port)
        if key not in self.services:
            log.error("register remove %s not in", key)
            return 0
        self.services.pop(key)
        return 1

    def query(self):
        return self.services

def setup(rc):
    rc.req("reg", "query", on_resp=setup_callback)

def setup_callback(reqid, services):
    G = globals()
    for key, names in services.items():
        host, port = key.split(":")
        port = int(port)
        for name in names:
            if name in G:
                log.info("dist setup_callback %s %s aleady %s", key, name, G[name])
                continue
            proxy = rpc.get_service_of_client(host, port, name)
            log.info("dist new service %s %s", key, name)
            G[name] = proxy

if __name__ == "__main__":

    import sys; print sys.argv
    ism = "m" in sys.argv
    isa = "a" in sys.argv
    isb = "b" in sys.argv

    import rpc
    import tcp

    host, port = "127.0.0.1", 10471
    reg_port = port + 1

    if ism:
        port = reg_port
        reg = Registor()
        rs = rpc.Server(host, port)
        rs.add_service("reg", reg)

    if isa:
        port += 2

        class A(object): 
            def a(self): return "a"

        a1 = A()
        a2 = A()

        rs = rpc.Server(host, port)
        rs.add_service("ra1", a1)
        rs.add_service("ra2", a2)

        rc = rpc.Client(host, reg_port)
        rc.req("reg", "add", rs.info())

    if isb:
        port += 3

        class B(object): 
            def b(self): return "b"

        b1 = B()
        b2 = B()

        rs = rpc.Server(host, port)
        rs.add_service("rb1", b1)
        rs.add_service("rb2", b2)

        rc = rpc.Client(host, reg_port)
        rc.req("reg", "add", rs.info())

    while True:
        tcp.poll()

        if ism:
            pass

        if isa or isb:
            import random
            if random.random() < 0.2:
                setup(rc)

        if isa:
            def on_resp(*args):
                print "resp", args
            try:
                print "!!!", ra1, ra2
                rb1.b(on_resp=on_resp)
                rb2.b(on_resp=on_resp)
            except Exception, err:
                print "!!!", err

