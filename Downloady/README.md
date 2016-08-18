Downloady
=========

- 2016 08 16
    - Downloady now uses temporary files for incomplete downloads, and renames them when finished. This helps distinguish downloads that were interrupted and should be resumed from files that just happen to have the same name, which previously would have been interpreted as a resume. This improves overall ease-of-use, simplifies the behavior of the `overwrite` parameter, and will remove duplicate work from other programs.
    - Rewrote the plan creator and download function to do a better job of separating concerns and simplify the plan selector.