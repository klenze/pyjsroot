unpacker="/u/land/fake_cvmfs/11/extra_jan24p1/upexps/202507_sfrs/202507_sfrs"
options="--allow-errors --input-buffer=600Mi"
#unpacker="/u/land/fake_cvmfs/11/extra_jan24p1/upexps_202506_g249/upexps/run/run_all --input-buffer=138Mi"
#source="stream://lxir133:7723"  
#source="stream://lxlanddaq01:9100"  
#source="stream://lxlanddaq01:9003"  
source="/lustre/sfrs/SfrsDetTests/2025jul/lmd/main0008_0001.lmd"

nan=float("nan")

#source="pulsertest.lmd"
port=8889

losparams={
 "LOS1":{
         "vftxoffsets":[nan, -2.102, -1.215, -0.5124, 0.08364,
                              0.02885, 1.073, 1.845, 0.8041],
         "tot_scale": [nan, 544.6, 546.1, 546.3, 545.2, 546.0, 552.9, 552.2, 548.5]
        }, 
 "LOS2":{},
 "LOS3":{},
 }



tdcsync=[
   ("TOF1VT", 16),
   ("TOF1VT", 1),
   ("LOS1VT", 1),
   ("LOS2VT", 5),
   ("LOS1TT_tot", 1),
   ("LOS2TT_tot", 5),
   ("TOF2VT", 16),
   ("TOF3VT", 16)]


wrsync=["BUS", "FIBERS", "MUSIC"]

example=["LOS1VT"]
