"""Run segmentation and depth once over sample photos, cache to disk, exit.

This is the script that takes the GPU out of the development loop. Run it
overnight on a handful of room photos; afterwards the renderer iterates
against cached .npy and .png files on a laptop CPU, indefinitely, for free.

    python scripts/precompute_masks.py data/photos/*.jpg
"""

# TODO: argparse over photo paths, call perception.segment + estimate_depth,
# write into data/cache/<sha256>/ via perception.cache.store
