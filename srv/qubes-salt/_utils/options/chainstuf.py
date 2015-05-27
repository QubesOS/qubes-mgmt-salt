"""
Sidecar to ``stuf`` that adds ``ChainMap``-like
container ``chainstuf``.  ``stuf`` itself provides
a ``chainstuf``, but as of 0.9.12, it has a bug
when using generators as mapping values. I have
not been able to track it down, so this less-complete
version that nonetheless lacks the generator bug
is used instead.
"""

try:
    from collections import ChainMap
except ImportError:
    from stuf.collects import ChainMap


class chainstuf(ChainMap):

    """
    A stuf-like surfacing of the ChainMap collection
    (multi-layer dict) introduced in Python 3. Uses a
    workalike replacement under Python 2.
    """

    def __init__(self, *maps):
        ChainMap.__init__(self, *maps)

    def __getattr__(self, key):
        # handle normal object attributes
        if key in self.__dict__:
            return self.__dict__[key]
        # handle special attributes
        else:
            for m in self.maps:
                try:
                    return m[key]
                except KeyError:
                    pass
            raise KeyError(key)

    def __setattr__(self, key, value):
        # handle normal object attributes
        if key == 'maps' or key in self.__dict__:
            ChainMap.__setattr__(self, key, value)
        else:
            self.maps[0][key] = value
