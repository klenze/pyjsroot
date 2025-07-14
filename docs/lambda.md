== Lambdas 101, the short version ==
Lambda expressions in Python define anonymous functions.

Say we have a higher order function:

```
def applytwice(f, x):
    return f(f(x))
```

This function takes a function f and a value x and returns ``f(f(x))``. We can call it like this:
```
def increment(x):
    return x+1

applytwice(increment, 40)
```

However, this is a bit bothersome, because we have to waste multiple lines to define increment, and have it pollute our current namespace with ``increment``. 

Luckily, we do not have to, instead we can use:
```
applytwice(lambda x: x+1, 40)
```

The general syntax is "lambda ", followed by a comma separated list of variable names which denote arguments your function will take (or nothing if you want a function without arguments), followed by ":" followed by an expression which specifies what the function should return.

Google [python lambda](https://google.com/search?q=python+lambda) for more examples and tutorials on this.

== How Python lambda expressions are weird ==

Python lambdas are a bit weird in how they treat free variables (which is the same as for inner functions). Rather then capturing them by reference at the time the lambda is defined, they will remember the scope in which the lambda was defined (prolonging its life if required) and interpret any free variables with respect to that scope.

Say we want to generate a list of functions which take one argument, and add i to it, where i is their position in the list, so
```
addN=[lambda x: x+0, lambda x: x+1, lambda x: x+2]
```
There are different ways we could create such a list of lambda expressions, for example for loops
```
ForAddN=[]
for n in range(3):
    ForAddN.append(lambda x: x+n)
```
Or list comprehension:
```
LCAddN=[lambda x:x+n for n in range(3)]
```

Or pure functional syntax:
```
MapAddN=list(map(lambda n: lambda x: x+n, range(3)))
```
MapAddN will work as intended, but ForAddN and LCAddN will not:
```
add1=ForAddN[1]; add1(2) # returns 4, not 3
add1=LCAddN[1];  add1(2) # returns 4, not 3
add1=MapAddN[1]; add1(2) # returns 3 as expected
```

This is because for the map variant, all the values of n have their own scope (as they are bound variables in the outer lambda). In the for loop variant, all of them will refer to the local variable n (which ends up being 2, but we can still set it to whatever we want. In the list comprehension variant, the different values of n share a single scope (which is not the local scope at least since Python 3) because the developers of Python prize speed over correctness.

There are multiple possible workarounds. We can use map expressions everywhere, which will likely confuse people. We can use functools.partial, which is better than having an explicit higher order lambda, but still not great:
```
from functools import partial
LCAddN=[partial(lambda x, N: x+N, N=n) for n in range(3)]
```

The preferred solution is to abuse default arguments, for example:
```
LCAddN=[lambda x, N=n: x+N for n in range(3)]
```
Commonly, we can use the same name for N and n, with the understanding that they refer to things in different scopes:
```
LCAddN=[lambda x, n=n: x+n for n in range(3)]
```

This has the advantage that it plays nicely with Python syntax and is shorter than partial. It has the disadvantage that it allows us to override the default parameter, so ``LCAddN[0](5,4)`` is now suddenly a thing.

This is relevant when creating multiple histograms, e.g. in a for loop (or with list comprehension). Consider:
```
        for i in range(1, 9):          
             h=self.mkHist("vftx_diff_%d"%i,
                           x=(lambda: self.vtimes[i], 2000, -8, 8))
```
After the for loop is done, i will be 8, so you will get eight histograms which all show the time difference in channel eight. Sad!

To fix this, we can use the trick discussed above:
```
        for i in range(1, 9):          
             h=self.mkHist("vftx_diff_%d"%i,
                           x=(lambda i=i: self.vtimes[i], 2000, -8, 8))
```


