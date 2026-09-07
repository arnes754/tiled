"""POST /photos - upload, normalise, and (optionally) kick off perception.

Reject bad input here rather than rendering something misleading: under ~1MP,
heavy motion blur, or no plausible floor region all get an honest error that
says what to reshoot. See docs/pipeline.md step 1.
"""
