import online_base
from numpy import isnan, nan
from functools import partial
import numpy as np
import math

class tdcchan:
    def __init__(self, name, arr, idx):
        self.name=name
        self.arr=arr
        self.idx=idx
    def get(self):
        if self.idx in self.arr:
            return self.arr[self.idx][0].getTime()
        return nan

class online_sync(online_base.online_base):
    def __init__(self, name, d, channels):
        super().__init__(name)
        chanlist=[tdcchan("%s[%d]"%(arr, idx), d[arr], idx) for arr,idx in channels]
        self.n=2*len(chanlist)-2
        x=math.floor(pow(self.n, 0.5))
        y=math.ceil(self.n/x)
        self.mkCanvas("%s"%name, x, y)
        ref=chanlist[0]
        periodf=5

        for ch in chanlist[1:]:
             h=self.mkHist("finetime diff %s - %s"%(ch.name, ref.name),
                          x=(partial(lambda ch: math.fmod(ch.get()-ref.get()+3*periodf/2, periodf), ch), periodf*100, 0, periodf),
                          log="y")
        period=5*1024
        for ch in chanlist[1:]:
             h=self.mkHist("coarsy diff %s - %s"%(ch.name, ref.name),
                          x=(partial(lambda ch: math.fmod(ch.get()-ref.get()+3*period/2, period), ch), period, 0, period), 
                          log="y")
        self.finalize()


