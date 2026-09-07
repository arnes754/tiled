"""Perspective warp, and the antialiasing that makes or breaks it."""


def warp_to_image(canvas, H, out_size, supersample=3):
    """Warp a plane-space canvas into image space.

    THE TRAP: cv2.warpPerspective does no mipmapping. At the far end of a
    floor, hundreds of texture pixels compress into one output pixel and the
    result is shimmering aliased noise - the single most obvious "this is
    fake" artefact.

    Mitigations, in order of preference:
      1. render this pass in WebGL client-side, where the GPU gives correct
         mipmapping and anisotropic filtering for free
      2. render the canvas at `supersample`x and downsample with INTER_AREA
      3. build a mip pyramid and select the level per-pixel from the
         Jacobian of H (correct, slow, implement only if 1 and 2 fall short)
    """
    raise NotImplementedError


def jacobian_scale(H, points):
    """Local scale factor of H at each point - drives mip level selection."""
    raise NotImplementedError
