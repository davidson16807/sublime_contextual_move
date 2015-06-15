# Sublime Contexual Move Keys
Ctrl+IJKL to move. Other keys toggle move behavior. You can move across characters, words, search results, tabs, and more.

## The Gist
Ctrl+ijkl are contextual arrow keys. By default, they move the cursor one character at a time. If you open the search panel, they'll move between search results. 

You can press other keys to toggle their behavior:

 * Toggle Ctrl+space to move a word at a time.
	
 * Toggle Ctrl+_ to move by subwords.
	
 * Toggle Ctrl+tab to move between tabs. 
	
 * Toggle Ctrl+| to add cursors to adjacent lines.
	
 * Toggle Ctrl+] to move the text around - left/right to indent/unindent, up/down to transpose.
	
 * Toggle Ctrl+[ to fold/unfold text.
	
Other keys will modify their behavior after being pressed:
	
 * Press Ctrl+U and they'll soft undo or soft redo. This does not effect the existing Ctrl+U behavior.
	
 * Press Ctrl+Enter and they'll move to the beginning/end of the line or document. Subsequent keypresses to Ctrl+IJKL will return them to their default behavior.


## FAQ

###Why not Ctrl+WASD?
 Because Ctrl+S and Ctrl+A are some of the most widely adopted hotkeys of all time and I don't plan to remap their behavior.

###Why not Ctrl+HJKL?
 Because this is not vim. The vast majority of users are already familiar with the "inverse T" style of navigation, thanks largely to WASD and the regular arrow keys.
 
###Why not use Vim?
 See above. This is a plugin for mortals.
 
###Why not just extend behavior to the arrow keys?
 Because moving your hand interrupts your workflow. I want to keep both hands on the home row for as long as I can.
 
###You changed my favorite hotkey!
 That wasn't a question, but yes, as with any plugin, you can remap the keys as you see fit.
