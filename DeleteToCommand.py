import sublime
import sublime_plugin

class DeleteToCommand(sublime_plugin.TextCommand):
    """Delete from each selection anchor to a named text boundary."""

    def run(self, edit, to):
        selections = list(self.view.sel())
        expanded = [sublime.Region(region.a, self._target(region.b, to))
                    for region in selections]

        self.view.sel().clear()
        self.view.sel().add_all(expanded)
        self.view.run_command('left_delete')

    def _target(self, point, to):
        if to == 'bof':
            return 0
        if to == 'eof':
            return self.view.size()
        if to == 'bol':
            return self.view.line(point).begin()
        if to == 'eol':
            return self.view.line(point).end()
        raise ValueError('Unknown delete boundary: {0}'.format(to))


