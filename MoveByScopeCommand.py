# -*- coding: utf-8 -*-

"""
Contents modified from Alexander Schepanovski's Reform plugin, credit goes to him: https://github.com/Suor/sublime-reform
"""

import re
import sublime, sublime_plugin
ST3 = sublime.version() >= '3000'

from functools import partial, reduce
from itertools import takewhile, chain

try:
    from .funcy import *
except ValueError: # HACK: for ST2 compatability
    from funcy import * 

'''
NOTE: Our design goal is to commute the diagram in "CATEGORY.png" using our implementation.
The diagram uses the following notations:
* "P" is a point
* "R" is a region
* "E" is the end of a region
* "B" is the beginning of a region
* "T" is a transposition between regions.
* trivial product morphisms are indicated by dotted lines

This design allows us to define a region type (e.g. word, function, class, etc.) using only two functions:
one function expresses for any position how to get to the very next end of a region  going down,
and the other function expresses for any position how to get to the very next beginning of a region going up.
Both functions are idempotent: feeding output back as input returns the same position (as shown in the diagrams).
Establishing this requirement allows a much cleaner implementation that avoids the introduction of off-by-one errors.
By composing these two functions you can construct the boundaries for any region,  
and combining these functions with character offsets ("prevchar" and "nextchar") lets you find the boundaries of adjacent regions.
Certain types of regions (e.g. functions or classes) may be easier to define by first obtaining a full list of regions,
and these types can be defined using the two aforementioned functions by comparing known region boundaries with current position. 
However this approach is not suitable for region types like words, where there are a large number of regions to consider.
This approach allows us to define both kinds of region types using a single common interface.
'''


class MoveByScopeCommand(sublime_plugin.TextCommand):
    def run(self, edit, forward, by, extend = False, complete = False, delete = False, to_end = False, demarcator=''):
        demarcation_ = demarcation(self.view, by, demarcator)
        if to_end:
            end_position = self.view.size()-1 if forward else 0
            end = sublime.Region(end_position, end_position)
            set_selection(self.view, [movement(RegionMovement(demarcation_), not forward, end)])
        elif extend:
            set_selection(self.view, 
                map(partial(expansion, RegionExpansion(demarcation_), forward, complete), 
                    self.view.sel()))
        elif delete:
            set_selection(self.view, 
                map(partial(expansion, RegionExpansion(demarcation_), forward, complete), 
                    self.view.sel()))
            self.view.run_command('left_delete')
        elif complete:
            set_selection(self.view, 
                map(partial(completion, demarcation_, forward), 
                    self.view.sel()))
        else:
            set_selection(self.view, 
                map(partial(movement, RegionMovement(demarcation_), forward), 
                    self.view.sel()))
    
    
class IndentScopeCommand(sublime_plugin.TextCommand):
    def run(self, edit, forward, by, demarcator=''):
        demarcation_ = demarcation(self.view, by, demarcator)
        set_replacements(self.view, edit,
            map(partial(indentation, RegionTraversal(demarcation_), self.view, forward), 
                self.view.sel()))

class TransposeByScopeCommand(sublime_plugin.TextCommand):
    def run(self, edit, forward, by, demarcator=''):
        demarcation_ = demarcation(self.view, by, demarcator)
        set_replacements(self.view, edit,
            map(partial(transposition, RegionTraversal(demarcation_), self.view, forward), 
                self.view.sel()))

# SECTION: FUNCTIONS WITH SIDE EFFECTS THAT ARE USED TO COMPOSE COMMANDS
def set_selection(view, regions):
    # NOTE: we need to materialize a possible iterator before clearing selection,
    #       as mapping selection is a common techique.
    if iterable(regions):
        regions = list(regions)

    view.sel().clear()
    add_selection(view, regions)
    view.show(view.sel())

def add_selection(view, regions):
    if iterable(regions):
        if ST3:
            view.sel().add_all(list(regions))
        else:
            # .add_all() doesn't work with python lists in ST2
            for region in regions:
                view.sel().add(r)
    else:
        view.sel().add(regions)

def set_replacements(view, edit, replacements):
    replacements = list(replacements) if iterable(replacements) else replacements
    regions = order_regions([replacement.region for replacement in replacements])
    for region1, region2 in zip(regions, regions[1:]):
        if region1.intersects(region2): return # do nothing if replacements step over each other
    selections = []
    offset = 0
    for replacement in replacements:
        view.replace(edit, offset_region(replacement.region, offset), replacement.text)
        selections.append(offset_region(replacement.selection, offset))
        offset += len(replacement.text) - replacement.region.size()
    set_selection(view, selections)

