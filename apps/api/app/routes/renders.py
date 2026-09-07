"""POST /renders - the hot path.

Must stay cheap: perception is already cached against photo_id, so this is
layout + warp + lighting + composite only. If this endpoint ever loads a
model, something has gone wrong architecturally.
"""
