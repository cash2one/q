# encoding: utf8

import etcp as tcp

class Proxy(object):

    def __init__(self, host, port, tarhost, tarport):
        self.host = host
        self.port = port
        self.tarhost = tarhost
        self.tarport = tarport
        self.name = "proxy(%s:%s)" % (tarhost, tarport)

        self.sock = tcp.listen(host, port, self._on_server_data, self._on_server_close)
        self.proxy = {}
        self.s2c = {}

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name

    def _on_server_data(self, sock):
        # TODO: on_connection
        if sock not in self.proxy:
            self.proxy[sock] = tcp.connect(self.tarhost, self.tarport, self.on_s_data, None)
        c = self.proxy[sock]
        self.s2c[c.sock] = sock

        data = "".join(sock.read_buff)
        sock.read_buff = []
        c.send(data)

    def on_s_data(self, sock):
        data = "".join(sock.read_buff)
        sock.read_buff = []
        self.s2c[sock].send(data)

    def _on_server_close(self, sock):
        pass

if __name__ == "__main__":

    import sys; print sys.argv

    host, port = "127.0.0.1", 10471
    thost, tport = "127.0.0.1", 6379

    rs = Proxy(host, port, thost, tport)
    while True:
        tcp.poll()

