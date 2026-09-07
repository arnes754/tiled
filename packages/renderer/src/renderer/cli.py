"""Render from the command line, no server and no browser.

    python -m renderer.cli render \
        --photo data/photos/bathroom.jpg \
        --tile catalogue/tiles/example-600x600-matte.json \
        --corners 120,880 1450,760 1600,1290 40,1340 \
        --width-mm 3200 \
        --out data/renders/out.jpg

The fastest way to judge whether the illusion holds. Add --sweep to render
every SKU in the catalogue against one photo for a contact sheet.
"""


def main():
    raise NotImplementedError


if __name__ == "__main__":
    main()
