
import sublime, sublime_plugin, re

class CloseRightCommand(sublime_plugin.WindowCommand):
    def run(self):
    	self.window.run_command('close')
    	self.window.run_command('next_view')
