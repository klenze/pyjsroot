import online_base
from numpy import isnan, nan
import numpy as np



class online_tof(online_base.online_base):
    def __init__(self, name, d):
        super().__init__(name)
        # raw dictionaries, containing a list of tdc_hits for every channel
        self.losdict=d["LOS1VT"]
        self.tofdicts={i:d["TOF%dVT"%i] for i in range(1,4)}
        # 
       # :
        self.npaddles=3 # 0: lower, 1: middle, 2:upper
        self.nplanes=2  # 0: front, 1: back
        self.nends=2    # 0: right, 1: left
        self.nsipm=4
        self.times=np.ones((self.npaddles, self.nplanes, self.nends, self.nsipm), dtype=float)
        self.times*=nan # make all invalid
        self.avgtimes=np.ones((self.npaddles, self.nplanes, self.nends), dtype=float)
        self.avgtimes*=nan # make all invalid
        self.lostimes=np.ones((8,), dtype=float)
        self.lostimes*=nan
        self.hitindices=[]

        self.mkCanvas("%s overview"%name, 12)
        ncorr=16+16*len(self.tofdicts)+1
        # pad 1: correlations
        h=self.mkHist("hits",
                      x=(lambda i:i, ncorr, 0.5, ncorr+0.5),
                      filllist=self.hitindices)
        h=self.mkHist("correlations",
                      x=(None, ncorr, 0.5, ncorr+0.5), # x[0]==None means no automatic filling
                      y=(None, ncorr, 0.5, ncorr+0.5))
        self.correlations=h.hist
        self.next_pad()
        for i in range(3):
            h=self.mkHist("avg P1-P2, paddle %d"%(i+1),
                    x=(lambda i=i: sum([pow(-1, iplane)*self.times[i][iplane][iside][ichan]
                                     for iplane in range(2) for iside in range(2) for ichan in range(4)])/4.
                        ,1000, -5., 5.))
 
        for i in range(3):
            h=self.mkHist("x-pos P1 vs P2, paddle %d"%(i+1),
                    x=(lambda i=i: sum([pow(-1, iside)*self.times[i][iplane][iside][ichan]
                                     for iplane in [0] for iside in range(2) for ichan in range(4)])/4.
                        ,100, -5., 5.),
                    y=(lambda i=i: sum([pow(-1, iside)*self.times[i][iplane][iside][ichan]
                                     for iplane in [1] for iside in range(2) for ichan in range(4)])/4.
                        ,100, -5., 5.))
        for i in range(3):
            h=self.mkHist("avg P*- avg LOS, paddle %d"%(i+1),
                    x=(lambda i=i: sum([self.times[i][iplane][iside][ichan]
                                     for iplane in range(2) for iside in range(2) for ichan in range(4)])/16.
                                   - sum(self.lostimes)/8.
                        ,10000, -1000., 1000))
 
        self.procs.append(lambda: self.onEvent())
        self.finalize()

    def onEvent(self):
       self.times*=nan # make all invalid
       self.avgtimes*=0.0 # set it to zero
       self.lostimes*=nan
       self.hitindices.clear()
       for ch,hitlist in self.losdict.items():
           self.hitindices.append(ch)
           self.lostimes[ch-1]=hitlist[0].getTime()

       for vftxno, tofdict in self.tofdicts.items():
           for ch, hitlist in tofdict.items():
               self.hitindices.append(16*vftxno+ch)
               ch-=1 # make channel run from zero
               t=hitlist[0].getTime()
               self.times[vftxno-1][ch//8][(ch%8)//4][ch%4]=t

       for vftxnofrom0 in range(3):
           for ch in range(16): # ch runs from zero here
               self.avgtimes[vftxnofrom0][ch//8][(ch%8)//4]+=self.times[vftxno-1][ch//8][(ch%8)//4][ch%4]/4.

       
       for i in self.hitindices:
           for j in self.hitindices:
               if j<=i:
                   self.correlations.Fill(i, j)

