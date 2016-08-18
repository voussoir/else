Open Dir DL
===========

The open directory downloader.

Requires `pip install beautifulsoup4`.

See inside opendirdl.py for usage instructions.

- 2016 08 16
    - **[cleanup]** Now that Downloady uses temp files for incomplete downloads, that logic can be removed from opendirdl.

- 2016 08 10
    - **[addition]** Added clickable links to each directory on HTML tree pages.
    - **[bugfix]** Fixed bug in smart_insert caused by 404's being considered falsey, triggering the 'one and only one' exception.
    - **[bugfix]** Fixed bug in smart_insert where 404'd URLs were not being deleted from the database.

- 2016 08 02
    - **[cleanup]** Removed the need for div IDs on the Tree pages by making the collapse button use `this.nextSibling`.
    - **[cleanup]** Rewrote `build_file_tree` with a way simpler algorithm.
    - **[removal]** Removed the ability to set a Node's parent during `__init__` because it wasn't fully fleshed out and doesn't need to be used anyway.

- 2016 08 01
    - **[addition]** Made the digest work even if you forget the http://
    
- 2016 07 29
    - **[change]** Moved some nested function definitions out to the top level, and made the construction of the file tree its own function. These functions really don't need to be used on their own, but they were cluttering the logic of the `tree` command.
    - **[change]** Renamed `Tree.listnodes` to `Tree.list_children`, and the `customsort` now expects to operate on Node objects rather than `(identifier, Node)` tuples. Nodes already have their identifier so the tuple was unecessary.
    - **[change]** Replaced local `download_file` function with a call to `downloady.download_file`. It supports download continuation and removes duplicate work.
    - **[cleanup]** Replaced all `safeprint` calls with `write` because it provides access to safeprint as well as file writing if needed.
    - **[removal]** Removed `Tree.sorted_children` since it was basically a duplicate of `Tree.listnodes` and I don't know why I had both.

- 2016 07 25
    - **[change]** Bytespersecond is now parsed by `bytestring.parsebytes` rather than `eval`, so you can write "100k" as opposed to "100 * 1024" etc.
    - **[removal]** Removed the `Downloader` class after watching [this Jack Diederich talk](https://youtu.be/o9pEzgHorH0) about unecessary classes.

- 2016 07 19
    - **[addition]** Gave the HTML tree divs a very gentle shadow and alternating colors to help with depth perception.
    - **[bugfix]** Fixed the allowed characters parameter of `filepath_sanitize`, which was not written correctly but worked out of luck.
    - **[cleanup]** Rearranged the big blocks to be in a logical order rather than alphabetical order. Walker > Downloader > other classes
    - **[cleanup]** Renamed the `keep_pattern` and `remove_pattern` functions to `keep_pattern_argparse` etc to be consistent with the other functions used by the argparser. *Does not affect the commandline usage!*
    - **[cleanup]** Fixed some mismatched code vs comments

- 2016 07 08
    - **[bugfix]** Fixed bug in which trees wouldn't generate on server:port urls.

- 2016 07 04
    - **[addition]** Added new argparse command "tree"

- 2016 02 08
    - **[bugfix]** Fixed bug where server:port urls did not create db files because of the colon. It's been replaced by a hash.
    - **[change]** Moved db commits to only happen at the end of a digest.
