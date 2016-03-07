


import cProfile

prof = cProfile.Profile()

def begin():
    prof.enable()
    pass

def end():
    prof.disable()
    prof.create_stats()

    prof.print_stats(-1)
    print 
    prof.print_stats(0)
    print 
    prof.print_stats(1)
    print 
    prof.print_stats(2)

def endl():
    prof.disable()
    prof.create_stats()
    prof.print_stats(1)

def install():
    begin()

import atexit
atexit.register(endl)

if __name__ == "__main__":
    import time
    def a(): b()
    def b(): c()
    def c(): 
        t = time.time()
        while time.time() < t + 1:
            pass

    # begin()
    # a()
    # end()

    install()
    a()

