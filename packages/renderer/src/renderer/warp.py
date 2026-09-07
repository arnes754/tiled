"""Perspective warp, and the antialiasing that makes or breaks it."""

import cv2
import numpy as np


def warp_to_image(canvas, H, out_size, supersample=3):
    """Warp a plane-space canvas into image space.

    ``canvas`` is canvas_px (BGR float32); ``H`` is a canvas_px -> image_px
    homography; ``out_size`` is (width, height) of the output image in
    image_px. Returns BGR float32 of shape (height, width, 3); pixels outside
    the warped quad are 0.

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

    This implements mitigation 2: warp into a supersample-times-larger buffer
    and box-filter (INTER_AREA) down, so each output pixel averages many
    canvas samples instead of point-sampling one.
    """
    out_w, out_h = int(out_size[0]), int(out_size[1])
    ss = max(1, int(supersample))
    h = np.asarray(H, dtype=np.float64)

    if ss == 1:
        return cv2.warpPerspective(
            canvas, h, (out_w, out_h), flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_CONSTANT, borderValue=(0.0, 0.0, 0.0),
        )

    scale = np.array([[ss, 0.0, 0.0], [0.0, ss, 0.0], [0.0, 0.0, 1.0]], dtype=np.float64)
    big = cv2.warpPerspective(
        canvas, scale @ h, (out_w * ss, out_h * ss), flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT, borderValue=(0.0, 0.0, 0.0),
    )
    return cv2.resize(big, (out_w, out_h), interpolation=cv2.INTER_AREA)


def jacobian_scale(H, points):
    """Local scale factor of H at each point - drives mip level selection."""
    raise NotImplementedError("mip-pyramid path (warp mitigation 3) is out of P1 scope")
