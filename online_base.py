import ROOT
from functools import partial
import ctypes

http_inst=None

class empty:
    pass

def __declare_cling__(stuff):
    assert True==ROOT.gInterpreter.Declare(stuff), "Running cling failed for declaration\n %s"%stuff

def __run_cling__(stuff):
    err=ctypes.c_int(0)
    res=ROOT.gROOT.ProcessLineSync(stuff, err)
    assert err.value==0, "Cling failed with err=%d while trying to process %s "%(err.value, stuff)
    return res

__run_cling__("gPad=nullptr;")
__gPad_nullptr__=ROOT.gPad

__run_cling__(
 """
  std::vector<TH1*> hists{};
  /*int addHist(const char* name)
  {
      if (auto* h=gDirectory->Get<TH1>(name))
      {
         hists.push_back(h);
         return 0;
      }
      else
      {
         fprintf(stderr, "%s: failed to add object %s\\n", __PRETTY_FUNCTION__, name);
         return 1;
      }
  };*/
  auto  addHistogram=[&hists](long int raw)
  {
      auto* objPtr=static_cast<TObject*>((void*)raw);
      auto* hPtr=dynamic_cast<TH1*>(objPtr);
      if (!hPtr)
         return 1;
      hists.push_back(hPtr);
      return 0;
  };
  auto clearAllHists=[&hists]()
  {
      int i{};
      for (auto* h: hists)
      {
         h->Reset();
         i++;
      }
      fprintf(stderr, "Cleared %d hists\\n", i);
  };
  """)


__run_cling__("clearAllHists();")

colors=[1,2,3,4,6,7,8,9]


__last_hist__=None
def __default_draw__(histobj, count):
    global __last_hist__
    histobj.cv.cd()
    if count==0:
        __last_hist__=histobj
    if histobj.hist.GetName() not in __last_hist__.codrawn:
        __last_hist__.codrawn[histobj.hist.GetName()]=histobj
    histobj.hist.SetLineColor(colors[count%len(colors)])
    histobj.hist.Draw(histobj.drawopts+["", " same"][count>0])
    ROOT.gPad=__gPad_nullptr__


def __tuplify__(it):
    if callable(it):
        it=it()
    if type(it)==dict:
        it=it.items()
    for obj in it:
         if type(obj)==tuple:
           yield obj
         else:
           yield (obj,)

class online_base:
    def __init__(self, name):
        self.name=name
        self.canvases={} # name -> canvas
        self.hists=[] # list of objects returned by mkHist
        self.current=[None, 0]
        self.procs=[]
        self.nev=0
        self.update_interval=1000

    def finalize(self):
        """
        Draw all objects. Separate so that the user can change stuff.
        To be called by the user.
        """
        draw_counts={}
        for h in self.hists:
            draw_counts.setdefault(h.cv, 0)
            h.draw(h, draw_counts[h.cv]) # call the wrapper draw method
            draw_counts[h.cv]+=1
        if not http_inst:
            print("online_base.http_inst is not set, will not try to register anything with THttpServer")
            return
        for cv in self.canvases.values():
            http_inst.Register("/"+self.name, cv)
        for h in self.hists:
            assert 0==__run_cling__('addHistogram(0x%x);'%ROOT.addressof(h.hist)), "Adding histogram %s to reset list failed"%h.hist.GetName()
        __run_cling__("clearAllHists()")
        #assert 0==ROOT.addHistogram(h.hist), "Adding histogram %s to reset list failed"%h
        http_inst.RegisterCommand("/reset", "clearAllHists()")
        http_inst.SetItemField("/reset", "_fastcmd", "true")
    def process(self):
        for p in self.procs:
            p()
        for h in self.hists:
            h.fill() # call wrapper
        self.nev+=1
        if self.nev%self.update_interval==0:
            for drawnhist in self.hists:
                if not drawnhist.updaterange or len(drawnhist.codrawn)<2:
                    continue
                #print("determining maximum for hist "+h.hist.GetName())
                m=2
                for histobj in drawnhist.codrawn.values():
                    h=histobj.hist
                    m=max(m, h.GetBinContent(h.GetMaximumBin()))
                # it appears that jsroot will update the data even between
                # we set modified, so we need to make halfway sure that the events
                # we will get will fit in the range. 
                # we expect that we will increase counts by a factor of
                # (nev+ui)/nev, plus some safety margin.
                # this is total bullshit. 
                # the alternative would be to have an invisible base histogram
                # whose bin content gets updated to be the max
                drawnhist.hist.SetMaximum(1.2*(1+self.update_interval/self.nev)*m)
            return
            for cv in self.canvases.values():
                i=0
                while True:
                    if not (pad:=cv.GetPad(i)):
                        break
                    pad.Modified()
                    pad.Update()
                    i+=1
                print("Updated %d pads for canvas %s"%(i, cv.GetName()))

    def mkCanvas(self, name, xpos=1, ypos=1):
        assert name not in self.canvases
        cv=ROOT.TCanvas(name, name, 1000, 1000)
        self.canvases[name]=cv
        cv.Divide(xpos, ypos)
        self.current=[cv, 0]
        return cv

    def next_pad(self):
        cv=self.current[0]
        assert cv != None, "Create a canvas before making histograms"
        self.current[1]+=1
        res=cv.GetPad(self.current[1])
        assert res!=None, "Canvas %s has no subpad %d"%(cv.GetName(), self.current[1])
        return res
    def reuse_pad(self):
        self.current[1]-=1

    def mkHist(self, name, 
               x, # x[0] is a callable which returns the quantity you want to plot
                  # x[1:] defines the binning and axis, e.g. xbins, xmin, xmax
               y=None,  # if None, create a 1d hist, otherwise same format as x
               cv=None, # if None, use next unused subcanvas
               drawopts=None,
               title=None, xtitle=None, ytitle=None,
               filllist= [tuple()], # a list of things passed to x[0] (and y[0])
                                    # by default, we will call h.Fill(x[0]()) once
                                    # take care not to overwrite your list, or pass
                                    # a parameterless function which returns the current list

               log="", # any of x, y, z, e.g. "yz"
               cond=lambda *args: True,
               color=None # automatically assign color
               ):
        res=empty()
        res.cv=cv
        res.cond=cond
        log=log.lower()
        if res.cv==None:
            res.cv=self.next_pad()
        objname=self.name+"/"+name
        res.filllist=filllist
        if y==None:
            res.hist=ROOT.TH1I(objname, name, *x[1:])
            res.hist.SetMinimum(int("y" in log))
            res.fill=lambda: [res.hist.Fill(x[0](*p)) for p in __tuplify__(res.filllist) if res.cond(*p)]
        else:
            res.hist=ROOT.TH2I(objname, name, *x[1:], *y[1:])
            res.hist.SetMinimum(int("z" in log))
            if drawopts==None:
                drawopts="colz"
            res.fill=lambda: [res.hist.Fill(x[0](*p), y[0](*p)) for p in __tuplify__(res.filllist) if res.cond(*p)]
        if title!=None:
            res.hist.SetTitle(title)
        if xtitle!=None:
            res.hist.GetXaxis().SetTitle(xtitle)
        if ytitle!=None:
            res.hist.GetYaxis().SetTitle(ytitle)
        for c in log:
            res.cv.__getattribute__("SetLog"+c)()
        if drawopts!=None:
            res.drawopts=drawopts
        else:
            res.drawopts=""
        res.draw=__default_draw__
        res.color=color
        res.updaterange=True # Should we set maximum automatically?
        res.codrawn={}       # hists we should update our maximum based on, filled by draw
        self.hists.append(res)
        return res


