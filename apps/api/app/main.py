"""FastAPI entrypoint.

    uvicorn app.main:app --reload

Deliberately thin: routes validate, call the renderer, and return. Anything
resembling image maths belongs in packages/renderer.
"""

from fastapi import FastAPI

app = FastAPI(title="tilevis")


@app.get("/health")
def health():
    return {"ok": True}


# TODO: mount routes.photos, routes.renders, routes.catalogue
# TODO: CORS for the web app in dev
