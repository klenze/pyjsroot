One of the time-honored traditions of R3B is that at some point, DAQ people write their own analysis framework as an alternative to FairRoot/R3BRoot, and try unsuccessfully to get the collaboration to adopt it.

This here is then me trying exactly that.

The other day, I wanted to integrate a new detector prototype (FastTof, which is currently read out with VTFX modules) into the online analysis so that I can check coarse and fine time correlations between it and LOS with a pulser.

Here are the steps I would have had to do in R3BRoot (following current best practices, starting with a working LOS time calibration and online):
* Create directories R3BRoot/fasttof/, R3BRoot/r3bdata/fasttof/, R3BRoot/r3bsource/fasttof/
* Generate a h101 header ``ext_h101_fasttof.h`` from the unpacker, and copy it to r3bsource
* Write a class R3BFastTofMappedData (h, cxx)
* Write a class R3BFastTofReader (h, cxx), which reads the h101 data and puts it into a TClonesArray
* Write a class R3BFastTofCalData (h, cxx)
* Write a class R3BFastTofMap2Cal (h, cxx) which applies uses R3BRCalEngine to generate the time calibration
* Write a class R3BFastTofMap2CalPar (h, cxx) which generates the time calibration
* Write class R3BFastTofLosOnlineSpectra (h, cxx) which reads R3BFastTofCalData and R3BLosCalData, calculates the differences and plots them.
* Write R3BRoot/fasttof/FastTofLinkDef.h
* Edit ``*LinkDef.h`` files in r3bdata and r3bsource
* Write R3BRoot/fasttof/CMakeLists.txt
* Edit the CMakeLists.txt in R3BRoot, r3bdata and r3bsource
* Write a macro ``fasttof_cal.C`` which specifies a struct containing the struct ``ext_h101_fasttof``, feeds that struct to the R3BFastTofReader, then instantiates R3BFastTofMap2CalPar and writes the time calibration data (as R3BTCalPar) to a root file using the FairRoot parameter API.
* Write a second macro ``fasttoflos_online.C`` which specifies a struct containing the struct ``ext_h101_fasttof``, feeds that struct to the R3BFastTofReader, load the time calibration data using the FairParam API, instantiates R3BFastTofMap2Cal, instantiates R3BFastTofLosOnlineSpectra.

So in total, that will be six new classes, 14 new files in the main git (plus two in R3BParams), plus edits in five more.

Of these, only R3BFastTofLosOnlineSpectra will contain any new code. Everything else will be virtually identical to existing TDC classes for LOS or TofD, except for a few array sizes and names. These five classes will just be technological debt added because we do not like templates.

Also, R3BFastTofLosOnlineSpectra will not be very flexible, if I want to pulser test other TDC systems which should run on the same 200MHz clock (Neuland, TofD, Fibers) I will have to either add all of them to that class, copy that class or find existing Los+X Spectra classes to add my histograms in.



Obviously, I did not do that. Instead, I had started out with pyh101 plus a basic framework for setting up an online analysis and a rudimentary los online analysis.

I wrote another Python class for showing tdc syncs online, which took me less than an hour, and added about five lines of code to instantiate it (and enable unpacking for TOF) in my main script.

Finally, I added the lines the pulsed channels to the configuration:
```
tdcsync=[
   ("LOS1VT", 1),     # reference, LOS VFTX #1
   ("LOS2VT", 5),     # LOS VFTX #2
   ("LOS1TT_tot", 1), # LOS TAMEX #1
   ("LOS2TT_tot", 5), # LOS TAMEX #2
   ("TOF1VT", 16),
   ("TOF2VT", 16),
   ("TOF3VT", 16)]
```
Apart from the RE which controls what gets unpacked, these lines are the only place where I explicitly refer to the FastTof. Everything else is automatic. pyh101 figures out that six arrays TOF[123]VT[CF] are provided by the unpacker and transforms them into python structures. A python function figures out that TOF1VF and TOF1VC have a naming scheme which indicates TDC data and applies a fine time calibration on the fly, which means that the first 10k hits are NaN, then you get calibrated data. Calibrations are cached, so the next time the previous calibration is used until you have accumulated enough statistics.

