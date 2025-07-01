#!/usr/bin/env -S python3 
import numpy
import h101
import h101.tdc_cal
import numpy as np
from numpy.linalg import norm
import re
import math
from math import *
import ROOT
import inspect
import sys, os
import itertools
import numpy as np
import subprocess
from scipy.optimize import least_squares
from functools import partial
import os.path
import signal

from time import sleep

import online_base
import online_los
import online_sync
from config import unpacker, source, port, losparams, tdcsync

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

def main():
   global end, d
   h101.tdc_cal.readcals("cal.json")
   h101.tdc_cal.filterre=re.compile("(LOS|TOF).*")
   h=h101.mkh101(inputs=source, unpacker=unpacker)
   #h.tpat_mask=0x1
   d=h.getdict()
#globals().update(d)
   onlines=[]
   if False:
      print(d)
      exit(1)
   online_base.http_inst=ROOT.THttpServer("http:%d"%port)
   for losno, pars in losparams.items():
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
   if len(tdcsync)>1:
      onlines.append(online_sync.online_sync("tdc sync", d, tdcsync))
   n, m=0,0
   #TPAT=d["TPAT"]
   while h.getevent() and not end:
      n+=1
      if (not n%1000):
          print(m, n)
          ROOT.gSystem.ProcessEvents()
          #print(d)
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
   end=False
   print("data finished or ^Ced, running jsroot only, ^C to exit")
   while not end:
      ROOT.gSystem.ProcessEvents()
      sleep(0.01)


if __name__=="__main__":
    try:
        main()
    except Exception as e:
        if h:
            h.unpacker.kill()
        raise e


exit(0)

for obj in hists:
    dname, fname = os.path.split(obj.GetName())
    print("%s %s"%(dname, fname))
    if dname!="":
        fr.mkdir(dname, "", True).WriteObject(obj, fname)
    else:
        fr.WriteObject(obj, fname)



