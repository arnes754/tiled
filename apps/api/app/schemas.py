"""Request/response models. Mirrors renderer.types across the wire."""

from pydantic import BaseModel


class PlaneIn(BaseModel):
    quad: list[tuple[float, float]]
    width_mm: float
    height_mm: float
    kind: str = "floor"


class RenderIn(BaseModel):
    photo_id: str
    sku: str
    planes: list[PlaneIn]
    pattern: str = "stack"
    grout_width_mm: float = 3.0
    grout_color: str = "#C9C4BA"
    offset_mm: tuple[float, float] = (0.0, 0.0)


class RenderOut(BaseModel):
    render_id: str
    before_url: str
    after_url: str
    area_m2: float | None = None   # feeds the m2 calculator and the quote
