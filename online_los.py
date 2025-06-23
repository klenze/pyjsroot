import online_base
from numpy import isnan, nan
from functools import partial
from math import pi, sin, cos

__tern__=lambda p, then, otherwise: [otherwise, then][bool(p)]

class online_los(online_base.online_base):
    def __init__(self, name, vftxdict, tamexdict, offset):
        super().__init__(name)
        self.vftxdict=vftxdict # a dict of all the los hits, e.g. {1: [tdchit(), tdchit, tdchit]}
        self.tamexdict=tamexdict # same as above
        self.offset=offset
        self.idxrange=list(range(offset+1, offset+8))

        # calibration parameters, to be overwritten by user as desired
        self.vftxoffsets=[nan]+[0 for i in range(1, 9)]
        self.tot_scale=[nan]+[1 for i in range(1,9)]


        # stuff which is useful in multiple places and will be set by onEvent:
        self.tamexhits=[] # a list of tuples (idx, tdchit), (idx, tdchit)
        self.vftxhits=[]  # as above
        self.vtimes=[0]+[nan for i in range(1, 9)] # zeroth entry is dummy value
        self.ttimes=[0]+[nan for i in range(1, 9)] # zeroth entry is dummy value
        self.tots= [0]+[nan for i in range(1, 9)] # zeroth entry is dummy value
        
        self.tdiffs=[nan for i in range(5)]

        self.mkCanvas("%s overview"%name, 3, 3)
        # pad 1: hits per channel
        h=self.mkHist("VTFX hits",
                      x=(lambda n,h: n, 8, 0.5, 8.5),
                      filllist=self.vftxhits)
        h.hist.SetLineColor(2)
        h.hist.SetTitle("hits per channel")
        self.reuse_pad()
        h=self.mkHist("Tamex hits",
                      x=(lambda n,h: n, 8, 0.5, 8.5),
                      filllist=self.tamexhits)

        # pad 2: multiplicities
        h=self.mkHist("VFTX multiplicites",
                      x=(lambda n,lst: self.sanitize_range(n), 16, 0.5, 16.5),
                      y=(lambda n,lst: len(lst), 10, 0, 10),
                      filllist=self.vftxdict)
        self.reuse_pad()
        h.hist.SetTitle("Tamex/VFTX multiplicities")
        h=self.mkHist("Tamex multiplicites",
                      x=(lambda n,lst: self.sanitize_range(n)+8, 16, 0.5, 16.5),
                      y=(lambda n,lst: len(lst), 10, 0, 10),
                      filllist=self.tamexdict)
        # pad 3: tot per channel
        h=self.mkHist("ToTs",
                      y=(lambda n, h:h.tot, 200,   0,  1000),
                      x=(lambda n, h: n,      8, 0.5,   8.5),
                      filllist=self.tamexhits,
                      )
        # pad 4: avg tot -- for people with lambda allergies
        def avgTot():
           avg=0
           for k in self.idxrange:
               if (h:=self.tamexdict.get(k))!=None:
                  avg+=h[0].tot/8
               else:
                   return nan
           return avg
        h=self.mkHist("avgToT",
                      x=(avgTot, 200, 0, 1000))
        # pad 5: odd vs even PMTs -- lambda version
        #h=self.mkHist("oddEvenDiff",
        #    x=(lambda: sum(map(lambda k: pow(-1, k)*__tern__((h:=self.vftxdict.get(k)), k.getTime(), nan)))),
        #       500, -20, 20))
        # okay, let us try again
        h=self.mkHist("oddEvenDiff",
                      x=(lambda: sum(map(lambda n: pow(-1, n)*self.vtimes[n], range(1,9))),
                         2000, -20, 20))
        # pad 6
        h=self.mkHist("walk",
                      x=(lambda n: self.ttimes[n]-self.avgvtime, 50, -4, 4),
                      y=(lambda n: self.tots[n], 100, 0, 500),
                      filllist=list(range(1,9)))


        #################################################
        self.mkCanvas("%s vftx cal"%name, 3, 3)

        for i in range(1, 9):
             h=self.mkHist("vftx_diff_%d"%i,
                           x=(partial(lambda i: self.vtimes[i]+self.avgvtime+self.vftxoffsets[i], i), 2000, -4, 4))

        #################################################
        self.mkCanvas("%s tamex cal"%name, 3, 3)

        for i in range(1, 9):
             h=self.mkHist("tamex_tot_%d"%i,
                           x=(partial(lambda i: self.tots[i], i), 500, 0, 1000))

          #################################################
        self.mkCanvas("%s time diff corr"%name, 3, 3)

        for i in range(1, 5):
            for j in range(i+1, 5):
                h=self.mkHist("time_diff_%d-%d_vs_%d-%d"%(i, i+4, j, j+4),
                              x=(partial(lambda i: self.tdiffs[i], i), 200, -2, 2),
                              y=(partial(lambda i: self.tdiffs[i], j), 200, -2, 2),
                              )

        self.procs.append(lambda: self.onEvent())
        self.finalize()

    def set_pmpos(phase, dir=1):
        self.pos=[(nan, nan)] # dummy entry for index zero
        for i in range(1, 9):
            x=phase+dir*i/8*(2*pi)
            self.pos.append((cos(x), sin(x)))

    def sanitize_range(self, n):
        """
        Check if n is within our range (as defined by the offset)
        and return it without the offset, otherwise return nan.
        """
        if self.offset<n and n<=self.offset+8:
          return n-self.offset
        return float("nan")

    def onEvent(self):
       for i in range(1,9):
            self.vtimes[i]=nan
            self.ttimes[i]=nan
            self.tots[i]=nan
       self.vftxhits.clear()
       self.tamexhits.clear()
       for k, hits in self.vftxdict.items():
            if not isnan(keff:=self.sanitize_range(k)):
                for h in hits:
                    self.vftxhits.append((keff, h))
                self.vtimes[keff]=hits[0].getTime()-self.vftxoffsets[keff]
       for k, hits in self.tamexdict.items():
            if not isnan(keff:=self.sanitize_range(k)):
                for h in hits:
                    self.tamexhits.append((keff, h))
                self.tots[keff]=hits[0].tot/self.tot_scale[keff]
                self.ttimes[keff]=hits[0].getTime()
       self.avgvtime=sum(self.vtimes)/8
       for i in range(1,5):
           self.tdiffs[i]=self.vtimes[i]-self.vtimes[i+4]

