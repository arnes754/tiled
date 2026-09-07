"""Layout is pure arithmetic, so it is fully testable without a photo.

Cases worth having before the implementation exists:
  - a 600mm tile with 3mm grout produces a 603mm period
  - running_half offsets alternate rows by exactly half a period
  - variant choice is deterministic across runs and reasonably uniform
  - a tile field renders edge to edge with no seam at the canvas boundary
"""

import pytest


@pytest.mark.skip(reason="layout.tile_canvas not implemented")
def test_period_includes_grout():
    ...


@pytest.mark.skip(reason="layout.tile_canvas not implemented")
def test_running_bond_offset():
    ...
