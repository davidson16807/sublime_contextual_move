import sublime
import sublime_plugin

class MoveLinesToEndCommand(sublime_plugin.TextCommand):
    """Move the selected lines to the beginning or end of the buffer."""

    def run(self, edit, forward):
        if not self.view.sel():
            return

        first_row = min(self._row_bounds(region)[0] for region in self.view.sel())
        last_row = max(self._row_bounds(region)[1] for region in self.view.sel())
        last_buffer_point = max(0, self.view.size() - 1)
        buffer_last_row = self.view.rowcol(last_buffer_point)[0]
        count = buffer_last_row - last_row if forward else first_row
        command = 'swap_line_down' if forward else 'swap_line_up'

        for unused in range(max(0, count)):
            self.view.run_command(command)

    def _row_bounds(self, region):
        begin_row = self.view.rowcol(region.begin())[0]
        end_point = region.end()
        if (not region.empty() and end_point > 0 and
                self.view.line(end_point).begin() == end_point):
            end_point -= 1
        return begin_row, self.view.rowcol(end_point)[0]

