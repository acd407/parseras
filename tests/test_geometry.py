from typing import Dict, Any

from parseras import (
    River,
    BreakLine,
    CrossSection,
    Foot,
    Head,
    LateralWeir,
    StorageArea,
)


GEOMETRY_TESTS = [
    {
        "test_name": "River",
        "file_path": "tests/data/river.g01",
        "class": River,
    },
    {
        "test_name": "BreakLine",
        "file_path": "tests/data/breakline.g01",
        "class": BreakLine,
    },
    {
        "test_name": "CrossSection",
        "file_path": "tests/data/cross_secion.g01",
        "class": CrossSection,
    },
    {
        "test_name": "Foot",
        "file_path": "tests/data/foot.g01",
        "class": Foot,
    },
    {
        "test_name": "Head",
        "file_path": "tests/data/head.g01",
        "class": Head,
    },
    {
        "test_name": "LateralWeir",
        "file_path": "tests/data/lateral_weir.g01",
        "class": LateralWeir,
    },
    {
        "test_name": "StorageArea",
        "file_path": "tests/data/storage_area.g01",
        "class": StorageArea,
    },
]


def test_geometry(test_config: Dict[str, Any]) -> bool:
    with open(test_config["file_path"], "r") as f:
        original_lines = f.readlines()

    geometry_class = test_config["class"]
    geometry = geometry_class(original_lines)

    generated_lines = geometry.generate()
    output_file = test_config["file_path"].replace(".g01", ".output.g01")
    with open(output_file, "w") as f:
        f.writelines(generated_lines)

    generated_text = "".join(generated_lines)
    original_text = "".join(original_lines)
    return original_text == generated_text
