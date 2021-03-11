# The MIT License (MIT)
# Copyright (c) 2014 Jimb Esser

import sublime, sublime_plugin, re


class FindToEndCommand(sublime_plugin.WindowCommand):
    def run(self, forward):
    	for i in range(0, 1000):
    		self.window.run_command('find_next' if forward else 'find_prev')
