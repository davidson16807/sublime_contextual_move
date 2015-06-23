import sublime, sublime_plugin, datetime

class ToggleMoveContextCommand(sublime_plugin.WindowCommand):
	def run(self, value = None):
		settings = self.window.settings();
		context = settings.get('move_context')
		if value:
			if context != value:
				context = value
			else:
				context = 'default'
			
			settings.set('move_context', context)
		# print(context)
		sublime.status_message('Context: ' + context.upper())

class SetMoveContextCommand(sublime_plugin.WindowCommand):
	def run(self, value, command, args={}):
		settings = self.window.settings();
		context = settings.get('move_context')
		settings.set('move_context', value)
		self.window.run_command(command, args)
		# print(context)
		sublime.status_message('Context: ' + context.upper())

class DoOnceMoveContextCommand(sublime_plugin.WindowCommand):
	def run(self, value):
		settings = self.window.settings();
		settings.set('move_context', value)
		settings.set('move_context_do_once', True)

class ContextualMoveCommand(sublime_plugin.WindowCommand):
	def run(self, **commands):
		settings = self.window.settings();
		context = settings.get('move_context');
		do_once = settings.get('move_context_do_once')
		
		context = context if context in commands else 'default'
		
		if context in commands:
			command = commands[context]
			args = command['args'] if 'args' in command else {}
			self.window.run_command(command['command'], args)
			print(command)

		if do_once:
			settings.set('move_context_do_once', False)
			settings.set('move_context', 'default')
