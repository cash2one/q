# encoding: utf8

import uuid

class Shell(object):

    def __init__(self):
        self.envs = {}

    def apply(self):
        uid = str(uuid.uuid4())
        self.envs[uid] = {}
        return uid

    def exc(self, uuid, code):
        exec(code, globals(), self.envs[uuid])

    def eva(self, uuid, code):
        return eval(code, globals(), self.envs[uuid])

def begin(host, port):
    s = Shell()
    uid = s.apply()
    while True:
        code = raw_input(">>> ")
        print code
        s.exc(uid, code)

if __name__ == "__main__" and 0:
    s = Shell()
    i = s.apply()
    s.exc(i, """
a = 1
""")
    print s.eva(i, "a")
    print s.envs

if __name__ == "__main__" and 1:
    begin(1, 1)
