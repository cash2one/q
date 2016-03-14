# encoding: utf8

from json import loads, dumps
from struct import pack, unpack

import etcp as tcp
import log
import weakref

dbs = {}
dbs[0] = {}

class Server(object):

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.name = "redis(%s:%d)" % (host, port)
        self.sock = tcp.listen(host, port, self._on_server_data, self._on_server_close)
        self.services = {}

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name

    def _on_server_data(self, sock):
        data = "".join(sock.read_buff)
        print "recv", repr(data)
        sock.read_buff = []

        resps = []

        begin = 0

        #NOTE *%d\r\n%s\r\n >= 7
        dend = len(data)
        if dend < 7:
            return 

        index = 1
        length = len(data)
        while True:
            if data[index:index+2]=="\r\n":
                break
            index += 1
            if index+2 > length:
                return
        args_amount = long(data[1:index])
        index += 2 # \r\n
        args = []

        # *2\r\n$4\r\nabcd\r\n$3\r\nabc\r\n
        for i in range(args_amount):
            if index+1==length:
                return 
            index += 1 # $
            r_index = index
            while True:
                if data[r_index:r_index+2]=="\r\n":
                    break
                r_index += 1
                if r_index+2 > length:
                    return
            args_length = long(data[index:r_index])
            if r_index+2+args_length+2 > length:
                return
            arg = data[r_index+2:r_index+2+args_length]
            args.append(arg)
            index = r_index+2+args_length+2

        print "~~~~~~~~~~", args
        self.execute_command(sock, *args)

        data = data[index:]
        if data:
            sock.read_buff.append(data)
        print "~~~", repr(data)
        print "~~", repr(sock.read_buff)

    def execute_command(self, sock, *args):
        command, args = args[0], args[1:]
        db = dbs[0]
        getattr(self, command)(sock, db, *args)

    def get(self, sock, db, key):
        value = db.get(key)
        self.reply_string(sock, value)

    def set(self, sock, db, key, value):
        db[key] = value
        self.reply_ok(sock)

    def reply_ok(self, sock):
        sock.send("+OK\r\n")

    def reply_string(self, sock, string):
        print "~~~~~~~~~~~~~~~~~~~~~~~~~~", sock, string
        if string is None:
            sock.send("$-1\r\n")
        elif isinstance(string, int):
            sock.send(":%s\r\n", string)
        else:
            data = "$%d\r\n%s\r\n "% (len(string), string)
            sock.send(data)

    def _on_server_close(self, sock):
        pass

if __name__ == "__main__":

    import sys; print sys.argv

    host, port = "127.0.0.1", 10471

    rs = Server(host, port)
    
    while True:
        tcp.poll()


