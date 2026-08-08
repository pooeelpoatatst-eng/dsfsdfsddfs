from PIL import Image

from app.modules.visual_media import Image as ModuleImage


def test_visual_media_imports_pillow_transforms() -> None:
    assert ModuleImage is Image
