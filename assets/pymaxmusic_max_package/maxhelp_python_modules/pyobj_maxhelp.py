#
# pyobj_maxhelp.py
# by Daniel Brown - daniel@intelligentmusicsystems.com
#
# An example of using the pymax system.
# Use with the Max patch "pyobj_maxhelp.maxpat"


class MyObject():
    def __init__(self):
        self.a = 2
        self.b = "hello"

    def add_a(self, value):
        return self.a + value

#------------------------------------------------------------------------

if __name__ == "__main__":

    from pymaxmusic import pymax
    
    pymax.open_pymax()
    pymax.add_class("myobject", MyObject)
    pymax.run_pymax()