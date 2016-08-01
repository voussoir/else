Open Dir DL
===========

The open directory downloader

Requires `pip install beautifulsoup4`

See inside opendirdl.py for usage instructions.

- 2016 08 01
    - Made the digest work even if you forget the http://
    
- 2016 07 29
    - Moved some nested function definitions out to the top level, and made the construction of the file tree its own function. These functions really don't need to be used on their own, but they were cluttering the logic of the `tree` command.
    - Renamed `Tree.listnodes` to `Tree.list_children` and the `customsort` now expects to operate on Node objects rather than `(identifier, Node)` tuples. Nodes already have their identifier so the tuple was unecessary.
    - Removed `Tree.sorted_children` since it was basically a duplicate of `Tree.listnodes` and I don't know why I had both.
    - Replaced all `safeprint` calls with `write` because it provides access to safeprint as well as file writing if needed.
    - Replaced local `download_file` function with a call to `downloady.download_file`. It supports download continuation and removes duplicate work.

- 2016 07 25
    - Removed the `Downloader` class after watching [this Jack Diederich talk](https://youtu.be/o9pEzgHorH0) about unecessary classes.
    - Bytespersecond is now parsed by `bytestring.parsebytes` rather than `eval`, so you can write "100k" as opposed to "100 * 1024" etc.

- 2016 07 19
    - Rearranged the big blocks to be in a logical order rather than alphabetical order. Walker > Downloader > other classes
    - Renamed the `keep_pattern` and `remove_pattern` functions to `keep_pattern_argparse` etc to be consistent with the other functions used by the argparser. *Does not affect the commandline usage!*
    - Gave the HTML tree divs a very gentle shadow and alternating colors to help with depth perception.
    - Fixed some mismatched code vs comments
    - Fixed the allowed characters parameter of `filepath_sanitize`, which was not written correctly but worked out of luck.

- 2016 07 08
    - Fixed bug in which trees wouldn't generate on server:port urls.

- 2016 07 04
    - Added new argparse command "tree"

- 2016 02 08
    - Fixed bug where server:port urls did not create db files because of the colon. It's been replaced by a hash.
    - Moved db commits to only happen at the end of a digest.
