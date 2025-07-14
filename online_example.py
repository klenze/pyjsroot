import online_base
from numpy import isnan, nan, array

class online_example(online_base.online_base):
    def __init__(self, name, vftxdict):
        super().__init__(name) # pass our name on to online_base
        self.vftxdict=vftxdict # our data from pyh101, passed by online.py
        self.debug=False

        # create our private np array to hold the first hit in each VFTX channel of LOS
        self.vtimes=array([nan for i in range(9)]) # zeroth entry is dummy value

        self.mkCanvas("%s vftx cal"%name, 3, 3)
        # we could also use self.mkCanvas("foo", 9) to get a 3x3 split automatically

        for i in range(1, 9):
           # because we do not pass any cv argument to mkHist, we will draw on 
           # the next unused canvas histogram names will be prefixed with our
           # name, so we do not need to work too hard to keep them unique
           # 
           # See lambda.md for how lambdas work and why we need i=i

           h=self.mkHist("vftx_diff_%d"%i,
                         x=(lambda i=i: self.vtimes[i], 2000, -8, 8),
                         xtitle="time relative to average")
        # for a two-d histogram, we would specify a y= in the same way as x
 
        # if you are uncomfortable using lambda expressions, you can also use
        # None and fill the histograms yourself later:
        h=self.mkHist("time variance",
                      x=(None, 2000, -8, 8))
        # h.hist is root THxI object, store it as a reference to fill it below:
        self.varhist=h.hist
 
        # always run our onEvent method before filling the lambda histograms:
        self.procs.append(lambda: self.onEvent())
        # draw everything on the canvases etc:
        self.finalize()
  
    def onEvent(self):
       self.vtimes*=nan # invalidate all vtimes entries
       for k, hits in self.vftxdict.items():
             # any list of hits will have at least one entry
             self.vtimes[k]=hits[0].getTime()
       self.avgvtime=sum(self.vtimes[1:])/8
       if self.debug:
           print(self.name, ": self.vtimes ==", self.vtimes)
       # the above will be nan if we do not have a hit for every PMT. 
       self.vtimes-=self.avgvtime # subtract average times
       # you are responsible for filling histograms without lambda expressions:
       self.varhist.Fill(self.vtimes[1:].dot(self.vtimes[1:])/(8-1))

