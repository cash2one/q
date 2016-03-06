
import log

class Registor(object):

    def __init__(self):
        self.services ={}

    def add(self, host, port, names):
        key = host, port
        if key in self.services:
            log.error("register add %s aleady", key)
            return 
        self.services[key] = names

    def remove(self, host, port):
        key = host, port
        if key not in self.services:
            log.error("register remove %s not in", key)
            return 0
        self.services.pop(key)
        return 1

    def query(self):
        print "*******", self.services
        return self.services

def setup(rc):
    rc.req("reg", "query", on_resp=setup_callback)

def setup_callback(reqid, resp):
    print "cb", reqid, resp
    import pdb; pdb.set_trace() 
    pass

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
        rs.add_service("a1", a1)
        rs.add_service("a2", a2)

        rc = rpc.Client(host, reg_port)
        rc.req("reg", "add", rs.info())

    if isb:
        port += 3

        class B(object): 
            def b(self): return "b"

        b1 = B()
        b2 = B()

        rs = rpc.Server(host, port)
        rs.add_service("b1", b1)
        rs.add_service("b2", b2)

        rc = rpc.Client(host, reg_port)
        rc.req("reg", "add", rs.info())

    while True:
        tcp.poll()

        if ism:
            print reg.services

        if isa or isb:
            setup(rc)

