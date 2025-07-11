import online_base
from numpy import isnan, nan
from functools import partial
from math import pi, sin, cos
import numpy as np



class online_rolu(online_base.online_base):
    def __init__(self, name, tamexdict):
        super().__init__(name)
        self.tamexdict=tamexdict # same as above
        self.idxrange=list(range(1, 9))

        # calibration parameters, to be overwritten by user as desired
        self.tot_scale=np.array([nan]+[1 for i in range(1,9)])
        # 
        # stuff which is useful in multiple places and will be set by onEvent:
        self.tamexhits=[] # a list of tuples (idx, tdchit), (idx, tdchit)
        self.ttimes=np.array([0]+[nan for i in range(1, 9)]) # zeroth entry is dummy value
        self.tots= np.array([0]+[nan for i in range(1, 9)]) # zeroth entry is dummy value
        

        self.mkCanvas("%s overview"%name, 2, 2)
        # pad 1: hits per channel
        h=self.mkHist("Tamex hits",
                      x=(lambda n,h: n, 4, 0.5, 4.5),
                      filllist=self.tamexhits)

        # pad 2: tot per channel
        h=self.mkHist("ToTs",
                      y=(lambda n, h:h.tot, 200,   0,  1000),
                      x=(lambda n, h: n,      4, 0.5,   4.5),
                      filllist=self.tamexhits,
                      )
        def tristate(low, high):
            if low and high:
                return 2
            return int(high)-int(low)
        R=1
        O=2
        L=3
        U=4
        h=self.mkHist("Counts",
                x=(lambda: tristate(R in self.tamexdict, L in self.tamexdict), 4, -1.5, 2.5),
                y=(lambda: tristate(O in self.tamexdict, U in self.tamexdict), 4, -1.5, 2.5),
                log="z",
#                xtitle="L,none,R,both",
#                ytitle="U,none,O,both"

                xlabels=["L", "\\emptyset", "R", "LR"],
                ylabels=["U", "\\emptyset", "O", "UO"]
                )
        self.procs.append(self.onEvent)
        self.finalize()
 
    def onEvent(self):
       for i in range(1,9):
            self.ttimes[i]=nan
            self.tots[i]=nan
       self.tamexhits.clear()
       for k, hits in self.tamexdict.items():
            if not isnan(keff:=k):
                for h in hits:
                    self.tamexhits.append((keff, h))
                self.tots[keff]=hits[0].tot/self.tot_scale[keff]
                self.ttimes[keff]=hits[0].getTime()
       #print(self.tamexdict, self.tamexhits)


