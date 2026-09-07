"""Everything that needs a model lives here, and nowhere else.

Two calls, both cached to disk by photo hash:

    masks  = segment(photo)     which pixels are floor / wall / occluder
    depth  = estimate_depth(photo)   optional, proposes the plane

Both run ONCE per uploaded photo. Every tile the customer clicks afterwards
is pure renderer work. That single caching decision is what keeps a browsing
session at fractions of a cent instead of a GPU-second per click.
"""
