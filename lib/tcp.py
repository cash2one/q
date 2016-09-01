# encoding: utf8

"""

异步非阻塞TCP

接口

    def on_connection(sock):
        pass

    def on_close(sock):
        pass

    def on_data(sock):
        print sock, sock.recv_buff

    ---

    sock = tcp.listen(host, port, on_connection, on_data=None, on_close=None, backlog=1024)
    sock.close()


    ---

    sock = tcp.connect(host, port, on_data, on_close, on_connected)
    sock.send(buff)
    sock.close()

实现笔记
    TCP 连接需要监听写事件的条件: 异步连接中 或 有数据需要发送


"""

import log
import socket
import select
import errno

def listen(host, port, on_data=None, on_close=None, backlog=1024):
    log.info("begin tcp listen %s %s %s", host, port, backlog)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setblocking(0)
    sock.bind((host, port))
    sock.listen(backlog)
    return _add_sock(sock, accept=True, on_data=on_data, on_close=on_close)

def connect(host, port, on_data, on_close):
    log.info("begin tcp connection to %s %s", host, port)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setblocking(0)
    sock.connect_ex((host, port))
    return _add_sock(sock, readable=True, writable=True, connecting=True, on_data=on_data, on_close=on_close)

def _f(ss):
    def name(s):
        from_ = "%s:%d" % s.getsockname()
        try:
            to = " - %s:%d" % s.getpeername()
        except:
            to = ""
        return "%s%s" % (from_, to)
    return "[%s]" % ",".join([name(s) for s in ss])

def poll():
    # print "before poll", _f(_reads), _f(_writes), _errors
    reads, writes, erros = select.select(_reads, _writes, _errors, 1)
    # print "end poll", _f(reads), _f(writes), erros

    for readable in reads:
        sock = _socks[readable.fileno()]
        if sock.readable:
            #print "begin recv"
            while True:
                try:
                    data = sock.sock.recv(0xffff)
                    if data:
                        sock.read_buff.append(data)
                        sock.on_data(sock)
                    else:
                        log.info("%s close", sock)
                        if sock.on_close: sock.on_close(sock)
                        sock.beenclosed()

                except socket.error as e:
                    err = e.args[0]
                    if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                        break
            #print "end recv"
        else:
            connection, addr = sock.sock.accept()
            connection.setblocking(0)
            _s = _add_sock(connection, readable=True, writable=True, on_data=sock.on_data)
            log.info("new tcp connection %s", _s)

    for writable in writes:
        sock = _socks[writable.fileno()]
        if sock.connecting:
            sock.connecting = False
            log.info("%s connecting done", sock)

        buff = "".join(sock.write_buff)
        sock.write_buff = []
        while buff:
            try:
                n = sock.sock.send(buff)
                if n < len(buff):
                    if n == 0: 
                        break
                    else:
                        buff = buff[n:]
                else:
                    buff = ""
            except socket.error as e:
                err = e.args[0]
                if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                    sock.write_buff.insert(0, buff)
                    break
                # TODO
                else:
                    1/0
                    pass
        if buff:
            sock.write_buff.append(buff)
        else:
            _writes.remove(sock.sock)

        #print "begin send"
        # while sock.write_buff:
        #     buff = sock.write_buff.pop(0)
        #     try:
        #         n = sock.sock.send(buff)
        #         if n < len(buff):
        #             # log.debug("tcp send %s", n)
        #             if n != 0: buff = buff[n:]
        #             sock.write_buff.insert(0, buff)
        #             break
        #         # log.debug("tcp send %s", n)
        #     except socket.error as e:
        #         err = e.args[0]
        #         if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
        #             sock.write_buff.insert(0, buff)
        #             break
        #         # TODO
        #         else:
        #             pass
        #print "end send"
        #if not sock.write_buff:
        #    try:
        #        _writes.remove(sock.sock)
        #    except:
        #        print sock.sock.getpeername(), sock.sock.getsockname()
        #        import pdb; pdb.set_trace() 

class Socket(object):

    def __init__(self, sock, readable, writable, accept, on_data, connecting, on_close):
        self.sock = sock
        self.readable = readable
        self.writable = writable
        self.accept = accept

        self.read_buff = []
        self.write_buff = []
        self.connecting = connecting

        self.on_data = on_data
        self.on_close = on_close

        if self.accept:
            self.name = 'listen(%s:%d)' % self.sock.getsockname()
        else:
            from_ = "%s:%d" % self.sock.getsockname() 
            to = "%s:%d" % self.sock.getpeername() 
            self.name = 'connection(%s > %s)' % (from_, to)

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name

    def send(self, buff):
        if not self.write_buff:
            _writes.add(self.sock)
        self.write_buff.append(buff)

    def close(self):
        # TODO 关闭 半关闭
        if self.write_buff or self.connecting:
            print "remove 1", self.sock.getpeername(), self.sock.getsockname()
            _writes.remove(self.sock)
        if self.readable or self.accept:
            _reads.remove(self.sock)
        self.sock.close()

    def beenclosed(self):
        # TODO 关闭 半关闭
        if self.write_buff or self.connecting:
            print "remove 2", self.sock.getpeername(), self.sock.getsockname()
            _writes.remove(self.sock)
        if self.readable or self.accept:
            _reads.remove(self.sock)
        self.sock.close()

_socks = {}

# _poll = select.poll()

_reads = set()
_writes = set()
_errors = set()

def _add_sock(sock, readable=False, writable=False, accept=False, on_data=None, connecting=False, on_close=None):
    s = Socket(sock, readable, writable, accept, on_data, connecting, on_close)
    _socks[sock.fileno()] = s
    if readable or accept:
        _reads.add(sock)
    if connecting:
        _writes.add(sock)
    return s

if __name__ == "__main__":
    # import time

    host, port = "127.0.0.1", 10471
    def on_data(s):
        print s, s.read_buff, "recv"

    def on_close(s):
        print s, s.read_buff, "close"

    sock = listen(host, port, on_data, on_close)

    def on_c_data(s):
        print s, s.recv_buff, "on_c_data"

    def on_c_close(s):
        print s, s.recv_buff, "on_c_close"

    connection = connect(host, port, on_c_data, on_c_close)
    d = "hello" * 2
    connection.send(d)
    connection.send(d)

    while True:
        poll()

        import random
        if random.random() < 0.3:
            pass
            #connection.send(d)
            connection.close()
