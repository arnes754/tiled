# Model and dependency licences

Record every model here before adding it. This ships commercially one day and
several of the obvious choices are non-commercial.

## Models

| Model | Licence | Commercial | Note |
|---|---|---|---|
| Depth Anything 3 | Apache-2.0 (code + weights) | yes | Clean. No launch risk. |
| SAM 2 | Apache-2.0 | yes | Unambiguous. Point/box prompts. |
| SAM 3 | Meta custom "SAM Licence" | yes, with terms | Not open source. No reverse engineering, redistribution only under the same terms. Read before launch. |
| SegFormer (ADE20K) | NVIDIA Source Code Licence | **NO** | "only may be used or intended for use non-commercially". Dev and evaluation only. Must be replaced. |
| Mask2Former (ADE20K) | "other" on the model card | unclear | Check the specific checkpoint before relying on it. |
| FLUX `dev` weights | non-commercial | **NO** | Testing only. |
| Qwen-Image-Edit | Apache-2.0 | yes | ~45GB VRAM - rented GPU, not a laptop. |

## Libraries

Permissive and unproblematic: Next.js, React, TypeScript, FastAPI, NumPy,
Pillow, PyTorch, transformers, OpenCV (incl. `ximgproc`), Postgres.

One footnote: Redis relicensed in 2024 to RSAL/SSPL. Using it as a queue
inside this product is fine; it only matters if you resell Redis itself.
`docker-compose.yml` uses **Valkey**, the BSD fork, to sidestep the question.

## Textures

CC0 from ambientCG / Poly Haven for testing. Production textures come from
the retailer, or are produced under contract - and who owns them should be
settled in writing before the library is built.
