# The MIT License (MIT)
# Copyright (c) 2014 Jimb Esser

import sublime, sublime_plugin, re


class FindExtremumCommand(sublime_plugin.WindowCommand):
    def run(self, forward):
        self.window.run_command("move_to", {"to": "eof" if forward else 'bof', "extend": False})
        self.window.run_command('find_next' if not forward else 'find_prev')
