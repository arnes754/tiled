#!/usr/bin/env bash
# Download a handful of CC0 tile textures for local testing.
#
# ambientCG and Poly Haven both publish seamless PBR tile materials under CC0
# with real-world scale metadata - the same shape of data a production
# catalogue needs, with no licensing questions while prototyping.
#
# TODO: pick ~6 materials (matte porcelain, gloss ceramic subway, terrazzo,
# marble-effect, hex mosaic, wood-effect plank), fetch the colour maps into
# catalogue/textures/<name>/, and write a matching JSON into catalogue/tiles/
# with the true size_mm from the material's scale metadata.
set -euo pipefail
echo "not implemented - see comments"
