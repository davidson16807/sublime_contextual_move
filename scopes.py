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
    def run(self, edit, forward, expand = False, complete = False, delete = False):
        regions = list_defs(self.view) or list_blocks(self.view)
        # if complete:
        #    map_selection(self.view, partial(complete_if_empty, partial(smart_up, regions), partial(smart_up, regions)))
        if expand or delete:
            up = partial(smart_up, regions)
            down = partial(smart_down, regions)
            map_selection(self.view, partial(complete_or_expand, up, down, forward))
        else:
            map_selection(self.view, partial(smart_down if forward else smart_up, regions))
        if delete:
            self.view.run_command('left_delete')

class TransposeByCommand(sublime_plugin.TextCommand):
    def run(self, edit, forward, by):
        if by == 'functions':
            regions = list_defs(self.view) or list_blocks(self.view)
            up = partial(smart_up_transpose, regions)
            down = partial(smart_down_transpose, regions)
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
    for source in old_selections:
        if forward:  
            destination = sublime.Region(source.end(), down(source))
            top = view.substr(source) 
            bottom = view.substr(destination)
            offset = destination.size()
        else:
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
        # sublime.CLASS_LINE_START | 
        sublime.CLASS_LINE_END | 
        sublime.CLASS_EMPTY_LINE
    )

def sub_word_down(view, current):
    return view.find_by_class(current.end(), True, 
        sublime.CLASS_SUB_WORD_START | 
        sublime.CLASS_SUB_WORD_END | 
        sublime.CLASS_PUNCTUATION_START | 
        sublime.CLASS_PUNCTUATION_END | 
        # sublime.CLASS_LINE_START | 
        sublime.CLASS_LINE_END | 
        sublime.CLASS_EMPTY_LINE
    )

def word_up(view, current):
    return view.find_by_class(current.begin(), False, 
        sublime.CLASS_WORD_START | 
        sublime.CLASS_WORD_END | 
        sublime.CLASS_PUNCTUATION_START | 
        sublime.CLASS_PUNCTUATION_END | 
        # sublime.CLASS_LINE_START | 
        sublime.CLASS_LINE_END | 
        sublime.CLASS_EMPTY_LINE
    )

def word_down(view, current):
    return view.find_by_class(current.end(), True, 
        sublime.CLASS_WORD_START | 
        sublime.CLASS_WORD_END | 
        sublime.CLASS_PUNCTUATION_START | 
        sublime.CLASS_PUNCTUATION_END | 
        # sublime.CLASS_LINE_START | 
        sublime.CLASS_LINE_END | 
        sublime.CLASS_EMPTY_LINE
    )

def current_start(current):
    return current.a

def current_stop(current):
    return current.b

def smart_up_transpose(regions, current):
    target = region_b(regions, current.begin()-1) or first(regions)
    return target.begin()

def smart_down_transpose(regions, current):
    target = region_f(regions, current.end()) or last(regions)
    return target.begin()

def smart_up(regions, current):
    target = region_b(regions, current.b - 1) or first(regions)
    return target.begin() 

def smart_down(regions, current):
    target = region_f(regions, current.b + 1) or last(regions)
    return target.begin()

def complete_if_empty(up, down, current):
    return sublime.Region(up(current), down(current)) if current.size() < 1 else current

def complete_or_expand(up, down, forward, current):
    if current.size() < 1:
        return sublime.Region(up(current), down(current)) if forward else sublime.Region(down(current), up(current))
    else:
        return sublime.Region(current.a, down(current) if forward else up(current))


def get_words(view, region):
    word = view.substr(region)
    words = view.find_all(r'\b%s\b' % word)

    # filter out words in strings and comments
    allow_escaped = any(is_escaped(view, r.begin()) for r in view.sel())
    if not allow_escaped:
        words = [w for w in words if not is_escaped(view, w.a)]

    return words 



def smart_region_up(view, region):
    comments_block = comments_block_at(view, region.b)
    block = smart_block_at(view, region.begin())
    scope = scope_up(view, region)

    if comments_block and not region.contains(comments_block):
        return comments_block
    elif block and not region.contains(block) and (not scope or scope.a < block.a):
        return block
    else:
        return scope or region

def comments_block_at(view, pos):
    def grab_empty_line_start(region):
        line_start = view.line(region).a
        space = view.find(r'[ \t]+', line_start)
        if space and space.b == region.a:
            return region.cover(space)
        else:
            return region

    clines = list(map(grab_empty_line_start, view.find_by_selector('comment')))

    pos = cursor_pos(view)
    this_line = first((i, r) for i, r in enumerate(clines) if r.contains(pos) and r.b != pos)
    if this_line:
        i, block = this_line
        for r in clines[i+1:]:
            if r.a == block.b:
                block = block.cover(r)
            else:
                break
        for r in reversed(clines[:i]):
            if r.b == block.a:
                block = block.cover(r)
            else:
                break
        return block


def smart_block_at(view, pos):
    lang = source(view)
    block = block_at(view, pos)

    # Close non-pairing curlies
    curlies = count_curlies(view, block)
    if curlies > 0:
        curly = find_closing_curly(view, block.end(), count=curlies)
        if curly is not None:
            return block.cover(view.full_line(curly))
    elif curlies < 0:
        curly = find_opening_curly(view, block.begin(), count=curlies)
        if curly is not None:
            return block.cover(view.full_line(curly))
    return block


def list_func_defs(view):
    lang = source(view)
    if lang in ('cs', 'java'):
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


def scope_up(view, region):
    scopes = list(scopes_up(view, region.end()))
    expansion = first(s for s in scopes if s != region and s.contains(region))
    if expansion:
        return expansion
    if region.empty():
        return first(scopes)

def scope_at(view, pos):
    scopes = scopes_up(view, pos)
    return first(s for s in scopes if s.contains(pos))

def scopes_up(view, pos):
    for scope, upper in with_next(_scopes_up(view, pos)):
        yield scope
        if upper and not upper.contains(scope):
            continue

def _scopes_up(view, pos):
    scopes = [_expand_def(view, adef) for adef in list_defs(view)]

    scope = region_b(scopes, pos)
    while scope:
        yield scope
        scope = region_b(scopes, scope.begin() - 1)


def _expand_def(view, adef):
    lang = source(view, adef.begin())

    if lang == 'python':
        next_line = newline_f(view, adef.end())
        adef = adef.cover(view.indented_region(next_line))
        prefix = re_find(r'^[ \t]*', view.substr(view.line(adef.begin())))
        while True:
            p = line_b_begin(view, adef.begin())
            if p is None:
                break
            line_b_str = view.substr(view.line(p))
            if line_b_str.startswith(prefix) and re_test(r'meta.(annotation|\w+.decorator)',
                    scope_name(view, p + len(prefix))):
                adef = adef.cover(sublime.Region(p, p))
            else:
                break
        return adef
    elif lang in ('js', 'cs', 'java'):
        # Extend to matching bracket
        start_bracket = view.find(r'{', adef.end(), sublime.LITERAL)
        end_bracket = find_closing_curly(view, start_bracket.b)
        adef = adef.cover(view.full_line(end_bracket))

        # Match , or ; in case it's an expression
        if lang == 'js':
            punct = view.find(r'\s*[,;]', adef.end())
            if punct and punct.a == adef.b:
                adef = adef.cover(punct)
        else:
            adef = adef.cover(view.line(adef.begin()))

        return adef
    else:
        # Heuristics based on indentation for all other languages
        next_line = newline_f(view, adef.end())
        indented = view.indented_region(next_line)
        last_line = view.line(indented.end())
        return adef.cover(last_line)
