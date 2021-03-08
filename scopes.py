# -*- coding: utf-8 -*-

"""
Contents modified from Alexander Schepanovski's Reform plugin, credit goes to him: https://github.com/Suor/sublime-reform
"""

import sublime, sublime_plugin
ST3 = sublime.version() >= '3000'

from functools import partial, reduce
from itertools import takewhile, chain

try:
    from .funcy import *
    from .viewtools import *
except ValueError: # HACK: for ST2 compatability
    from funcy import * 
    from viewtools import *

'''
NOTE: Our design goal is to commute the following diagram using our implementation:
```
% https://tikzcd.yichuanshen.de/#N4Igdg9gJgpgziAXAbVABwnAlgFyxMJZAJgBpiBdUkANwEMAbAVxiRACEQBfU9TXfIRRkAzFVqMWbAKLdeIDNjwEiI8uPrNWiEAAU5fJYNWkAjBsna9Bhf2VCSZi1pk3FAlcNIAGZ1J2cPIYeDqZO1Jr+IABKbnbGKGFiEZZssUG2Rp7IYQCsflbp8u72RGQALAVsgcXx2WT5KS46shklCchqlU1R+m11Dt6k3RLNIAAqcVmD6j1Wk1ziMFAA5vBEoABmAE4QALZIZCA4EEhDo1Fo2zA0AEYwK1iE1Ax09wy6A2zbWCsAFjgbDt9odqCckGELlYwDAAB44GBgKBA3YHRCQ8GIc6RKxXG73R6EDLAtHnTGQuB-LCbQGIAC0kJxbBh8MRyOJqLOYNOiDUULYeJoAGM-nRtiiQbzuUhcnMBdc7g8niAXm8YB8vjofv9ARzJbLjjzynq0QA2aWIcovJ5WKAQHAI9nyElIc2GmXWmFsO0O5YStEAdgtboYNrYcAgoeRcp0guujxUJqQVvdiANlOptIZScQQdT51DXp0Psd-qQefJntt9tLOYAHBbTAWw8Wa376xaAJxV71tp1bTm5i0NkCFqwRqMq-k6Fk4ePGVXvT7Tb6-AFlxDd1NN6gZmlIbPOwc71OdnMYnmmRmpGdwnAisVT15LzUgbXr88XiHec9HTF5sde19fsQBddE-x5EdANbYCN1MPlMRDFsQBLdsj0leCLQA5DUJAsCK0vPk9yzUwcwIiEjmIiEcwgpARBzBCeUoql93pUj0LRWj0XYgcMK-RBmMzaiKC4IA
\begin{tikzcd}
                                        &                                                                                                                                          & B \arrow[d]                                               &                                                                      \\
                                        & R \arrow[r, dotted] \arrow[ru, dotted]                                                                                                   & E \arrow[u, shift left]                                   & P \arrow[lu, "prevbegin"'] \arrow[d, shift left]                     \\
T \arrow[ru, dotted] \arrow[rd, dotted] &                                                                                                                                          & B \arrow[d, "nextend", shift left] \arrow[ru, "prevchar"] & P \arrow[l, "prevbegin"'] \arrow[ld, "nextend"] \arrow[u] \arrow[dd] \\
                                        & R \arrow[uu, "prevregion"] \arrow[ru, dotted] \arrow[r, dotted] \arrow[dd, "nextregion"'] \arrow[lu, shift left] \arrow[ld, shift right] & E \arrow[u, "prevbegin"] \arrow[rd, "nextchar"']          &                                                                      \\
T \arrow[ru, dotted] \arrow[rd, dotted] &                                                                                                                                          & B \arrow[d, shift left]                                   & P \arrow[ld] \arrow[uu, shift right]                                 \\
                                        & R \arrow[r, dotted] \arrow[ru, dotted]                                                                                                   & E \arrow[u]                                               &                                                                     
\end{tikzcd}
```
Where "P" is a point, "R" is a region, "E" is the end of a region, "B" is the beginning of a region, and "T" is a transposition between regions.

This design allows us to define a region type (e.g. word, function, class, etc.) using only two functions:
one to express for any position how to get to the very next region end going down,
and the other to express for any position how to get to the very next region beginning going up.
By composing these two you can construct the boundaries for any region,  
and combining these functions with character traversal lets you find the boundaries of adjacent regions.
Certain types of regions (e.g. functions or classes) may be easier to define by first obtaining a full list of regions,
and these types can be defined using the two aforementioned functions by comparing known region boundaries with current position. 
However this approach is not suitable for region types like words, where there are a large number of regions to consider.
This approach allows us to define both kinds of region types using a single common interface.
'''


