
def info(msg, *args):
    if args:
        print msg % args
    else:
        print msg

warnning = info
debug = info
error = info

