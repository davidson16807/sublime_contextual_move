# Sublime Contexual Move Keys
`Ctrl+IJKL` to move. Other keys toggle move behavior. You can move across characters, words, search results, tabs, and more.

## The Gist
`Ctrl+IJKL` are contextual arrow keys. By default, they move the cursor one character at a time. Adding "Shift" will extend the selection. 

If you open the command palette or an autocomplete dropdown, they'll move through the options just like regular arrow keys. 

If you open the search panel, they'll move between search results. 

You can press other keys to toggle move behavior:

 * Toggle `Ctrl+,` to move a word at a time.
	
 * Toggle `Ctrl+_` to move by subwords.
 
 * Toggle `Ctrl+;` to move to the beginning/end of the line or document. Subsequent keypresses to `Ctrl+IJKL` will return to the default behavior.
	
 * Toggle `Ctrl+tab` to move between tabs. 
	
 * Toggle `Ctrl+|` to add cursors to adjacent lines.
	
 * Toggle `Ctrl+=` to scroll.

 * Toggle `Ctrl+^` to move the text around - left/right to transpose characters, up/down to transpose lines.
	
 * Toggle `Ctrl+[` to fold/unfold text.
 
 * Toggle `Ctrl+]` to indent/unindent and transpose by lines.
	
Other keys will modify move behavior after being pressed. After pressing `Ctrl+U`, subsequent presses to `Ctrl+IK` will soft undo or soft redo. This does not change the existing `Ctrl+U` behavior.
	


## FAQ

###Why?

Plenty of reasons:
 * Provide vim-like navigation without the steep learning curve

 * Vastly expand a user's hotkey repertoire without taxing memory

 * Eliminate the need to leave the home row when navigating through text

 * Create an economy of hotkeys, freeing up keyboard real estate so users can create their own hotkeys

###Why not `Ctrl+WASD`?
 Because `Ctrl+S` and `Ctrl+A` are some of the most widely adopted hotkeys of all time and I don't plan to remap their behavior.

###Why not `Ctrl+HJKL`?
 Because this is not vim. The vast majority of users are already familiar with the "inverse T" style of navigation, thanks largely to WASD and the regular arrow keys.
 
###Why not use Vim?
 See above. This is a plugin for mortals.
 
###Why not just extend behavior to the regular arrow keys?
 Because moving your hand interrupts your workflow. I want to keep both hands on the home row for as long as I can.
 
###You changed my favorite hotkey!
 That wasn't a question, but yes, as with any plugin, you can remap the keys as you see fit.
