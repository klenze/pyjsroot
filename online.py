#!/usr/bin/env -S python3 
import numpy
import h101


import sys, os
os.environ["DISPLAY"]=""


import h101.tdc_cal
import numpy as np
from numpy.linalg import norm
import re
import math
from math import *
import ROOT
import inspect
import itertools
import numpy as np
import subprocess
from scipy.optimize import least_squares
from functools import partial
import os.path
import signal

from time import sleep, time

import online_base
import online_los
import online_tdcsync
import online_wrsync
import online_rolu
import online_tof
import online_example

assert len(sys.argv)<=2, "Usage: %s [config].py"%sys.argv[0]
if len(sys.argv)==2:
    cfgfile=sys.argv[1][:-3]
else:
    cfgfile="config"


cfg=__import__(cfgfile, globals(), locals(), ["unpacker", "source", "options", "port", "losparams", "tdcsync", "wrsync", "example"], 0)


end=False

h=None

def handle_sig_int(sig, frame, reason="Caught ^C"):
    end=True
    if h:
        h.unpacker.kill()
    print("%s, dying"%reason)
    os.kill(os.getpid(), 9)
    

signal.signal(signal.SIGINT, handle_sig_int)

#upexps="/u/land/fake_cvmfs/11/extra_jan24p1/upexps/202503_s122/202503_s122"

#sp=subprocess.Popen(upexps+" --stream=lxlanddaq01:9100 --ntuple=RAW,STRUCT,-", shell=True,
#        stdout=subprocess.PIPE, stderr=subprocess.PIPE)


lmap=lambda *a,**kw:list(map(*a, **kw))

#f=open(sys.argv[1], "br")
#h=h101.H101(fd=f.fileno())


d=None

use_tof="|TOF"

def main():
   global end, d
   h101.tdc_cal.readcals("cal.json")
   h101.tdc_cal.filterre=re.compile("^(LOS|ROLU|TIME%s).*"%use_tof)
   h=h101.mkh101(inputs=cfg.source, unpacker=cfg.unpacker, options=cfg.options)
   #h.tpat_mask=0x1
   d=h.getdict()
#globals().update(d)
   onlines=[]
   if False:
      print(d)
      exit(1)
   online_base.http_inst=ROOT.THttpServer("http:%d"%cfg.port)
   online_base.http_inst.SetTopName("%s"%cfg.source)
   for losno, pars in cfg.losparams.items():
      los=online_los.online_los(losno, d[losno+"VT"], d[losno+"TT_tot"], offset=0)
      for k, v in pars.items():
          if not hasattr(los, k):
              print("%s: parameter %s is assigned to %s in config, but there is no such parameter."%(losno, k, v))
              exit(1)
          vold=getattr(los, k)
          if type(vold)==np.ndarray and type(v)==list:
              v=np.array(v, dtype=vold.dtype)
          if type(vold)!=type(v):
              print("%s: parameter %s is assigned to type %s in config, but should be of type %s."%(losno, k, type(v), type(vold)))
              exit(1)
          if hasattr(vold, "__len__") and len(vold) != len(v):
              print("%s: parameter %s is assigned with a length of %d in config, but should have a length of %s."%(losno, k, len(v), len(vold)))
              exit(1)
          setattr(los, k, v)
      onlines+=[los]
      los.tot_scale/=sum(los.tot_scale[1:9])/8
   if True:
       onlines.append(online_rolu.online_rolu("rolu", d["ROLU1TT_tot"]))
   if use_tof!="":
       onlines.append(online_tof.online_tof("tof", d))
   if len(cfg.tdcsync)>1:
      onlines.append(online_tdcsync.online_tdcsync("tdc sync", d, cfg.tdcsync))
   if len(cfg.wrsync)>0:
      onlines.append(online_wrsync.online_wrsync("wr sync", d, cfg.wrsync))
   for i in cfg.example:
      onlines.append(online_example.online_example("example %s"%i, d[i]))
   print(onlines)
   n, m=0,0
   #TPAT=d["TPAT"]
   last_update=time()
   last_count=0
   while h.getevent() and not end:
      n+=1
      #print(d["TIMESTAMP_MUSIC"], d["TIMESTAMP_BUS"], d["TIMESTAMP_MUSIC"]-d["TIMESTAMP_BUS"])
      if (time()>last_update+1):
          print("processed %12d of %12d events, %d events in the last second"%(m, n, m-last_count))
          last_count=m
          last_update=time()
          ROOT.gSystem.ProcessEvents()
          if (int(time())%10==0):
              print(d)
              pass
          if not n%12000:
               h101.tdc_cal.writecals("cal.json")

      #if len(TPAT)!=1 or not TPAT[0]&1:
      #    continue
      #if 1 not in LOS1TT_tot.keys():
      #    continue
      #print(d)
      for on in onlines:
          on.process()
      m+=1
   if cfg.source.find("lmd")==-1:
       print("stream data ended, will quit now.")

   end=False
   print("data finished or ^Ced, running jsroot only, ^C to exit")
   while not end:
      ROOT.gSystem.ProcessEvents()
      sleep(0.01)


if __name__=="__main__":
    try:
        main()
    except Exception as e:
        if type(e)==KeyError:
            print("Key error, just in case here is the main dict")
            print(d)
        if h:
            h.unpacker.kill()
        #handle_sig_int(0, 0, "Exception")
        raise e


exit(0)

for obj in hists:
    dname, fname = os.path.split(obj.GetName())
    print("%s %s"%(dname, fname))
    if dname!="":
        fr.mkdir(dname, "", True).WriteObject(obj, fname)
    else:
        fr.WriteObject(obj, fname)