# SECTION: PURE FUNCTIONS THAT ARE USED TO MAP SELECTIONS
def movement(movement, forward, current):
    if forward: return movement.next(current)
    else: return movement.prev(current)

def completion(demarcation, forward, current):
    if forward: return sublime.Region(demarcation.prevbegin(current.begin()), demarcation.nextend(current.end())) 
    else: return sublime.Region(demarcation.nextend(current.end()), demarcation.prevbegin(current.end()))

def expansion(expansion_, forward, complete, current):
    if current.size() < 1 and complete: return completion(expansion_.demarcation, forward, current)
    else: return expansion_.next(current) if forward else expansion_.prev(current)
    
def indentation(traversal, view, forward, current):
    settings = view.settings()
    tab_size = settings.get('tab_size', 4)
    translate_tabs_to_spaces = settings.get('translate_tabs_to_spaces', False)
    canonical_tab = (' ' * tab_size) if translate_tabs_to_spaces else '\t'
    tab_regex = re.compile('^(\t|'+(' ' * tab_size)+')')
    target = current
    replacement = ''
    offset = 0
    region = completion(traversal.demarcation, True, current)
    lines = view.lines(region)
    previous = sublime.Region(lines[0].begin(), lines[0].begin()) if lines else None
    for line in lines: 
        target = target.cover(line)
        inbetween = sublime.Region(previous.end(), line.begin())
        line_text = view.substr(line)
        line_replacement = (canonical_tab + line_text) if forward else tab_regex.sub('', line_text)
        if line.begin() < current.begin(): offset += len(line_replacement) - len(line_text)
        replacement += view.substr(inbetween) + line_replacement
        previous = line
    return Replacement(target, replacement, offset_region(current, offset))

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
        offset = -destination.size() - inbetween.size()
    if source.intersects(destination):
        return Replacement(source, top, current)
    else:
        return Replacement(source.cover(destination), bottom+middle+top, offset_region(current, offset))

