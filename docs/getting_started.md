# Getting started

## Prerequisites

You need standard python libraries such as numpy. 

You need pyh101, which does all of the work not related to histogramming and plotting. 

## Running pyjsroot

To run the program, you require a configuration, which is for now stored in a python file. See ``sample_config.py``. You can pass online which configuration you want to run:
```
  $ ./online.py my_config.py
```

## Adding histograms

Plese read ``online_example.py`` for a basic class which creates some histograms. Note that if you add a new class, you will also need to instantiate it in online.py. We will find a better way to deal with this later. 

## More details on histograms

For my ```online_base.py```, I let the user specify a histogram using a syntax like

```
    h=self.mkHist("MyHistName/Title",
                  x=(xlambda, xbins, xmin, xmax),
		  y=(ylambda, ybins, ymin, ymax),
		  filllist=fillobj)
```

See the ``online_base.py`` for all of the options. The idea is that this allows you to specify the whole histogram, name, ranges and what goes into it.

If y is unset, you get a TH1I, otherwise you get a TH2I. If xlambda is None, no automatic filling will happen, it is your responsibility to store h.hist (which points the the THxI object) and call its Fill method.

If xlambda is not None, then for each event, we will iterate over the objects in filllist and pass them to xlambda (and possibly ylambda), then call Fill once per object with the result(s). If filllist is a dictionary, we will iterate over filllist.items(). If it is a lambda expression, we will call it, then iterate over the result. If filllist is not set, we will call xlambda (and ylambda, if present) once without arguments.

For example, consider:
```
        h=self.mkHist("VFTX multiplicities",
                      x=(lambda n,lst: n, 8, 0.5, 8.5),
                      y=(lambda n,lst: len(lst), 10, 0, 10),
                      filllist=d["LOS1VT"])
```
"For each event, iterate over the entries of the time calibrated LOS VFTX hits, calling TH2I::Fill() once per entry. On the xaxis, I want to plot the channel number from 1 to 8, on the yaxis, I want to plot the multiplicities from zero to 10."

(Note that we will never fill the y=0 bin, because our dictionary only contains entries which have at least one hit. If we wanted that, we would use ``filllist=[i+1 for i in range(8)], x=(lambda n:n, ...), y=lambda n:len(d["LOS1VT"].get(n, []))``. We might also like to move the ``d["LOS1VT"]`` out of the lambda.)

This is at the moment a (imho promising) proof of concept. 

Feel free to contact me (Philipp) if you have troubles or suggestions.
