# encoding: utf8

"""
Code objects 

Code objects represent byte-compiled executable Python code, or bytecode. 
The difference between a code object and a function object is that the function object contains an explicit reference to the function’s globals (the module in which it was defined), 
while a code object contains no context; 
also the default argument values are stored in the function object, not in the code object (because they represent values calculated at run-time). 
Unlike function objects, code objects are immutable and contain no references (directly or indirectly) to mutable objects.

Special read-only attributes: 
    co_name gives the function name; 
    co_argcount is the number of positional arguments (including arguments with default values); 
    co_nlocals is the number of local variables used by the function (including arguments); 
    co_varnames is a tuple containing the names of the local variables (starting with the argument names); 
    co_cellvars is a tuple containing the names of local variables that are referenced by nested functions; 
    co_freevars is a tuple containing the names of free variables; 
    co_code is a string representing the sequence of bytecode instructions; 
    co_consts is a tuple containing the literals used by the bytecode; 
    co_names is a tuple containing the names used by the bytecode; 
    co_filename is the filename from which the code was compiled; 
    co_firstlineno is the first line number of the function; 
    co_lnotab is a string encoding the mapping from bytecode offsets to line numbers (for details see the source code of the interpreter); 
    co_stacksize is the required stack size (including local variables); co_flags is an integer encoding a number of flags for the interpreter.

The following flag bits are defined for co_flags: 
    bit 0x04 is set if the function uses the *arguments syntax to accept an arbitrary number of positional arguments; 
    bit 0x08 is set if the function uses the **keywords syntax to accept arbitrary keyword arguments; 
    bit 0x20 is set if the function is a generator.

Future feature declarations (from __future__ import division) also use bits in co_flags to indicate whether a code object was compiled with a particular feature enabled: 
    bit 0x2000 is set if the function was compiled with future division enabled; 
    bits 0x10 and 0x1000 were used in earlier versions of Python.

Other bits in co_flags are reserved for internal use.

If a code object represents a function, the first item in co_consts is the documentation string of the function, or None if undefined.
"""

def function(): 
    pass
code_obj = function.func_code
code_attrs = dir(code_obj)
del code_obj
del function

code_equal_ignore_atts = set(["co_filename", "co_firstlineno", "co_name"])

def code_equal(one, another):
    eq = True
    for attr in code_attrs:
        if attr.startswith("__") and attr != "__doc__":
            continue 
        if attr in code_equal_ignore_atts:
            continue
        if attr == "co_code":
            print attr, repr(getattr(one, attr)), repr(getattr(another, attr)) , getattr(one, attr) == getattr(another, attr)
        else:
            print attr, getattr(one, attr), getattr(another, attr) , getattr(one, attr) == getattr(another, attr)
        eq = eq and getattr(one, attr) == getattr(another, attr)
    print eq
    print 
    print
    return eq

def f1():
    pass

def f2():
    pass

def f22(a, b):
    pass

def f3():
    return 1 + 1

def f4():
    return 2

def f5():
    for x in range(10):
        print 2

def f51():
    for y in range(10):
        print 2

def f6():
    for x in range(10):
        print 3

def f7():
    pass
    pass
    pass

def eq(f1, f2):
    print f1, f2
    return code_equal(f1.func_code, f2.func_code)

eq(f1, f2)
eq(f2, f22)
eq(f1, f7)
eq(f2, f3)
eq(f3, f4)
eq(f5, f51)


gd = {}
ld = {}
code = """
a = 1
"""
exec code in gd, ld
print "gd", gd
print "ld", ld


def sub(key, cb):
    pass

def f():
    print 1

sub("xxx", f)

def f():
    print 2

#reload

#pub() print 2


def f():
    def h():
        print 1
    return h

a = f()
a = f()

#reload

def f():
    def h():
        print 2
    return h

b = f()