# SECTION: MISCELLANEOUS FUNCTIONS AND STRUCTURES THAT ARE USED TO COMPOSE COMMANDS
def demarcation(view, type, demarcator=''):
    language = source(view)
    functions = {
        'python': lambda: PythonScopeDemarcation(view, 
                [declaration
                    for declaration in view.find_by_selector('meta.function')
                    if not re_test(r'^(lambda|\s*\@)', view.substr(declaration))]
            ),
        'c++': lambda: CLikeScopeDemarcation(
                view.size(),
                chain(view.find_by_selector('meta.method'), view.find_by_selector('meta.function')),
                view.find_by_selector('punctuation.section.block.end'),
                chain(
                    view.find_by_selector('meta.template'), 
                    view.find_by_selector('punctuation.definition.comment'),
                    view.find_by_selector('storage.type'),
                    view.find_by_selector('storage.modifier')
                )
            ),
        'c': lambda: CLikeScopeDemarcation(
                view.size(),
                view.find_by_selector('meta.function'),
                view.find_by_selector('punctuation.section.block.end'),
                chain(
                    view.find_by_selector('punctuation.definition.comment'),
                    view.find_by_selector('storage.type'),
                    view.find_by_selector('storage.modifier')
                )
            ),
        'js': lambda: CLikeScopeDemarcation(
                view.size(),
                [beginning
                    for beginning in chain(
                        view.find_all(r'([\t ]*(?:\w+ *:|(?:(?:var|let|const) +)?[\w.]+ *=) *)?\bfunction\b'), 
                        view.find_by_selector('meta.class-method'))
                    if not is_escaped(view, beginning.a)],
                view.find_by_selector('punctuation.section.block.end'),
                view.find_by_selector('punctuation.definition.comment')
            ),
        'r': lambda: CLikeScopeDemarcation(
                view.size(),
                [beginning
                    for beginning in view.find_all(r'([\t ]*(?:\w+ *:|(?: +)?[\w.]+ *=) *)?\bfunction\b')
                    if not is_escaped(view, beginning.a)],
                view.find_by_selector('punctuation.section.braces.end'),
                view.find_by_selector('punctuation.definition.comment')
            ),
        'java': lambda: CLikeScopeDemarcation(
                view.size(),
                chain(view.find_by_selector('meta.method'), view.find_by_selector('meta.function')),
                view.find_by_selector('punctuation.section.block.end'),
                chain(
                    view.find_by_selector('punctuation.definition.comment'),
                    view.find_by_selector('storage.type'),
                    view.find_by_selector('storage.modifier')
                )
            ),
        'cs': lambda: CLikeScopeDemarcation(
                view.size(),
                chain(view.find_by_selector('meta.method'), view.find_by_selector('meta.function')),
                view.find_by_selector('punctuation.section.block.end'),
                chain(
                    view.find_by_selector('punctuation.definition.comment'),
                    view.find_by_selector('storage.type'),
                    view.find_by_selector('storage.modifier')
                )
            ),
        'clike': lambda: CLikeScopeDemarcation(
                view.size(),
                chain(view.find_by_selector('meta.method'), view.find_by_selector('meta.function')),
                chain(view.find_by_selector('punctuation.section.block.end'), view.find_by_selector('punctuation.section.braces.end')),
                chain(
                    view.find_by_selector('punctuation.definition.comment'),
                    view.find_by_selector('storage.type'),
                    view.find_by_selector('storage.modifier')
                )
            ),
        'fortran': lambda: CLikeScopeDemarcation(
                view.size(),
                view.find_all(r'\bsubroutine\b'),
                view.find_all(r'\bend subroutine\b'),
                view.find_by_selector('punctuation.definition.comment')
            ),
    }
    classes = {
        'python': lambda: PythonScopeDemarcation(view, view.find_by_selector('meta.class')), 
        'c++': lambda: CLikeScopeDemarcation(
                view.size(),
                chain(
                    view.find_by_selector('meta.class'), 
                    view.find_by_selector('meta.struct'), 
                    view.find_by_selector('meta.enum')
                ),
                view.find_by_selector('punctuation.section.block.end'),
                chain(
                    view.find_by_selector('meta.template'), 
                    view.find_by_selector('punctuation.definition.comment')
                )
            ),
        'clike': lambda: CLikeScopeDemarcation(
                view.size(),
                chain(
                    view.find_by_selector('meta.class'), 
                    view.find_by_selector('meta.class.identifier'), 
                    view.find_by_selector('meta.struct'), 
                    view.find_by_selector('meta.enum')
                ),
                view.find_by_selector('punctuation.section.block.end'),
                chain(
                    view.find_by_selector('punctuation.definition.comment'),
                    view.find_by_selector('storage.modifier')
                )
            ),
        'fortran': lambda: CLikeScopeDemarcation(
                view.size(),
                view.find_all(r'\bmodule\b'),
                view.find_all(r'\bend module\b'),
                view.find_by_selector('punctuation.definition.comment')
            ),
    }
    return {
        'subwords': lambda: SubWordDemarcation(view),
        'words': lambda: WordDemarcation(view),
        'empty_lines': lambda: EmptyLineDemarcation(view),
        'tabulations': lambda: CustomDemarcation(view, r'\t'),
        'parentheses': lambda: CustomDemarcation(view, r'[\\(\\)]'),
        'brackets': lambda: CustomDemarcation(view, r'\\[|\\]'),
        'braces': lambda: CustomDemarcation(view, r'[{}]'),
        'listitems': lambda: ListItemDemarcation(view),
        'conditionals': lambda: ListItemDemarcation(view),
        'functions': lambda: functions[language]() if language in functions else functions['clike'](),
        'classes': lambda: classes[language]() if language in classes else classes['clike'](),
    }[type]()

class Replacement:
    def __init__(self, region, text, selection): 
        self.region = region
        self.text = text
        self.selection = selection

# SECTION: CATEGORIES THAT OPERATE ON GENERIC REGION DEMARCATIONS
class RegionExpansion:
    """A category of functions. Given a region, these functions return new regions 
    with same starting point but different ending point.
    The ending point of the return value is the ending position of a region.
    Given a category for region demarcation, a region traversal category exists. 
    These required categories are defined later in the document"""
    def __init__(self, region_demarcation):
        self.demarcation = region_demarcation
    def prev(self, region):
        a = region.a
        b1 = region.b
        b2 = self.demarcation.prevbegin(region.b-1)
        return sublime.Region(a , b2) if not (b2 < a and a < b1) else sublime.Region(a, a)
    def next(self, region):
        a = region.a
        b1 = region.b
        b2 = self.demarcation.nextend(region.b+1)
        return sublime.Region(a, b2) if not (b1 < a and a < b2) else sublime.Region(a, a)

