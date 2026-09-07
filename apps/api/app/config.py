"""Settings from environment. See .env.example - none are required for the
renderer-only dev loop.
"""

from pydantic import BaseModel


class Settings(BaseModel):
    data_dir: str = "./data"
    torch_device: str = "mps"
    image_edit_provider: str | None = None  # blank disables the finish pass


settings = Settings()
