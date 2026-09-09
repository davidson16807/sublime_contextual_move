"""Use Sublime's Find panel query and flags for directional selection."""

import sublime_plugin


class ContextualFindCommand(sublime_plugin.WindowCommand):
    def run(self, forward, extend=False):
        view = self.window.active_view()
        if view is None:
            return
        saved = list(view.sel()) if extend else []
        # Do not use find_under*: those commands derive a query from selected
        # text and can disagree with the pattern and flags in the Find panel.
        if not extend or not saved:
            self.window.run_command('find_next' if forward else 'find_prev')
            self._search = None
            return

        signature = tuple((region.a, region.b) for region in saved)
        previous = getattr(self, '_search', None)
        if (previous and previous['view'] == view.id()
                and previous['change_count'] == view.change_count()
                and previous['selection'] == signature):
            anchor = previous['anchor']
        else:
            anchor = saved[-1] if forward else saved[0]
        # Search from the last match, including after wrapping or changing
        # direction. Stop at the next unselected match or after one full cycle.
        seen = set()
        try:
            while True:
                view.sel().clear()
                view.sel().add(anchor)
                self.window.run_command('find_next' if forward else 'find_prev')
                matches = list(view.sel())
                if not matches:
                    break
                anchor = matches[-1] if forward else matches[0]
                position = (anchor.a, anchor.b)
                if position in seen:
                    break
                seen.add(position)
                if not any(region.contains(anchor) for region in saved):
                    saved.append(anchor)
                    break
        finally:
            view.sel().clear()
            for region in saved:
                view.sel().add(region)
        self._search = {
            'view': view.id(), 'change_count': view.change_count(),
            'selection': tuple((region.a, region.b) for region in view.sel()),
            'anchor': anchor,
        }
        view.show(anchor)
