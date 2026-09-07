"""Surface segmentation.

Model choice is a licensing decision as much as a technical one - see
docs/licences.md before switching:

  SAM 3     concept prompts ("floor", "wall", "toilet") in one pass.
            Meta's own licence: commercial use allowed, but it is not an
            open-source licence. Read it before launch.
  SAM 2     Apache-2.0, unambiguous. Point/box prompts instead of concepts,
            so it needs prompt seeding logic.
  SegFormer ADE20K has floor/wall/ceiling as native classes and the model is
            tiny - but NVIDIA's weights are NON-COMMERCIAL. Dev only, must be
            replaced before this ships.

Whichever backend, the contract is the same.
"""

SURFACES = ("floor", "wall", "ceiling")
OCCLUDERS = ("toilet", "sink", "cabinet", "bathtub", "shower", "rug", "furniture", "door")


def segment(image_bgr, backend: str = "sam2") -> dict:
    """Return {name: bool mask} for surfaces and occluders present."""
    raise NotImplementedError


def paintable(masks: dict, surface: str = "floor"):
    """masks[surface] AND NOT union(occluders present)."""
    raise NotImplementedError
