
import log
import subprocess

_processes = {}

def start_process(cmd, **kw):
    popen = subprocess.Popen(cmd.split(" "), **kw)
    pid = popen.pid
    log.info("start process %d %s ", pid, cmd)
    _processes[pid] = popen
    return pid

def kill_process(pid):
    if pid not in _processes:
        log.error("kill process pid not found %d", pid)
        return 0
    log.info("kill process pid %d", pid)
    popen = _processes[pid]
    popen.kill()
    return 1

def poll():
    for pid, popen in _processes.items():
        retstatus = _processes[pid].poll()
        if retstatus is not None:
            log.info("process mgr poll process %d terminated %d", pid, retstatus)
            del _processes[pid]

if __name__ == "__main__":

    pid = start_process("ls -l")
    kill_process(pid)

    pid = start_process("python")
    kill_process(pid)

    pid = start_process("cd", shell=True)
    kill_process(pid)

    pid = start_process("dir", shell=True)
    kill_process(pid)

    pid = start_process("sleep 5")
    poll()
    import time
    time.sleep(3)
    kill_process(pid)

    time.sleep(3)
    poll()

