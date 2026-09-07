# Textures

Not committed (except this file). Fetch CC0 test textures with:

    ./scripts/fetch_test_textures.sh

Sources with real-world scale metadata and no licensing questions:
ambientCG (https://ambientcg.com) and Poly Haven (https://polyhaven.com).

## What a production texture must be

- **Seamless.** Tiles edge to edge with no visible join.
- **Scale-known.** 300-600 px per real 100 mm, recorded, not guessed.
- **Flat-lit.** No baked shadows or highlights - lighting is added at render
  time from the customer's own room. A texture with a shadow in it will show
  that shadow in every render, in the wrong place.
- **Colour-calibrated** against a physical sample under showroom light.

This library, not the software, is usually the critical path of the project.
