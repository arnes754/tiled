// Client-side perspective transform for the live preview.
//
// Why duplicate the server's maths: dragging a corner must update at 60fps,
// and a round trip per frame cannot do that. The browser draws the
// interactive preview in WebGL - which also gives correct mipmapping and
// anisotropic filtering for free, solving the far-floor aliasing that
// cv2.warpPerspective does not handle (see packages/renderer/warp.py).
//
// The server render remains the source of truth for the saved image.
export {};
// TODO: solve 4-point homography, upload texture, draw quad with mipmaps
