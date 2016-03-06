
import log
import subprocess

class ProcessManager(object):

    def __init__(self):
        self.processes = {}

    def start_process(self, cmd, **kw):
        log.info("start process %s", cmd)
        popen = subprocess.Popen(cmd.split(" "), **kw)
        pid = popen.pid
        self.processes[pid] = popen
        return pid

    def kill_process(self, pid):
        if pid not in self.processes:
            log.error("kill process pid not found %d", pid)
            return 0
        log.info("kill process pid %d", pid)
        popen = self.processes[pid]
        popen.kill()
        return 1

if __name__ == "__main__":

    mgr = ProcessManager()
    pid = mgr.start_process("ls -l")
    mgr.kill_process(pid)

    pid = mgr.start_process("python")
    mgr.kill_process(pid)

    pid = mgr.start_process("cd", shell=True)
    mgr.kill_process(pid)

    pid = mgr.start_process("dir", shell=True)
    mgr.kill_process(pid)

    pid = mgr.start_process("sleep 5")
    import time
    time.sleep(3)
    mgr.kill_process(pid)

