
import sublime, sublime_plugin, re

class ExpandSheetSelectionCommand(sublime_plugin.WindowCommand):
    def run(self, forward=True):
        offset = 1 if forward else -1
        active_sheet = self.window.active_sheet()
        all_sheets = self.window.sheets()
        new_sheet_id = (all_sheets.index(active_sheet) + offset) % len(all_sheets)
        new_sheet = all_sheets[new_sheet_id]
        selected_sheets = self.window.selected_sheets()
        if new_sheet not in selected_sheets:
            selected_sheets.append(new_sheet)
            self.window.select_sheets(selected_sheets)
            self.window.focus_sheet(new_sheet)
        else:
            selected_sheets.remove(active_sheet)
            self.window.select_sheets(selected_sheets)
            self.window.focus_sheet(new_sheet)
