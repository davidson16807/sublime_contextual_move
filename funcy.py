import re
from collections import defaultdict
from operator import methodcaller
from itertools import tee, chain, islice
try:
    from itertools import izip as zip
except ImportError:
    pass


### funcy seqs

def first(seq):
    return next(iter(seq), None)

def last(seq):
    try:
        return seq[-1]
    except IndexError:
        return None
    except TypeError:
        item = None
        for item in seq:
            pass
        return item


def nth(n, seq):
    """Returns nth item in the sequence or None if no such item exists."""
    try:
        return seq[n]
    except IndexError:
        return None
    except TypeError:
        return next(islice(seq, n, None), None)


def remove(pred, seq):
    return filter(complement(pred), seq)

def lremove(pred, seq):
    return list(remove(pred, seq))


def without(seq, *items):
    for value in seq:
        if value not in items:
            yield value

def lwithout(seq, *items):
    return list(without(seq, *items))

def pairwise(seq):
    a, b = tee(seq)
    next(b, None)
    return zip(a, b)

def with_next(seq, fill=None):
    a, b = tee(seq)
    next(b, None)
    return zip(a, chain(b, [fill]))


def count_reps(seq):
    """Counts number occurrences of each value in the sequence."""
    result = defaultdict(int)
    for item in seq:
        result[item] += 1
    return result


### funcy strings

def _make_getter(regex):
    if regex.groups == 0:
        return methodcaller('group')
    elif regex.groups == 1 and regex.groupindex == {}:
        return methodcaller('group', 1)
    elif regex.groupindex == {}:
        return methodcaller('groups')
    elif regex.groups == len(regex.groupindex):
        return methodcaller('groupdict')
    else:
        return identity

_re_type = type(re.compile(r''))

def _prepare(regex, flags):
    if not isinstance(regex, _re_type):
        regex = re.compile(regex, flags)
    return regex, _make_getter(regex)


def re_all(regex, s, flags=0):
    return list(re_iter(regex, s, flags))

def re_find(regex, s, flags=0):
    return re_finder(regex, flags)(s)

def re_test(regex, s, flags=0):
    return re_tester(regex, flags)(s)


def re_finder(regex, flags=0):
    regex, getter = _prepare(regex, flags)
    return lambda s: iffy(getter)(regex.search(s))

def re_tester(regex, flags=0):
    return lambda s: bool(re.search(regex, s, flags))


### funcy funcs

EMPTY = object()

def identity(x):
    return x

def complement(func):
    return lambda *a, **kw: not func(*a, **kw)

def iffy(pred, action=EMPTY, default=identity):
    if action is EMPTY:
        return iffy(bool, pred)
    else:
        return lambda v: action(v)  if pred(v) else           \
                         default(v) if callable(default) else \
                         default


### types tests

def isa(*types):
    return lambda x: isinstance(x, types)

from collections import Iterable
iterable = isa(Iterable)
