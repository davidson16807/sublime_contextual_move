"""
A collection of tools to deal with scopes and text in sublime view.
"""
import sublime
ST3 = sublime.version() >= '3000'

try:
    from .funcy import *
except ValueError: # HACK: for ST2 compatability
    from funcy import *


### Cursor and selection

def cursor_pos(view):
    return view.sel()[0].b

### Lines

def line_at(view, pos):
    return view.line(pos)

def line_start(view, pos):
    line = view.line(pos)
    return sublime.Region(line.begin(), pos)

def line_end(view, pos):
    line = view.line(pos)
    return sublime.Region(pos, line.end())

def list_lines_b(view, pos):
    while pos:
        yield view.full_line(pos)
        pos = view.find_by_class(pos, False, sublime.CLASS_LINE_END)

def list_lines_f(view, pos):
    while pos < view.size():
        yield view.full_line(pos)
        pos = view.find_by_class(pos, True, sublime.CLASS_LINE_START)

if ST3:
    def line_b_begin(view, pos):
        if view.classify(pos) & sublime.CLASS_LINE_START:
            return newline_b(view, pos)
        else:
            return newline_b(view, newline_b(view, pos))

    def newline_b(view, pos):
        if pos > 0:
            return view.find_by_class(pos, False, sublime.CLASS_LINE_START)

    def newline_f(view, pos):
        if pos < view.size():
            return view.find_by_class(pos, True, sublime.CLASS_LINE_START)
else:
    def line_b_begin(view, pos):
        line_start = view.line(pos).begin()
        return newline_b(view, min(pos, line_start))

    def newline_b(view, pos):
        if pos > 0:
            return view.line(pos - 1).begin()

    def newline_f(view, pos):
        if pos < view.size():
            region = view.find(r'^', pos + 1)
            return region.end()

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
