Minecraft 3D Vector
===================

Given one, two, or three square images, produce a 3-dimensional rendering of them as a block in glorious SVG.

The svg has two layers. They contain identical shapes, but the lower one is slightly blurred. Although the shapes are aligned pretty well, some rendering engines create a 1px gap between shapes due to rounding. The blurred object helps fill these in. A mask is used to make sure the blur does not cause a halo around the edges. The seams still aren't perfect but they're pretty good, man.

Because each pixel of each face produces two shapes, you should probably stick to small source images.

## Usage:

    > mc3dvector.py dirt.png
    Creates a block with dirt on all sides

    > mc3dvector.py tree_top.png tree_side.png
    Creates a block with tree_top on the top, and tree_side on both sides.

    > mc3dvector.py dirt.png gravel.png obsidian.png
    Creates a block with dirt on top, gravel on the left, and obsidian on the right.

The images do not need to be the same size as each other, but they each must be square.