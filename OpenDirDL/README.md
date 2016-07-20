Open Dir DL
===========

- 2016 07 19
    - Rearranged the big blocks to be in a logical order rather than alphabetical order. Walker > Downloader > other classes
    - Renamed the `keep_pattern` and `remove_pattern` functions to `keep_pattern_argparse` etc to be consistent with the other functions that take argparse namespaces as their only parameter. Does not affect the commandline usage.
    - Gave the HTML tree divs a very gentle shadow and alternating colors to help with depth perception.

- 2016 07 08
    - Fixed bug in which trees wouldn't generate on server:port urls.

- 2016 07 04
    - Added new argparse command "tree"

- 2016 02 08
    - Fixed bug where server:port urls did not create db files.
    - Moved db commits to only happen at the end of a digest.

Requires `pip install beautifulsoup4`

See inside opendirdl.py for usage instructions.