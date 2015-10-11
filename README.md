# Sublime Contexual Move Keys
`Ctrl+IJKL` to move. Other keys toggle move behavior. You can move across characters, words, search results, tabs, and more.

## The Gist
`Ctrl+IJKL` are contextual arrow keys. By default, they move the cursor one character at a time. `Ctrl+Shift+IJKL` will extend the selection. `Ctrl+Alt+IJKL` will delete. `Alt+JL` will undo/redo.

If you open the command palette or an autocomplete dropdown, they'll move through the options just like regular arrow keys. 

If you open the search panel, they'll move between search results. 

You can press other keys to modify move behavior:

Hotkey|Move Behavior|Mneumonic 
----------|----------|----------
`Ctrl+.`| Move one character at a time | `.` denotes characters in regex
`Ctrl+_`| Move by subwords | `_` delimits subwords in C-like languages
`Ctrl+,`| Move by words | `,` delimits words in natural language (`Ctrl+spacebar` is already taken)
`Ctrl+;`| Move to the beginning/end of the line/document. Subsequent keypresses to `Ctrl+IJKL` will return to default behavior | `;` delimits lines in C-like languages (`Ctrl+enter` is already taken)
`Ctrl+tab`| Move between tabs | Resembles existing shortcut
`Ctrl++`| Scroll | `+` looks like the cursor you get when you click the middle mouse button
`Ctrl+pipe`| Add cursors to adjacent lines. Press escape to return to a single selection and retrn to default behavior | The "pipe" character looks like a cursor
`Ctrl+^`| Move text around | Same shortcut used in TextMate
`Ctrl+[`| fold/unfold | Resembles existing shortcut
`Ctrl+]`| indent/unindent and transpose by line | Resembles existing shortcut
`Ctrl+f2`| move through bookmarks | Resembles existing shortcut
`Ctrl+f6`| move through spelling errors | Resembles existing shortcut
`Ctrl+[1-5]`| perform the action `N` number of times, where `N` is the button you pressed | Similar shortcut used in Vim

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
