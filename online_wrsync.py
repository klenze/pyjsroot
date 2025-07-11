import online_base
from numpy import isnan, nan
from functools import partial
import numpy as np
from numpy import log10
import math
import itertools
from copy import copy
class fifo2:
    def __init__(self, n):
        self.curr=[nan for i in range(n)]
        self.prev=[nan for i in range(n)]

        self.changed=[False for i in range(n)]
        self.count=[0 for i in range(n)]
        self.totcount=[0 for i in range(n)]
    def unset(self, tslist):
        for i in range(len(self.changed)):
            self.changed[i]=False
            if not isnan(tslist[i]):
                self.count[i]+=1
                self.totcount[i]+=1
    def update(self, tslist):
        for i, ts in enumerate(tslist):
            if not isnan(ts):
                self.prev[i]=self.curr[i]
                self.curr[i]=copy(ts)
                self.changed[i]=True
                self.count[i]=0
                self.totcount[i]+=1
            else:
                self.changed[i]=False


# TODO: this class requires cleanup because it currently deals with handling broken
# timestamps from a detector system. 

class online_wrsync(online_base.online_base):
    def __init__(self, name, d, channels):
        super().__init__(name)
        self.n=len(channels)
        self.mkCanvas("%s"%name, 3*self.n+1)
        self.channels=channels
        self.wrts=[d["TIMESTAMP_%s"%self.channels[i]] for i in range(self.n)]
        self.trig=d["TRIGGER"]
        self.valid=[]
        self.corr=[]
        self.notimestamps=[nan for i in range(self.n)]
        self.tsmem=fifo2(self.n)
        self.tsmem3=fifo2(self.n)

        h=self.mkHist("WRTS corr",
                      x=(lambda corr:corr[0], self.n, -0.5, self.n-0.5),
                      y=(lambda corr:corr[1], self.n, -0.5, self.n-0.5),
                      xlabels=self.channels,
                      ylabels=self.channels,
                      log="z",
                      filllist=self.corr)
        ref=0
        refts=self.wrts[ref]
        for i,ts in enumerate(self.wrts[1:], start=1):
            h=self.mkHist("WRTS diff %s - %s"%(self.channels[i],self.channels[ref]),
                          x=(lambda i=i: self.symlog(self.tsmem.curr[i]-self.tsmem.curr[ref]), 2000, -10, 10),
                          xtitle="sign(\Delta t) log_{10}(abs(\Delta t/ns))",
                          log="y")
            h.cond=lambda i=i: self.tsmem.changed[i] or self.tsmem.changed[ref]
        for i,ts in enumerate(self.wrts):
            h=self.mkHist("WRTS skip %s"%(self.channels[i]),
                          x=(lambda i=i: log10(self.tsmem.curr[i]-self.tsmem.prev[i]), 2000, 0, 10),
                          xtitle="log_{10}(\Delta t/ns)",
                          log="y")
            h.cond=lambda i=i: self.tsmem.changed[i]

        for i,ts in enumerate(self.wrts):
            h=self.mkHist("T3 WRTS skip %s"%(self.channels[i]),
                    #x=(lambda i=i: (self.tsmem3.curr[i]-self.tsmem3.prev[i])/1e9, 2000, 0, 1),
                    x=(lambda i=i: log10(self.tsmem3.curr[i]-self.tsmem3.prev[i]), 2000, 0, 10),
                    #xtitle="\Delta t in s"
                    xtitle="log_{10}(\Delta t/ns)",
                    log="y",
                      )
            h.cond=lambda i=i: self.tsmem3.changed[i]
        self.offset=255
        i=2
        h=self.mkHist("T3+%d WRTS skip %s"%(self.offset, self.channels[i]),
                    x=(lambda i=i: log10(self.tmp[0]-self.tmp[1]), 2000, 0, 10),
                    xtitle="log_{10}(\Delta t/ns)",
                    log="y",
                      )
        h.cond=lambda: self.tmpchanged
        self.tmp=[nan, nan]
        self.procs.append(lambda:self.onEvent())
        self.realt3=[]
        self.lastt3=[nan for i in range(20)]
        self.trigfifo=[0 for i in range(300)]
        self.finalize()

    def onEvent(self):
       self.valid.clear()
       self.valid+=[i for i in range(self.n) if not isnan(self.wrts[i])]
       self.corr.clear()
       self.corr+=map(list, itertools.product(self.valid, self.valid))
       self.tsmem.update(self.wrts)
       if self.trig==3:
          if not isnan(self.wrts[0]):
              #print("Bus:   %5d          "%(self.tsmem3.count[0])) #, self.tsmem3.count[2], np.array(self.realt3)-(self.tsmem.totcount[2])+self.offset))
              diffs=(-np.array(self.lastt3)+self.tsmem.totcount[2])
              if (not 254 in diffs and diffs[-1]>254):
                  print(diffs)
              #for i, t in enumerate(self.trigfifo):
              #    if t==3:
              #        print("%d "%i, end="")
              #print("")
              if self.trigfifo[254]!=3:
                  print("T3 event without offset 254!")
              #else:
                  #print(self.tsmem.curr[2]-self.tsmem.curr[0])
          if not isnan(self.wrts[2]):
              #print("Music:           %5d"%self.tsmem3.count[2])
              self.realt3.append(self.tsmem.totcount[2]+self.offset)
              self.lastt3=[copy(self.tsmem.totcount[2])]+self.lastt3[:-1]


          for i in []: #["curr", "prev", "changed"]:
              print(i, getattr(self.tsmem3, i))
          self.tsmem3.update(self.wrts)
          #print("-----------")
       else:
           self.tsmem3.unset(self.wrts)
       #if self.trig==3 and not isnan(self.wrts[0]):
       #       print("fooo", self.tsmem3.curr[0]-self.tsmem.curr[0], self.tsmem.totcount[0])
       if not isnan(self.wrts[2]):
           self.trigfifo=[copy(self.trig)]+self.trigfifo[:-1]
       #if self.tsmem3.count[2]==self.offset and not isnan(self.wrts[2]):
       if len(self.realt3)>0 and self.tsmem.totcount[2]==self.realt3[0]:
           self.realt3=self.realt3[1:]
           self.tmp=[copy(self.wrts[2])]+self.tmp[:-1]
           #print(self.tmp[0]-self.tmp[1]-1e8)
           #print(self.tmp[0]-self.tsmem3.curr[0], self.tmp[0]-self.tsmem.curr[0], self.tsmem3.count[0], self.tsmem.totcount[0])
           self.tmpchanged=True
       else:
           self.tmpchanged=False

       #if self.tsmem3.changed[0] or self.tmpchanged:
       #    print("d=", self.tmp[0]-self.tsmem3.curr[0], self.tmpchanged)
       #print(self.tsmem.totcount[2], self.realt3)

       if self.tsmem3.changed[0] and not self.tsmem.changed[0]:
           print("Weirdness after updating on %s, trigger=%s"%(self.wrts, self.trig))
       if False: # self.tsmem.changed[0] or self.tsmem.changed[1]:
           print(self.tsmem.curr[1]-self.tsmem.curr[0])
           print(type(self.tsmem.curr[1]))
       #print(self.tsmem.changed)


