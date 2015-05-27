"""Options"""

import sys

from stuf import orderedstuf  #, chainstuf
# temporarily pulled stuf version of chainstuf in favor of
# local version until a bug with generator values can be
# tracked down and fixed
from options.chainstuf import chainstuf
from options.configparser import ConfigParser
from nulltype import NullType
from options.funclike import *
from options.combomethod import combomethod


# Define sentinel objects
Unset      = NullType('Unset')
Prohibited = NullType('Prohibited')
Transient  = NullType('Transient')
Reserved   = NullType('Reserved')

def bad_option_name(name):
    return hasattr(Options, name) or hasattr(OptionsChain, name)


class BadOptionName(AttributeError):
    """
    Raised when an Options object is given an option name that conflicts
    with an existing method.
    """
    pass


def attrs(m, first=[], underscores=False):
    """
    Given a mapping m, return a string listing its values in a
    key=value format. Items with underscores are, by default, not
    listed. If you want some things listed first, include them in
    the list first.
    """
    keys = first[:]
    for k in m.keys():
        if not underscores and k.startswith('_'):
            continue
        if k not in first:
            keys.append(k)
    return ', '.join(["{0}={1}".format(k, repr(m[k])) for k in keys])


class OptionsClass(object):

    """
    Class from which client classes can inherit. It will add ``set`` and
    ``settings`` methods.
    """

    @combomethod
    def set(receiver, **kwargs):
        """
        Change the receiver's settings to those defined in the kwargs.
        An update-like function. This uplevels calls that would look
        like ``Class.options.set(...)`` to the simpler ``Class.set(...)``.
        Works on either class or instance receivers. Requires that one
        uses the instance variable ``options`` to store persistent
        configuration data.
        """
        receiver.options.set(**kwargs)

    def settings(self, **kwargs):
        """
        Open a context manager for a `with` statement. Temporarily change settings
        for the duration of the with.
        """
        return OptionsContext(self, kwargs)

    def __repr__(self):
        return "{0}({1})".format(self.__class__.__name__, attrs(self.options))