# SECTION: CATEGORIES THAT OPERATE ON GENERIC REGION DEMARCATIONS
class RegionMovement:
    """A category of functions that either advance forward to region ends, 
    or behind to region beginnings.
    Given a category for region demarcation, a region traversal category exists. 
    These required categories are defined later in the document"""
    def __init__(self, region_demarcation):
        self.demarcation = region_demarcation
    def prev(self, selection):
        return self.demarcation.prevbegin(selection.begin()-1) if selection.size() < 1 else selection.begin()
    def next(self, selection):
        return self.demarcation.nextend(selection.end()+1) if selection.size() < 1 else selection.end()

class RegionTraversal:
    """A category of functions iterating through regions.
    Given a category for region demarcation, a region traversal category exists. 
    These required categories are defined later in the document"""
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
        self.view = view
    def prevbegin(self, position):
        return self.view.find_by_class(position, False, 
            sublime.CLASS_SUB_WORD_START  
            | sublime.CLASS_SUB_WORD_END 
            | sublime.CLASS_WORD_START  
            | sublime.CLASS_WORD_END  
            | sublime.CLASS_PUNCTUATION_START  
            | sublime.CLASS_PUNCTUATION_END  
            | sublime.CLASS_LINE_START  
            | sublime.CLASS_LINE_END  
            | sublime.CLASS_EMPTY_LINE
        )
    def nextend(self, position):
        return self.view.find_by_class(position, True, 
            sublime.CLASS_SUB_WORD_START  
            | sublime.CLASS_SUB_WORD_END  
            | sublime.CLASS_WORD_START  
            | sublime.CLASS_WORD_END  
            | sublime.CLASS_PUNCTUATION_START  
            | sublime.CLASS_PUNCTUATION_END  
            | sublime.CLASS_LINE_START  
            | sublime.CLASS_LINE_END  
            | sublime.CLASS_EMPTY_LINE
        )

class WordDemarcation:
    """a category of functions mapping positions to region boundaries,
    effectively providing the definition of a region"""
    def __init__(self, view):
        self.view = view
    def prevbegin(self, position):
        return self.view.find_by_class(position, False, 
            sublime.CLASS_WORD_START
            | sublime.CLASS_WORD_END 
            | sublime.CLASS_PUNCTUATION_START 
            | sublime.CLASS_PUNCTUATION_END 
            # | sublime.CLASS_EMPTY_LINE
            # | sublime.CLASS_LINE_START
            # | sublime.CLASS_LINE_END
        )
    def nextend(self, position):
        return self.view.find_by_class(position, True, 
            sublime.CLASS_WORD_START
            | sublime.CLASS_WORD_END
            | sublime.CLASS_PUNCTUATION_START 
            | sublime.CLASS_PUNCTUATION_END 
            # | sublime.CLASS_EMPTY_LINE
            # | sublime.CLASS_LINE_START
            # | sublime.CLASS_LINE_END
        )

class EmptyLineDemarcation:
    """a category of functions mapping positions to region boundaries,
    effectively providing the definition of a region"""
    def __init__(self, view):
        self.view = view
    def prevbegin(self, position):
        return self.view.find_by_class(position, False, 
            sublime.CLASS_EMPTY_LINE
            # | sublime.CLASS_LINE_START
            # | sublime.CLASS_LINE_END
        )
    def nextend(self, position):
        return self.view.find_by_class(position, True, 
            sublime.CLASS_EMPTY_LINE
            # | sublime.CLASS_LINE_START
            # | sublime.CLASS_LINE_END
        )

class CustomDemarcation:
    """a category of functions mapping positions to region boundaries,
    effectively providing the definition of a region"""
    def __init__(self, view, demarcator):
        self.view = view
        self.demarcator = demarcator
    def prevbegin(self, position):
        return max([delimiter.end()
            for delimiter in self.view.find_all(self.demarcator)
            if delimiter.end() <= position
            # NOTE: the line below can be used to match complex list items with parens and bracks, 
            # but results do not feel very predictable to the user
            # and braces_match(self.view.substr(sublime.Region(position, delimiter.begin())))
        ] or [position])
    def nextend(self, position):
        return min([delimiter.begin()
            for delimiter in self.view.find_all(self.demarcator)
            if position <= delimiter.begin()
            # NOTE: the line below can be used to match complex list items with parens and bracks, 
            # but results do not feel very predictable to the user
            # and braces_match(self.view.substr(sublime.Region(position, delimiter.begin())))
        ] or [position])