class MoveByScopeCommand(sublime_plugin.TextCommand):
    def run(self, edit, forward, by, expand = False, complete = False, delete = False):
        demarcation_ = demarcation(self.view, by)
        if expand:
            set_selection(self.view, 
                map(partial(expansion, RegionExpansion(demarcation_), forward, complete), 
                    self.view.sel()))
        elif delete:
            set_selection(self.view, 
                map(partial(completion, demarcation_, forward), 
                    self.view.sel()))
            self.view.run_command('left_delete')
        elif complete:
            set_selection(self.view, 
                map(partial(completion, demarcation_, forward), 
                    self.view.sel()))
        else:
            set_selection(self.view, 
                map(partial(movement, RegionTraversal(demarcation_), forward), 
                    self.view.sel()))


class IndentScopeCommand(sublime_plugin.TextCommand):
    def run(self, edit, forward, by):
        demarcation_ = demarcation(self.view, by)
        set_selection(self.view, 
            map(partial(completion, demarcation_, forward), 
                self.view.sel()))
        self.view.run_command('indent' if forward else 'unindent')

class TransposeByCommand(sublime_plugin.TextCommand):
    def run(self, edit, forward, by):
        demarcation_ = demarcation(self.view, by)
        set_replacements(self.view, edit,
            map(partial(transposition, RegionTraversal(demarcation_), self.view, forward), 
                self.view.sel()))

# SECTION: FUNCTIONS WITH SIDE EFFECTS THAT ARE USED TO COMPOSE COMMANDS
def set_selection(view, region):
    # NOTE: we need to materialize a possible iterator before clearing selection,
    #       as mapping selection is a common techique.
    if iterable(region):
        region = list(region)

    view.sel().clear()
    add_selection(view, region)
    view.show(view.sel())

def add_selection(view, region):
    if iterable(region):
        if ST3:
            view.sel().add_all(list(region))
        else:
            # .add_all() doesn't work with python lists in ST2
            for r in region:
                view.sel().add(r)
    else:
        view.sel().add(region)

def set_replacements(view, edit, replacements):
    replacements = list(replacements) if iterable(replacements) else replacements
    view.sel().clear()
    for replacement in replacements:
        view.replace(edit, replacement.region, replacement.text)
    view.sel().add_all([replacement.selection for replacement in replacements])
    view.show(view.sel())

# SECTION: FUNCTIONS WITHOUT SIDE EFFECTS THAT ARE USED MAP SELECTIONS
def movement(traversal, forward, current):
    if forward: return traversal.next(current).begin()
    else: return traversal.prev(current).begin()

def completion(demarcation, forward, current):
    if forward: return sublime.Region(demarcation.prevbegin(current.begin()), demarcation.nextend(current.end())) 
    else: return sublime.Region(demarcation.nextend(current.end()), demarcation.prevbegin(current.end()))

def expansion(expansion_, forward, complete, current):
    if current.size() < 1 and complete: return completion(expansion_.demarcation, forward, current)
    else: return expansion_.next(current) if forward else expansion_.prev(current)

def transposition(traversal, view, forward, current):
    source = completion(traversal.demarcation, forward, current) if current.size() < 1 else current
    if forward:  
        destination = traversal.next(source)
        inbetween = sublime.Region(source.end(), destination.begin())
        top = view.substr(source) 
        bottom = view.substr(destination)
        middle = view.substr(inbetween)
        offset = destination.size() + inbetween.size()
    else:
        destination = traversal.prev(source)
        inbetween = sublime.Region(source.begin(), destination.end())
        top = view.substr(destination)
        bottom = view.substr(source)
        middle = view.substr(inbetween)
        offset = -destination.size()
    return Replacement(
        source.cover(destination), 
        bottom+middle+top, 
        sublime.Region(current.a + offset, current.b + offset))

