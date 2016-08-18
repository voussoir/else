Clip Extension
==============

This module works with pyperclip to provide some handy features for commandline utilities.

Instead of having the user paste text into the commandline to run your script, just let them enter `script.py !c` and resolve it automatically. Pasting into the cmd on Windows is annoying and requires a mouse-click so this can be very convenient.

Since "!i" resolves to user input, your script can accept piping with `ls | script.py !i`.