class Options(orderedstuf):

    """
    Options handler.
    """

    def __init__(self, *args, **kwargs):
        orderedstuf.__init__(self, *args)
        for k, v in kwargs.items():
            if bad_option_name(k):
                raise BadOptionName("Options already defines an attribute {0!r}".format(k))
            else:
                self[k] = v
        self._magic = {}

        # The explicit for loop setting values from kwargs should not be necessary.
        # orderedstuf.__init__(self, *args, **kwargs) should do the trick. And it
        # does, on most platforms. But on PyPy, stuf(a=sys.stdout) fails in much
        # the same way used to on Python 3. Until stuf/orderedstuf is fixed for
        # PyPy, this workaround fixes the issue for Options. (Reconfirmed bug
        # still exists in PyPy 2.1 with stuf 0.9.12 in Sept 2013. Patch
        # retained.)

    def set(self, **kwargs):
        # To set values at the base options level, create a temporary next level,
        # which will have the magical option interpretation. Then copy the resulting
        # values here. Do in original ordering.
        oc = OptionsChain(self, kwargs)
        for key in self.keys():
            self[key] = oc[key]

    def setdefault(self, key, default):
        """
        If key is in the dictionary, return its value. If not, insert key with a
        value of default and return default. If the value is Prohibited, no
        change will be allowed, and a KeyError will be raised. If the value is
        Transient or Unset, it will be as if the value were never there, and the
        default will be set. NB ``setdefault`` does not participate in "magical"
        value interpretation.
        """
        try:
            value = self[key]
            if value is Prohibited:
                raise KeyError("changes to {0!r} are prohibited".format(key))
            elif value is Transient or value is Unset:
                self[key] = default
                return default
            else:
                return value
        except KeyError as e:
            # All keys must be defined in initial object construction,
            # even if defined as Unset or Transient. So if *no* value
            # is available for a key, definite error. Stricter than
            # general dict / mapping practice.
            raise e

        # In general usage, ``setdefault`` will be called only on ``OptionsChain``
        # instances, but defined for ``Options`` as well for completeness.

    def update(self, *args, **kwargs):
        """
        Update self with the given data. Necessary to avoid apparent bug in
        ``stuf`` when updating with iterable objects, especially generators. NB
        ``update`` does not participate in "magical" value interpretation.
        """
        for a in args:
            for k, v in a.items():
                self[k] = v
        for k, v in kwargs.items():
            self[k] = v

    def push(self, kwargs):
        """
        Create the next layer down. Intended for instances to call during
        ``__init__()``.

        """
        return OptionsChain(self, kwargs)

        # NB the implicit addflat() call is gone

    # def __iter__(self):
    #    for k in super(Options, self).keys():
    #        if not k.startswith('_'):
    #            yield k
    #    raise StopIteration

    def items(self):
        """
        Return items of self, but none that are 'internal' (ie start with underscore _)
        """
        return [(k, v) for (k, v) in super(Options, self).items() if not k.startswith('_')]

    def add(self, **kwargs):
        """
        Create the next layer down. Like ``push()``, but accepts full kwargs
        not just a dict. Intended for subclasses to call when defining their
        own class options. Not for instances to call.
        """
        child = OptionsChain(self, {})
        for key, value in kwargs.items():
            if bad_option_name(key):
                raise BadOptionName("OptionsChain already defines an attribute {0!r}".format(key))
            else:
                child[key] = value
        return child

    def parent(self, new_base):
        raise ValueError("Cannot change parent of base Options")

    def magic(self, **kwargs):
        """
        Set some options as having 'magical' update properties. In a sense, this
        is like Python ``properties`` that have a setter.  NB no magical
        processing is done to the base Options. These are assumed to have whatever
        adjustments are needed when they are originally set.
        """
        self.setdefault('_magic', {})
        for k, v in kwargs.items():
            self._magic[k] = real_func(v)

    def magical(self, key):
        """
        Instance based decorator, specifying a function in the using module
        as a magical function. Note that the magical methods will be called
        with a self of None.
        """
        def my_decorator(func):
            self._magic[key] = func
            return func

        return my_decorator

    def write(self, filepath):
        """
        Save configuration values to the given filepath.
        """
        c = INIConfig()
        for k, v in self.items():
            c.config[k] = v
        with open(filepath, "w") as f:
            f.write(str(c))

    def read(self, filepath):
        """
        Load configuration values from the given filepath.
        """
        c = INIConfig(open(filepath, "r"))
        for k in c.config:
            self[k] = c.config[k]

    def copy(self):
        """
        Return a copy of this instance.
        """
        new = orderedstuf.copy(self)
        new._magic = self._magic.copy()
        return new

        # UNDER CONSTRUCTION

        # use read, sections, itesms as in this note
        # http://stackoverflow.com/questions/3587041/python-
        # http://docs.python.org/dev/library/configparser.html

        # not sure why we take such care to get the order right for Options, because the
        # dict handed to Options.__init__ is not in order!

        # should there be a leftovers_ok option that raises an error on push()
        # if there are leftovers?


