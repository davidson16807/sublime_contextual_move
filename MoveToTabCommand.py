# -*- coding: utf-8 -*-

"""
Move Tab
Plugin for Sublime Text to move tabs around
Copyright (c) 2012 Frédéric Massart - FMCorz.net
Licensed under The MIT License
Redistributions of files must retain the above copyright notice.
http://github.com/FMCorz/MoveTab
"""

import sublime, sublime_plugin

class MoveToTabCommand(sublime_plugin.WindowCommand):
	def run(self, position):
		view = self.window.active_view()
		(group, index) = self.window.get_view_index(view)
		if index < 0: return
		views = self.window.views_in_group(group)
		self.window.focus_view(views[position])