class ListItemDemarcation:
    """a category of functions mapping positions to region boundaries,
    effectively providing the definition of a region"""
    def __init__(self, view):
        self.view = view
    def prevbegin(self, position):
        return max([delimiter.end()
            for delimiter in self.view.find_all(r'[,([{]\s*')
            if delimiter.end() <= position
            # NOTE: the line below can be used to match complex list items with parens and bracks, 
            # but results do not feel very predictable to the user
            # and braces_match(self.view.substr(sublime.Region(position, delimiter.begin())))
        ] or [position])
    def nextend(self, position):
        return min([delimiter.begin()
            for delimiter in self.view.find_all(r'[,)}]')
            if position <= delimiter.begin()
            # NOTE: the line below can be used to match complex list items with parens and bracks, 
            # but results do not feel very predictable to the user
            # and braces_match(self.view.substr(sublime.Region(position, delimiter.begin())))
        ] or [position])

class CLikeScopeDemarcation:
    """a category of functions mapping positions to boundaries for functions within c-like langauges,
    effectively providing the definition for functions within these languages.
    Starting boundaries include "predeclarations" such as comments and template constructs, 
    which may be customized by the user."""
    def __init__(self, view_size, declarations, braces, predeclarations):

        self.declaration_beginnings = list(declaration.begin() for declaration in declarations)
        self.brace_endings = list(brace.end() for brace in braces)
        self.predeclaration_beginnings = list(predeclaration.begin() for predeclaration in predeclarations)
        self.view_size = view_size
    def nextend(self, position):
        braces = [ending 
            for ending in self.brace_endings
            if position <= ending]
        nearest_valid_beginning = min([beginning 
            for beginning in self.declaration_beginnings
            if position < beginning
            and [brace for brace in braces if brace < beginning]] 
            or [self.view_size-1])
        return max([brace 
            for brace in braces 
            if brace < nearest_valid_beginning] or [position])
    def prevbegin(self, position):
        declaration = max([declaration 
            for declaration in self.declaration_beginnings
            if declaration <= position] 
            or [min(self.declaration_beginnings or [position])])
        previous_brace = max([ending
            for ending in self.brace_endings
            if ending < declaration] or [0])
        predeclaration = min([predeclaration 
            for predeclaration in self.predeclaration_beginnings
            if previous_brace < predeclaration and predeclaration <= position] or [declaration]) 
        return min([predeclaration, declaration])

class PythonScopeDemarcation:
    def __init__(self, view, declarations):
        self.view = view
        self.declaration_beginnings = list(declaration.begin() for declaration in declarations)
    def prevbegin(self, position):
        view = self.view
        return max([declaration 
            for declaration in self.declaration_beginnings
            if declaration <= position]
            or [min(self.declaration_beginnings or [position])])
    def nextend(self, position):
        view = self.view
        tab_size = view.settings().get('tab_size', 4)
        def indent_length(line_region):
            line_text = view.substr(line_region)
            indentation = re.search(r'^\s*', line_text).group() or ''
            indent_length_ = indentation.count('\t')*tab_size + indentation.count(' ')
            return indent_length_
        endings = [
            max([line.end()
                 for line in view.lines(sublime.Region(position, declaration))
                 if  indent_length(view.line(declaration)) < indent_length(line)]
                 or [view.size() -1])
            for declaration in chain(self.declaration_beginnings, [view.size()-1])
            if position < declaration
        ]
        return min([ending
            for ending in endings
            if position < ending])




# SECTION: FUNCTIONS THAT HELP WORK WITH PREDEFINED REGION TYPES (FUNCTIONS, CLASSES, ETC.)
def offset_region(region, offset):
    return sublime.Region(region.a + offset, region.b + offset)

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


def cursor_pos(view):
    return view.sel()[0].b

### Scope
def scope_name(view, pos=None):
    if pos is None:
        pos = cursor_pos(view)
    return view.scope_name(pos)

def parsed_scope(view, pos=None):
    return parse_scope(scope_name(view, pos))

def source(view, pos=None):
    return first(vec[1] for vec in parsed_scope(view, pos) if vec[0] == 'source')

def parse_scope(scope_name):
    return [name.split('.') for name in scope_name.split()]

def is_escaped(view, pos):
    return any(s[0] in ('comment', 'string') for s in parsed_scope(view, pos))

def braces_match(text):
    return text.count('(') == text.count(')') and text.count('[') == text.count(']') and text.count('{') == text.count('}')