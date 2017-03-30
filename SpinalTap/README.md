Spinal
========

A couple of tools for copying files and directories.

- 2017 03 12
    - Fix the PermissionDenied callback always being called with Source path even if the Destination is the one that caused the problem.

- 2016 12 06
    - Fixed bug where dry runs would still create directories

- 2016 11 27
    - Renamed the `copy_file` parameter `callback` to `callback_progress` for clarity.

- 2016 03 02
    - Fixed issue where the copy's path casing was based on the input string and not the path's actual casing (since Windows doesn't care).
    - Change the returned written_bytes to 0 if the file did not need to be copied. This is better for tracking how much actually happens during each backup.
    - Fixed encode errors caused by callback_v1's print statement.

- 2016 03 03
    - Moved directory / filename exclusion logic into the walk_generator so the caller doesn't need to worry about it.
    - walk_generator now yields absolute filenames since copy_dir no longer needs to process exclusions, and that was the only reason walk_generator used to yield them in parts.

- 2016 03 04
    - Created a FilePath class to cache os.stat data, which should reduce the number of unecessary filesystem calls.

- 2016 03 18
    - Added `glob.escape` to `get_path_casing`.
    - Added callbacks for some extra debug output.