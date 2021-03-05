import sublime, sublime_plugin, datetime

class SetMoveContextCommand(sublime_plugin.WindowCommand):
	def run(self, value, command=None, args={}):
		settings = self.window.settings();
		context = settings.get('move_context')
		settings.set('move_context', value)
		if command:	self.window.run_command(command, args)
		# print(context)
		sublime.status_message('Context: ' + context.upper())

class DoOnceMoveContextCommand(sublime_plugin.WindowCommand):
	def run(self, value):
		settings = self.window.settings();
		settings.set('move_context', value)
		settings.set('move_context_do_once', value)

class ExtremumMoveContextCommand(sublime_plugin.WindowCommand):
	def run(self):
		settings = self.window.settings();
		settings.set('move_context_extremum', True)

class ContextualMoveCommand(sublime_plugin.WindowCommand):
	def run(self, **commands):
		settings = self.window.settings();
		context = settings.get('move_context');
		do_once = settings.get('move_context_do_once')
		extremum = settings.get('move_context_extremum')

		context = context if context else 'default'
		if extremum:
			context = context+'_extremum' if context+'_extremum' in commands else 'default_extremum'
		else:
			context = context if context in commands else 'default'
		print(context)
		
		if context in commands:
			command = commands[context]
			args = command['args'] if 'args' in command else {}
			self.window.run_command(command['command'], args)
			print(command)

		if extremum:
			settings.set('move_context_extremum', False)
			# settings.set('move_context', 'default')