class OptionsChain(chainstuf):

    def __init__(self, bottom, kwargs):
        """
        Create an OptionsChain, pushing one level down.
        """
        chainstuf.__init__(self, bottom)
        processed = self._process(bottom, kwargs)
        self.maps = [processed, bottom]

    def _magicalized(self, key, value):
        """
        Get the magically processed value for a single key value pair.
        If there is no magical processing to be done, just returns value.
        """
        magicfn = self._magic.get(key, None)
        if magicfn is None:
            return value
        argcount = func_code(magicfn).co_argcount
        if argcount == 1:
            return magicfn(value)
        elif argcount == 2:
            return magicfn(value, self)
        elif argcount == 3:
            return magicfn(None, value, self)
        else:
            msg = 'magic functions take 1-3 arguments, not {0}'.format(argcount)
            raise ValueError(msg)

    def _process(self, base, kwargs):
        """
        Given kwargs, removes any key:value pairs corresponding to this set of
        options. Those pairs are interpreted according to'paramater
        interpretation magic' if needed, then returned as dict. Any key:value
        pairs remaining in kwargs are not options related to this class, and may
        be used for other purposes.
        """

        opts = {}
        for key, value in kwargs.items():
            if key in base:
                opts[key] = self._magicalized(key, value)

        # NB base identical to self when called from set(), but not when called
        # from __init__()

        # empty kwargs of 'taken' options
        for key in opts:
            del kwargs[key]

        return opts

    def __repr__(self):
        """
        Get repr() of OptionsChain. Dig down to find earliest ancestor, which
        contains the right ordering of keys.
        """
        grandpa = self.maps[-1]
        n_layers = len(self.maps)
        while not isinstance(grandpa, Options):
            n_layers += len(grandpa.maps) - 1
            grandpa = grandpa.maps[-1]

        guts = attrs(self, first=list(grandpa.keys()), underscores=True)
        return "{0}({1} layers: {2})".format(self.__class__.__name__, n_layers, guts)

    # def __iter__(self):
    #    for k in super(OptionsChain, self).keys():
    #        if not k.startswith('_'):
    #            yield k
    #    raise StopIteration

    def items(self):
        """
        Return items of self, but none that are 'internal' (ie start with underscore _)
        """
        return [(k, v) for (k, v) in super(OptionsChain, self).items() if not k.startswith('_')]

    def push(self, kwargs):
        """
        Create the next layer down. Intended for instances to call
        individual method invocations, where ``self.options`` is already
        an OptionChain.

        """
        return OptionsChain(self, kwargs)

        # NB Implicit addflat() has been removed

    def addflat(self, args, keys):
        """
        Sometimes kwargs aren't the most elegant way to provide options. In those
        cases, this routine helps map flat args to kwargs. Provide the actual args,
        followed by keys in the order in which they should be consumed. There can
        be more keys than args, but not the other way around. Returns a list of
        keys used (from which one can also determine if a key was not used).
        """
        if not args:
            return []
        if len(args) > len(keys):
            raise ValueError('More args than keys not allowed')
        additional = dict(zip(keys, args))
        self.update(additional)
        keys_used = list(additional.keys())
        return keys_used

    def add(self, **kwargs):
        """
        Create the next layer down. Like ``push()``, but accepts full kwargs
        not just a dict. Intended for subclasses to call when defining their
        own class options. Not for instances to call.
        """
        child = OptionsChain(self, {})
        for key, value in kwargs.items():
            if bad_option_name(key):
                raise BadOptionName("OptionsChain already defines an attribute {0!r}".format(key))
            else:
                child[key] = value
        return child

    def parent(self, new_base):
        """
        Rebase the mapping (change its parent). Useful for implementing
        "styles"
        """
        raise NotImplementedError()

    def set(self, **kwargs):
        newopts = self._process(self, kwargs)
        for k, v in newopts.items():
            if v is Unset:
                del self.maps[0][k]
            elif self[k] is Prohibited:
                raise KeyError("changes to '{0}' are prohibited".format(k))
            else:
                self.maps[0][k] = v

    def setdefault(self, key, default):
        """
        If key is in the dictionary, return its value. If not, insert key with a
        value of default and return default. If the value is Prohibited, no
        change will be allowed, and a KeyError will be raised. If the value is
        Transient or Unset, it will be as if the value were never there, and the
        default will be set. NB ``setdefault`` does not participate in "magical"
        value interpretation.
        """
        try:
            value = self[key]
            if value is Prohibited:
                raise KeyError("changes to {0!r} are prohibited".format(key))
            elif value is Transient or value is Unset:
                self[key] = default
                return default
            else:
                return value
        except KeyError as e:
            # All keys must be defined in initial object construction,
            # even if defined as Unset or Transient. So if *no* value
            # is available for a key, definite error. Stricter than
            # general dict / mapping practice.
            raise e

    def update(self, *args, **kwargs):
        """
        Update self with the given data. Necessary to avoid apparent bug in
        ``stuf``, ``orderedstuf``, or ``chainstuf`` when updating with iterable
        objects, especially generators. NB ``update`` does not participate in "magical"
        value interpretation.
        """
        for a in args:
            for k, v in a.items():
                self[k] = v
        for k, v in kwargs.items():
            self[k] = v

    def copy(self):
        """
        Return a copy of the self. That means a copy of just the top layer,
        with bottom layers showing through.
        """
        new = OptionsChain(self.maps[1], {})
        for k, v in self.items():
            new[k] = v
        return new

    # TBD Need to examine all the places we need to check for Prohibited
    # when setting values - eg, what about in Options

    # Do we want to define a more specific exception for Prohibited?

    # TBD when using Prohibited values, __getattr__ and __getitem_ should raise
    # an exception when being accessed extenrally

    #  TBD Handle the unsetting of magic in subclasses


    # def __setattr__(self, name, value):
    #    print "OptionsChain.__setattr__() name:", name, "value:", value
    #    if name in self:
    #        print "    in self"
    #        if value is Unset and name in self.maps[0]:
    #            # only unset the very top level
    #            del self.maps[0][name]
    #        else:
    #            self[name] = self._magicalized(name, value)
    #    else:
    #        print "    not in self; punt to superclass"
    #        chainstuf.__setattr__(self, name, value)
    # could possibly extend set() magic to setattr (but would have to be
    # careful of recursions). Current draft doesn't work - infinite recursion
