import online_base
from numpy import isnan, nan
from functools import partial
from math import pi, sin, cos
import numpy as np
from numpy.linalg import lstsq # linear
from numpy.linalg import norm

from scipy.optimize import least_squares # non-linear

__tern__=lambda p, then, otherwise: [otherwise, then][bool(p)]

class online_los(online_base.online_base):
    def __init__(self, name, vftxdict, tamexdict, offset):
        super().__init__(name)
        self.vftxdict=vftxdict # a dict of all the los hits, e.g. {1: [tdchit(), tdchit, tdchit]}
        self.tamexdict=tamexdict # same as above
        self.offset=offset
        self.idxrange=list(range(offset+1, offset+8))

        # calibration parameters, to be overwritten by user as desired
        self.vftxoffsets=np.array([nan]+[0 for i in range(1, 9)])
        self.tot_scale=np.array([nan]+[1 for i in range(1,9)])
        # 
        self.newana=False
        # stuff which is useful in multiple places and will be set by onEvent:
        self.tamexhits=[] # a list of tuples (idx, tdchit), (idx, tdchit)
        self.vftxhits=[]  # as above
        self.vtimes=np.array([0]+[nan for i in range(1, 9)]) # zeroth entry is dummy value
        self.ttimes=np.array([0]+[nan for i in range(1, 9)]) # zeroth entry is dummy value
        self.tots= np.array([0]+[nan for i in range(1, 9)]) # zeroth entry is dummy value
        
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
        h=self.mkHist("VFTX multiplicities",
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
                      y=(lambda n, h:h.tot, 500,   0,  500),
                      x=(lambda n, h: n,       8, 0.5,   8.5),
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
                      x=(avgTot, 200, 0, 500))
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
        self.mkCanvas("%s lospos toys"%name, 3, 3)
        h=self.mkHist("PMT positions",
                      x=(None, 5, -1.2, 1.2),
                      y=(None, 5, -1.2, 1.2),
                      xtitle="<-Mes-- (-x, a.u.) --Wix->",
                      ytitle="<-Down-- (+y, a.u.) --Up-->")
        self.pmposhist=h

        # pad7
        h=self.mkHist("lospos1",
                x=(lambda: self.lospos1[0], 200, -2, 2),
                y=(lambda: self.lospos1[1], 200, -2, 2))
        # pad7
        h=self.mkHist("lospos2",
                x=(lambda: self.lospos2[0], 200, -2, 2),
                y=(lambda: self.lospos2[1], 200, -2, 2))

        # pad 8: lospos x
        h=self.mkHist("losposX",
                x=(lambda: self.lospos1[0], 200, -0.5, 0.5),
                y=(lambda: self.lospos2[0], 200, -0.5, 0.5))

        h=self.mkHist("speed",
                x=(lambda: self.c, 200, 0, 4),
                y=(lambda: self.timedev, 200, 0, 1))



 
        #################################################
        self.mkCanvas("%s vftx cal"%name, 3, 3)

        for i in range(1, 9):
             h=self.mkHist("vftx_diff_%d"%i,
                           x=(partial(lambda i: self.vtimes[i]+0*self.vftxoffsets[i], i), 2000, -8, 8))

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
                              x=(partial(lambda i: self.tdiffs[i], i), 400, -4, 4),
                              y=(partial(lambda i: self.tdiffs[i], j), 400, -4, 4),
                              )

        self.set_pmpos()
        self.procs.append(lambda: self.onEvent())
        self.finalize()

    def set_pmpos(self, phase=3*pi/8, dir=-1):
        #r=47.5 #mm
        v=0.47 #
        #v=10/0.4
        r=1/v
        #r=
        #sign=np.sign
        # third element will be useful later
        self.pos=np.array([[r*cos(pi*i*dir/4+phase), r*sin(pi*i*dir/4+phase), 0] for i in range(-1, 8)])
        self.pos[0]=np.array([0, 0, 0]) # dummy values to simulate indices starting from 1
        for i,p in enumerate(self.pos[1:], 1):
            self.pmposhist.hist.Fill(p[0]/r, p[1]/r, i)
        self.weights=-self.pos.dot(np.array([[1, 0, 0], [0, 1, 0]]).T).T
        self.flatweights=np.sign(self.weights)
        if False:
           print("pos:")
           print(self.pos)
           print(self.flatweights)


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
                #print(hits[0].totc, hits[0].tot)
                self.tots[keff]=hits[0].tot/self.tot_scale[keff]
                self.ttimes[keff]=hits[0].getTime()
       self.avgvtime=sum(self.vtimes)/8
       self.vtimes[1:]-=self.avgvtime
       for i in range(1,5):
           self.tdiffs[i]=self.vtimes[i]-self.vtimes[i+4]
       self.lospos1=self.flatweights.dot(self.vtimes/8.)
       self.lospos2=self.weights.dot(self.vtimes/8.)
       self.lospos3=np.array([nan, nan])
       self.lospos4=np.array([nan, nan])
       self.cost=np.array(5*[nan])
       self.c=nan
       self.timedev=nan
       if isnan(self.avgvtime) or not self.newana:
           return
       # better pos from vftx, use linear least squares
       if True:
           timecol=np.array([[0],[0],[1]]).T
           var_ti=self.vtimes.dot(self.vtimes.T)
           M= + 2*(self.vtimes)[1:,np.newaxis].dot(timecol)   - 2*self.pos[1:]
           b=     (self.vtimes[1:])**2 -    var_ti 
           res=lstsq(M, b, rcond=None)
           self.lospos3=res[0][0:2]
       if False: 
           print("\n\nM ~~~~~~~~~")
           print(M)
           print("*\nx ~~~~~~~~~")
           print(res[0])
           print("-\nb ~~~~~~~~~")
           print(b)
           print("=\n")
           print(M.dot(res[0])-b)
           print(self.lospos2)
       def loss(x, t, pmtno):
          c=1
          return c*(t-self.vtimes[pmtno])-norm(x[:2]-self.pos[pmtno,:2])

       def totloss(x, pos):
          t=x[0]
          #c=1
          return np.array([loss(x=pos, t=t, pmtno=i) for i in range(1, 9)])
      #print(res.x, pow(var_ti, 0.5), res.cost)
       #self.c=res.x[1]
       self.timedev=pow(var_ti, 0.5)

       def totloss1(x):
           t=x[0]
           pos=x[1:3]
           return np.array([loss(x=pos, t=t, pmtno=i) for i in range(1, 9)])

       res=least_squares(totloss1, [0, 0, 0])
       self.lospos4=res.x
       for i in range(1, 5):
             res=least_squares(totloss, [0], x=getattr(self, "lospos%d"%i))
             self.cost[i]=res.cost
       print(cost)
