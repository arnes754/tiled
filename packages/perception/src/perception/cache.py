"""Disk cache keyed by photo content hash.

This is what removes the GPU from the development loop entirely: run
segmentation and depth once over a handful of sample photos, commit nothing,
and then iterate on layout/warp/lighting for days against cached .npy files
on a laptop CPU.

    data/cache/<sha256>/
        masks/floor.png
        masks/toilet.png
        depth.npy
        meta.json
"""

from pathlib import Path

CACHE_DIR = Path("data/cache")


def key_for(image_path: str) -> str:
    """sha256 of the file bytes."""
    raise NotImplementedError


def load(key: str) -> dict | None:
    raise NotImplementedError


def store(key: str, masks: dict, depth=None, meta: dict | None = None) -> None:
    raise NotImplementedError