class OptionsContext(object):

    """
    Context manager so that modules that use Options can easily implement
    a `with x.settings(...):` capability. In x's class:

    def settings(self, **kwargs):
        return OptionsContext(self, kwargs)
    """

    def __init__(self, caller, kwargs):
        """
        When `with x.method(*args, **kwargs)` is called, it creates an OptionsContext
        passing in its **kwargs.
        """
        self.caller = caller
        if 'opts' in kwargs:
            newopts = OptionsChain(caller.options, kwargs['opts'])
            newopts.maps.insert(0, caller._process(newopts, kwargs))
        else:
            newopts = OptionsChain(caller.options, kwargs)
        caller.options = newopts

    def __enter__(self):
        """
        Called when the `with` is about to be 'entered'. Whatever this returns
        will be the value of `x` if the `as x` construction is used. Not generally
        needed for option setting, but might be needed in a subclass.
        """
        return self.caller

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Called when leaving the `with`. Reset caller's options to what they were
        before we entered.
        """
        self.caller.options = self.caller.options.maps[-1]

    # Using a with statement and OptionsContext can effectively reduce the
    # thread safety of an object, even to NIL. This is because the object is
    # modified for an indeterminate period. It would be possible to improve
    # thread safety with an with..as construction, if what was returned by as
    # were a proxy that didn't modify the original object.  Another approach
    # might be to provide per-thread options, with _get_options() looking
    # options up in a tid-indexed hash, and set() operations creating a copy
    # (copy-on-write, per thread, essentially).

    # with module quoter have found some interesting use cases like abbreviation
    # args (MultiSetter), and have further explored how subclasses will integrate
    # with the delegation-based options. Have discovered that some subclasses will
    # want flat args, prohibit superclass args. Also, some args could potentially
    # allow setting at instantiation time but not call/use time.

    # Would it make sense to support magicalized class setting -- for subclasses?
    # even if it would, how to accomplish neatly? probably would require a
    # property like object that lets you assign the magic along with the
    # initial value

    # next step: integrate setter from testprop.py
    # consider adding _for key pointing to object that options are for
    # also providing access to whole dict for arguments like chars
    # and clean up HTMLQuoter using the improved functions & access

    # quoter might provide the usecase for a getter, too - in that suffix is == prefix
    # if suffix itself not given

    # instead of Magic() or Setter() maybe Property() or Prop()
