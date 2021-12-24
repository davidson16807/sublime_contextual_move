import sublime, sublime_plugin, datetime

class SetMoveContextCommand(sublime_plugin.WindowCommand):
	def run(self, value, demarcator='', command=None, args={}):
		settings = self.window.settings();
		settings.set('move_context', value)
		if command:	self.window.run_command(command, args)

class DoOnceMoveContextCommand(sublime_plugin.WindowCommand):
	def run(self, value):
		settings = self.window.settings();
		settings.set('move_context', value)
		settings.set('move_context_do_once', True)

class ToEndMoveContextCommand(sublime_plugin.WindowCommand):
	def run(self):
		settings = self.window.settings();
		settings.set('move_context_to_end', True)

class ContextualMoveCommand(sublime_plugin.WindowCommand):
	def run(self, **commands):
		settings = self.window.settings();
		context = settings.get('move_context');
		do_once = settings.get('move_context_do_once')
		to_end = settings.get('move_context_to_end')

		if do_once:
			settings.set('move_context', 'default')

		context = context if context else 'default'
		if to_end:
			context = context+'_to_end' if context+'_to_end' in commands else 'default_to_end'
		else:
			context = context if context in commands else 'default'
		
		if context in commands:
			command = commands[context]
			args = command['args'] if 'args' in command else {} 
			self.window.run_command(command['command'], args)

		if to_end:
			settings.set('move_context_to_end', False)

		if do_once:
			settings.set('move_context_do_once', False)
		