# encoding: utf8

"""

异步非阻塞TCP

接口

    sock = tcp.listen(host, port, on_data=None, on_close=None, backlog=1024)
    sock.close()

    ---

    sock = tcp.connect(host, port, on_data, on_close, on_connected)
    sock.send(buff)
    sock.close()

    ---

    def on_data(sock):
        print sock, sock.recv_buff

    def on_close(sock):
        print sock, sock.recv_buff

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
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host, port))

    k = 1024
    m = 1024 * k * 10
    print "*** 1", sock.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, m)
    print "*** 2", sock.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)

    print "*** 11", sock.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, m)
    print "*** 21", sock.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF)

    sock.listen(backlog)
    return _add_sock(sock, accept=True, on_data=on_data, on_close=on_close)

def connect(host, port, on_data, on_close):
    log.info("begin tcp connection to %s %s", host, port)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    k = 1024
    m = 1024 * k * 10
    print "*** 1", sock.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, m)
    print "*** 2", sock.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)

    print "*** 11", sock.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, m)
    print "*** 21", sock.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF)


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

    try:
        events = epoll.poll()
    except IOError as exception:
        print "epoll", exception
        return 

    for fileno, event in events:
        sock = _socks[fileno]
        if event & select.EPOLLIN:
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
                print "*** 3", connection.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)
                print "*** 4", connection.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF)
                log.info("new tcp connection %s", _s)

        elif event & select.EPOLLOUT:
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
                sock.unreg_write()

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

        if readable or accept:
            flag = select.EPOLLIN
        if connecting or writable:
            flag = flag | select.EPOLLOUT
        self.flag = flag
        epoll.register(sock.fileno(), self.flag)

    def unreg_write(self):
        epoll.modify(self.sock.fileno(), select.EPOLLIN)

    def reg_write(self):
        epoll.modify(self.sock.fileno(), select.EPOLLIN | select.EPOLLOUT)

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name

    def send(self, buff):
        if not self.write_buff:
            self.reg_write()
        self.write_buff.append(buff)

    def close(self):
        # TODO 关闭 半关闭
        epoll.unregister(self.sock.fileno())
        self.sock.close()

    def beenclosed(self):
        # TODO 关闭 半关闭
        epoll.unregister(self.sock.fileno())
        self.sock.close()

_socks = {}
epoll = select.epoll()

def _add_sock(sock, readable=False, writable=False, accept=False, on_data=None, connecting=False, on_close=None):
    s = Socket(sock, readable, writable, accept, on_data, connecting, on_close)
    _socks[sock.fileno()] = s
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
