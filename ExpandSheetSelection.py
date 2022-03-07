
import sublime, sublime_plugin, re

class ExpandSheetSelectionCommand(sublime_plugin.WindowCommand):
    def run(self, forward=True):
        offset = 1 if forward else -1
        sheet = self.window.active_sheet()
        sheets = self.window.sheets()
        print()
        print(sheets.index(sheet))
        print(len(sheets))
        next_sheet_id = (sheets.index(sheet) + offset) % len(sheets)
        print(next_sheet_id)
        next_sheet = sheets[next_sheet_id]
        selection = self.window.selected_sheets()
        selection.append(next_sheet)
        self.window.select_sheets(selection)
        self.window.focus_sheet(next_sheet)