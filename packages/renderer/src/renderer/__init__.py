"""Geometric tile renderer.

Hard rule: nothing in this package may import torch, transformers, or reach
the network. It is numpy and opencv only, so the render loop stays fast,
free, and reproducible. Model output arrives as plain arrays from
`tilevis-perception`.
"""

from .types import Plane, RenderRequest, TileSpec

__all__ = ["Plane", "RenderRequest", "TileSpec"]
