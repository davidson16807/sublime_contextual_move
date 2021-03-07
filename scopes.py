import sublime, sublime_plugin
ST3 = sublime.version() >= '3000'

from functools import partial, reduce
from itertools import takewhile

try:
    from .funcy import *
    from .viewtools import *
except ValueError: # HACK: for ST2 compatability
    from funcy import * 
    from viewtools import *

class MoveByFunctionCommand(sublime_plugin.TextCommand):
    def run(self, edit, forward, expand = False, complete = False, delete = False, by='functions'):
        regions = (list_defs(self.view) if by == 'functions' else list_class_defs(self.view)) or list_blocks(self.view)
        up = partial(smart_up, regions)
        down = partial(smart_down, regions)
        if complete and (expand or delete):
            map_selection(self.view, partial(complete_or_expand, up, down, forward))
        elif complete:
            map_selection(self.view, partial(complete_if_empty, up, down))
        elif expand or delete:
            map_selection(self.view, partial(just_expand, up, down, forward))
        else:
            map_selection(self.view, down if forward else up)
        if delete:
            self.view.run_command('left_delete')

class TransposeByCommand(sublime_plugin.TextCommand):
    def run(self, edit, forward, by):
        if by == 'functions':
            regions = list_defs(self.view) or list_blocks(self.view)
            up = partial(smart_up, regions)
            down = partial(smart_down, regions)
        elif by == 'classes':
            regions = list_class_defs(self.view) or list_blocks(self.view)
            up = partial(smart_up, regions)
            down = partial(smart_down, regions)
        else:
            up = {
                'characters': partial(char_up, self.view),
                'subwords': partial(sub_word_up, self.view),
                'words': partial(word_up, self.view),
            }[by]
            down = {
                'characters': partial(char_down, self.view),
                'subwords': partial(sub_word_down, self.view),
                'words': partial(word_down, self.view),
            }[by]
        map_selection(self.view, partial(complete_if_empty, up, down))
        transpose_selection(self.view, edit, forward, up, down)

def transpose_selection(view, edit, forward, up, down):
    old_selections = view.sel()
    replacements = []
    for selection in old_selections:
        if forward:  
            source = sublime.Region(selection.begin(), selection.end())
            destination = sublime.Region(source.end(), down(source))
            top = view.substr(source) 
            bottom = view.substr(destination)
            offset = destination.size()
        else:
            source = sublime.Region(selection.end(), selection.begin())
            destination = sublime.Region(source.begin(), up(source)) 
            top = view.substr(destination) 
            bottom = view.substr(source)
            offset = -destination.size()
        replacements.append((source.cover(destination), bottom+top, sublime.Region(source.a + offset, source.b + offset)))
    view.sel().clear()
    for region, text, selection in replacements:
        view.replace(edit, region, text)
    view.sel().add_all([selection for region, text, selection in replacements])
    view.show(view.sel())

def char_up(view, current):
    return current.begin()-1

def char_down(view, current):
    return current.end()+1

def sub_word_up(view, current):
    return view.find_by_class(current.begin()-1, False, 
        sublime.CLASS_SUB_WORD_START | 
        sublime.CLASS_SUB_WORD_END | 
        sublime.CLASS_PUNCTUATION_START | 
        sublime.CLASS_PUNCTUATION_END | 
        sublime.CLASS_LINE_END | 
        sublime.CLASS_EMPTY_LINE
    )

def sub_word_down(view, current):
    return view.find_by_class(current.end(), True, 
        sublime.CLASS_SUB_WORD_START | 
        sublime.CLASS_SUB_WORD_END | 
        sublime.CLASS_PUNCTUATION_START | 
        sublime.CLASS_PUNCTUATION_END | 
        sublime.CLASS_LINE_END | 
        sublime.CLASS_EMPTY_LINE
    )

def word_up(view, current):
    return view.find_by_class(current.begin(), False, 
        sublime.CLASS_WORD_START | 
        sublime.CLASS_WORD_END | 
        sublime.CLASS_PUNCTUATION_START | 
        sublime.CLASS_PUNCTUATION_END | 
        sublime.CLASS_LINE_END | 
        sublime.CLASS_EMPTY_LINE
    )

def word_down(view, current):
    return view.find_by_class(current.end(), True, 
        sublime.CLASS_WORD_START | 
        sublime.CLASS_WORD_END | 
        sublime.CLASS_PUNCTUATION_START | 
        sublime.CLASS_PUNCTUATION_END | 
        sublime.CLASS_LINE_END | 
        sublime.CLASS_EMPTY_LINE
    )

def smart_up(regions, current):
    target = region_b(regions, current.b - 1) or first(regions)
    return target.begin() 

def smart_down(regions, current):
    target = region_f(regions, current.b + 1) or last(regions)
    return target.begin()

def just_expand(up, down, forward, current):
    return sublime.Region(current.a, down(current) if forward else up(current))

def complete_if_empty(up, down, current):
    return sublime.Region(up(current), down(current)) if current.size() < 1 else current

def complete_or_expand(up, down, forward, current):
    if current.size() < 1:
        return sublime.Region(up(current), down(current)) if forward else sublime.Region(down(current), up(current))
    else:
        return just_expand(up, down, forward, current)





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


