# The MIT License (MIT)
# Copyright (c) 2014 Jimb Esser

import sublime, sublime_plugin, re


class HistoryToEndCommand(sublime_plugin.WindowCommand):
    def run(self, forward):
    	for i in range(0, 1000):
    		self.window.run_command('redo' if forward else 'undo')