# SECTION: MISCELLANEOUS FUNCTIONS AND STRUCTURES THAT ARE USED TO COMPOSE COMMANDS
def demarcation(view, type):
    return {
        'subwords': lambda: SubWordDemarcation(view),
        'words': lambda: WordDemarcation(view),
        'separators': lambda: ListItemDemarcation(view),
        'functions': lambda: PredefinedRegionDemarcation(list_defs(view) or list_blocks(view)),
        'classes': lambda: PredefinedRegionDemarcation(list_class_defs(view) or list_blocks(view)),
    }[type]()

class Replacement:
    def __init__(self, region, text, selection):
        self.region = region
        self.text = text
        self.selection = selection

# SECTION: CATEGORIES THAT OPERATE ON GENERIC REGION DEMARCATIONS
class RegionExpansion:
    """A category of functions iterating through regions.
    Given a categories for character traversal and region demarcation, 
    a region traversal category exists. 
    These required categeroies are defined later in the document"""
    def __init__(self, region_demarcation):
        self.demarcation = region_demarcation
    def prev(self, region):
        return sublime.Region( region.a, self.demarcation.prevbegin(region.b-1) )
    def next(self, region):
        return sublime.Region( region.a, self.demarcation.prevbegin(self.demarcation.nextend(region.b+1)) )

class RegionTraversal:
    """A category of functions iterating through regions.
    Given a categories for character traversal and region demarcation, 
    a region traversal category exists. 
    These required categeroies are defined later in the document"""
    def __init__(self, region_demarcation):
        self.demarcation = region_demarcation
    def prev(self, region):
        begin = self.demarcation.prevbegin(region.begin()-1)
        end = self.demarcation.nextend(begin)
        return sublime.Region( begin, end )
    def next(self, region):
        end = self.demarcation.nextend(region.end()+1)
        begin = self.demarcation.prevbegin(end)
        return sublime.Region( begin, end )

# SECTION: CATEGORIES THAT DEFINE TYPES OF REGIONS
class SubWordDemarcation:
    """a category of functions mapping positions to region boundaries,
    effectively providing the definition of a region"""
    def __init__(self, view):
        pass
    def prevbegin(self, position):
        return self.view.find_by_class(position, False, 
            sublime.CLASS_SUB_WORD_START | 
            sublime.CLASS_SUB_WORD_END | 
            sublime.CLASS_PUNCTUATION_START | 
            sublime.CLASS_PUNCTUATION_END | 
            sublime.CLASS_LINE_END | 
            sublime.CLASS_EMPTY_LINE
        )
    def nextend(self, position):
        return self.view.find_by_class(position, True, 
            sublime.CLASS_SUB_WORD_START | 
            sublime.CLASS_SUB_WORD_END | 
            sublime.CLASS_PUNCTUATION_START | 
            sublime.CLASS_PUNCTUATION_END | 
            sublime.CLASS_LINE_END | 
            sublime.CLASS_EMPTY_LINE
        )

class WordDemarcation:
    """a category of functions mapping positions to region boundaries,
    effectively providing the definition of a region"""
    def __init__(self, view):
        self.view = view
    def prevbegin(self, position):
        return self.view.find_by_class(position, False, 
            sublime.CLASS_WORD_START #| 
            # sublime.CLASS_WORD_END | 
            # sublime.CLASS_PUNCTUATION_START | 
            # sublime.CLASS_PUNCTUATION_END | 
            # sublime.CLASS_LINE_END | 
            # sublime.CLASS_EMPTY_LINE
        )
    def nextend(self, position):
        return self.view.find_by_class(position, True, 
            # sublime.CLASS_WORD_START | 
            sublime.CLASS_WORD_END #| 
            # sublime.CLASS_PUNCTUATION_START | 
            # sublime.CLASS_PUNCTUATION_END | 
            # sublime.CLASS_LINE_END | 
            # sublime.CLASS_EMPTY_LINE
        )

