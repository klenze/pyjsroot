import online_base
from numpy import isnan, nan
from functools import partial
import numpy as np
import math
import itertools

class online_tdcsync(online_base.online_base):
    def __init__(self, name, d, channels):
        super().__init__(name)
        self.n=2*len(chanlist)
        self.mkCanvas("%s"%name, self.n)
        self.wrts={n:d["TIMESTAMP_%s_WR"%n] for n in channels}

        self.corr=[]


        h=self.mkHist("WRTS corr",
                      x=(lambda ts=ts: ts-refts, -2000, 0, 2000),
                      y=(lambda corr:corr[1], 
                      log="")


        refstr=channels[0]
        refts=wrts[refstr]
        for n,ts in self.wrts.items():
            if n==refstr:
                continue
            h=self.mkHist("WRTS diff %s - %s"%(n, refstr),
                          x=(lambda ts=ts: ts-refts, -2000, 0, 2000),
                          log="")

        for ch in chanlist[1:]:
             h=self.mkHist("coarsy diff %s - %s"%(ch.name, ref.name),
                          x=(partial(lambda ch: math.fmod(ch.get()-ref.get()+3*period/2, period), ch), period, 0, period), 
                          log="y")
        self.finalize()
    def onEvent(self):
        self.corr.clear()
        valid=list(filter lambda ts: not isnan(ts), self.wrts)
        self.corr.append(itertools.product(valid, valid))



