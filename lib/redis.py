# encoding: utf8

"""
"""

from json import loads, dumps
from struct import pack, unpack

import etcp as tcp
import log
import weakref

class Redis(object):

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.name = "redis(%s:%d)" % (host, port)
        self.sock = tcp.listen(host, port, self._on_server_data, self._on_server_close)
        self.dbs = {0:{}}

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name

    def _on_server_data(self, sock):
        data = "".join(sock.read_buff)
        sock.read_buff = []
        reqs = self.reqs(data)
        print "~~~~~~~~", reqs
        self._handle_request(sock, reqs)

    def _on_server_close(self, ):
        pass

    def reqs(self, data):
        begin = 0
        dend = len(data)

        reqs = []
        while True:
            if begin >= dend:
                return reqs
            if data[begin] != "*":
                return reqs

            numberi = begin
            while numberi < dend:
                if data[numberi] == "\n":
                    numberi -= 1
                    break
                numberi += 1
            else:
                return reqs

            number = int(data[begin+1:numberi])
            sbegin = begin+numberi+2
            print number, repr(data[sbegin:])
            args = []
            for _ in xrange(number):
                if data[sbegin] == "$":

                    ni = sbegin + 1
                    while ni < dend:
                        if data[ni] == "\n":
                            ni -= 1
                            break
                        ni += 1
                    else:
                        return reqs
                    number = int(data[sbegin+1:ni])
                    if ni + 2 + number < dend:
                        args.append(data[ni + 2:ni+2+number])
                        sbegin = ni+2+number+2
                        print args, 999
                    else:
                        return reqs
            reqs.append(args)
            begin = sbegin

        return reqs

    def _handle_request(self, sock, reqs):
        for req in reqs:
            if req[0] == "get":
                value = self.dbs[0].get(req[1], None)
                self.resp(sock, value)
            elif req[0] == "set":
                key = req[1]
                value = req[2]
                self.dbs[0][key] = value
                sock.send("+OK\r\n")

    def resp(self, sock, value):
        n = len(value)
        sock.send("$%s\r\n%s\r\n" % (n, value))

if __name__ == "__main__":

    import sys; print sys.argv

    rs = Redis("127.0.0.1", 8880)
    
    while True:
        tcp.poll()