class ListItemDemarcation:
    """a category of functions mapping positions to region boundaries,
    effectively providing the definition of a region"""
    def __init__(self, view):
        self.view = view
    def prevbegin(self, position):
        regions = list_separator_defs(self.view)
        target = region_b(regions, position) or first(regions)
        return target.begin() 
    def nextend(self, position):
        regions = list_separator_defs(self.view)
        target = region_f(regions, position) or last(regions)
        return target.end()
    
class PredefinedRegionDemarcation:
    """a category of functions mapping positions to boundaries of
    predefined regions, provided in the `regions` parameter."""
    def __init__(self, regions):
        self.regions = regions
    def prevbegin(self, position):
        return (region_b(self.regions, position) or first(self.regions)).begin()
    def nextend(self, position):
        return (region_f(self.regions, position) or last(self.regions)).begin()




# SECTION: FUNCTIONS THAT HELP CREATE PREDEFINED REGION TYPES (FUNCTIONS, CLASSES, ETC.)
def list_func_defs(view):
    lang = source(view)
    if lang in ('cs', 'java', 'cpp'):
        return view.find_by_selector('meta.method.identifier')

    # Sublime doesn't think "function() {}" (mind no space) is a func definition.
    # It however thinks constructor and prototype have something to do with it.
    if lang == 'js':
        # Functions in javascript are often declared in expression manner,
        # we add function binding to prototype or object property as part of declaration.
        func_def = r'([\t ]*(?:\w+ *:|(?:(?:var|let|const) +)?[\w.]+ *=) *)?\bfunction\b'
        raw_funcs = view.find_all(func_def)
        is_junk = lambda r: is_escaped(view, r.a)
        funcs = lremove(is_junk, raw_funcs)
        return funcs + view.find_by_selector('meta.class-method')

    funcs = view.find_by_selector('meta.function')
    if lang == 'python':
        is_junk = lambda r: re_test(r'^(lambda|\s*\@)', view.substr(r))
        funcs = lremove(is_junk, funcs)
    return funcs

def list_class_defs(view):
    lang = source(view)
    if lang in ('cs', 'java'):
        return view.find_by_selector('meta.class.identifier')
    else:
        return view.find_by_selector('meta.class')

def list_defs(view):
    funcs = list_func_defs(view)
    if source(view) == 'js':
        return funcs
    classes = list_class_defs(view)
    return order_regions(funcs + classes)


def list_blocks(view):
    empty_lines = view.find_all(r'^\s*\n')
    return invert_regions(view, empty_lines)


def list_separator_defs(view):
    selectors = [
        # 'punctuation.definition.generic.begin', 'punctuation.definition.generic.end',
        # 'punctuation.section.block',
        # 'punctuation.section.block',
        # 'punctuation.section.braces',
        # 'punctuation.section.group',
        # 'punctuation.section.parens',
        # 'punctuation.section.brackets',
        # 'punctuation.section.parameters',

        'punctuation.section.arguments',
        'punctuation.section.sequence',
        'punctuation.section.target-list',
        'punctuation.section.mapping',
        'punctuation.section.set',

        # 'punctuation.separator.parameters',
        # 'punctuation.separator.sequence',
        # 'punctuation.separator.arguments',
        # 'punctuation.separator.target-list',
        # 'punctuation.separator.mapping',
        # 'punctuation.separator.set',
    ]
    return order_regions(chain(*[view.find_by_selector(selector) for selector in selectors]))
    # return invert_regions(view, order_regions(chain(*[view.find_by_selector(selector) for selector in selectors])))


# SECTION: FUNCTIONS THAT HELP WORK WITH PREDEFINED REGION TYPES (FUNCTIONS, CLASSES, ETC.)
def region_b(regions, pos):
    return first(r for r in reversed(regions) if r.begin() <= pos)

def region_f(regions, pos):
    return first(r for r in regions if pos < r.begin())

def order_regions(regions):
    order = lambda r: (r.begin(), r.end())
    return sorted(regions, key=order)

def invert_regions(view, regions):
    # NOTE: regions should be non-overlapping and ordered,
    #       no check here for performance reasons
    start = 0
    end = view.size()
    result = []

    for r in regions:
        if r.a > start:
            result.append(sublime.Region(start, r.a))
        start = r.b

    if start < end:
        result.append(sublime.Region(start, end))

    return result



