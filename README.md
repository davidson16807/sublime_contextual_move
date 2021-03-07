# Sublime Contexual Move Keys
`Ctrl+IJKL` to move. Other keys toggle move behavior. You can move across characters, words, search results, tabs, and more.

## The Gist
* `Ctrl+IJKL` are contextual arrow keys. By default, they move the cursor one character at a time. 
* `Ctrl+Shift+IJKL` will extend the selection. 
* `Ctrl+Alt+IJKL` will delete text ("**alter** it").
* `Ctrl+Alt+Shift+IJKL` will move text (**alter** by **shifting** it). 
* `Alt+JL` will undo/redo changes to text.
* If you open the command palette or an autocomplete dropdown, they'll move through the options just like regular arrow keys. 
* If you open the search panel, they'll move between search results. 
* You can press other keys to modify move behavior, shown below.

Hotkey|Move Behavior|Mneumonic 
----------|----------|----------
`Ctrl+.`| Move one character or line at a time | `.` denotes characters in regex
`Ctrl+_`| Move by subwords | `_` delimits subwords in C-like languages
`Ctrl+,`| Move by words | `,` delimits words in natural language (`Ctrl+spacebar` is already taken)
<!-- `Ctrl+1`| Move through comma separated list items | grammar rules are mapped to numbers, sorted by precedence -->
<!-- `Ctrl+2`| Move through statements | grammar rules are mapped to numbers, sorted by precedence -->
`Ctrl+1`| Move through functions | grammar rules are mapped to numbers, sorted by precedence
`Ctrl++`| Move through pages and tabs | `+` looks like the cursor you get when you click the middle mouse button (`Ctrl+tab` is already taken)
`Ctrl+pipe`| Add cursors to adjacent lines. Press escape to return to a single selection and retrn to default behavior | The "pipe" character looks like a cursor
`Ctrl+[`| fold/unfold | Resembles existing shortcut
`Ctrl+]`| indent/unindent and transpose by line | Resembles existing shortcut
`Ctrl+f2`| Move through bookmarks | Resembles existing shortcut
`Ctrl+f6`| Move through spelling errors | Resembles existing shortcut
`Ctrl+;`| Move to the beginning/end of the list of things being traversed, which can vary based on the other hotkeys. This behavior turns itself off after a single use. | `;` is next to `IJKL` and allows sweeping motion across the keyboard
`Ctrl+enter`| Create a new thing being traversed above/below, which can vary based on the other hotkeys. This behavior turns itself off after a single use. | `enter` adds new lines

* You can combine the hotkeys above with modifiers in useful ways. For instance: 
** pressing `Ctrl+1`, `Ctrl+;`, `Ctrl+Alt+L` will delete everything to the end of a comma separated list 
** pressing `Ctrl+2` followed by any combination of `Ctrl+Alt+Shift+IK` will change the order of functions in the document.
** pressing `Ctrl++`, followed by any combination of `Ctrl+Alt+JL` will close tabs.

## FAQ

###Why?

Plenty of reasons:
 
 * Provide vim-like navigation without the steep learning curve

 * Vastly expand a user's hotkey repertoire without taxing memory

 * Eliminate the need to leave the home row when navigating through text

 * Free up keyboard real estate without loss of utility

 * Create a sensible framework on which users can create their own hotkeys

###Why not `Ctrl+WASD`?
 Because `Ctrl+S` and `Ctrl+A` are some of the most widely adopted hotkeys of all time and I don't plan to remap their behavior. Fortunately, the plugin is designed mostly to provide navigation for times when the mouse cannot be easily switched to. Many of the standard hotkeys only exist because they worked well regardless of whether the mouse is available, so we have plenty of options to work with on the right hand side.

###Why not `Ctrl+HJKL`?
 Because this is not vim. The vast majority of users are already familiar with the "inverse T" style of navigation, thanks largely to WASD and the regular arrow keys. IJKL is also a common choice for other software, too. For instance, Kerbal Space Program uses IJKL to handle translations. Sublime itself uses IJKL to traverse the "Folders" side bar. 
 
###Why not use Vim?
 See above. This is a plugin for mortals.
 
###Why not just extend behavior to the regular arrow keys?
 Because moving your hand interrupts your workflow. I want to keep both hands on the home row for as long as I can.
 
###You changed my favorite hotkey!
 That wasn't a question, but yes, it's possible I did that. I tried to avoid modifying standard hotkeys on the left hand side of the keyboard.   As with any plugin, you can remap the keys as you see fit.
