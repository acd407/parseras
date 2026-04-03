from typing import List, Dict, Any

from parseras import (
    River,
    BreakLine,
    CrossSection,
    Foot,
    Head,
    LateralWeir,
    StorageArea,
    RASStructure,
    DataBlockValue,
    GeometryFile,
)


class Block(RASStructure):
    def __init__(self, lines: List[str], key: str, value_width: int, values_per_line: int, items_per_value: int):
        self._key_value_types = {
            key: (
                DataBlockValue,
                {"value_width": value_width, "values_per_line": values_per_line, "items_per_value": items_per_value},
            ),
        }
        super().__init__(lines)


GEOMETRY_TESTS = [
    {
        "test_name": "River",
        "file_path": "tests/river.g01",
        "class": River,
    },
    {
        "test_name": "BreakLine",
        "file_path": "tests/breakline.g01",
        "class": BreakLine,
    },
    {
        "test_name": "CrossSection",
        "file_path": "tests/cross_secion.g01",
        "class": CrossSection,
    },
    {
        "test_name": "Foot",
        "file_path": "tests/foot.g01",
        "class": Foot,
    },
    {
        "test_name": "Head",
        "file_path": "tests/head.g01",
        "class": Head,
    },
    {
        "test_name": "LateralWeir",
        "file_path": "tests/lateral_weir.g01",
        "class": LateralWeir,
    },
    {
        "test_name": "StorageArea",
        "file_path": "tests/storage_area.g01",
        "class": StorageArea,
    },
]


BLOCK_TESTS = [
    {
        "test_name": "ReachXY",
        "file_path": "tests/common_blocks/block1.g01",
        "key": "Reach XY",
        "value_width": 16,
        "values_per_line": 4,
        "items_per_value": 2,
    },
    {
        "test_name": "StaElev",
        "file_path": "tests/common_blocks/block2.g01",
        "key": "#Sta/Elev",
        "value_width": 8,
        "values_per_line": 10,
        "items_per_value": 2,
    },
    {
        "test_name": "XSGisCutLine",
        "file_path": "tests/common_blocks/block3.g01",
        "key": "XS GIS Cut Line",
        "value_width": 16,
        "values_per_line": 4,
        "items_per_value": 2,
    },
    {
        "test_name": "StorageAreaSurfaceLine",
        "file_path": "tests/common_blocks/block4.g01",
        "key": "Storage Area Surface Line",
        "value_width": 16,
        "values_per_line": 2,
        "items_per_value": 2,
    },
    {
        "test_name": "StorageArea2DPoints",
        "file_path": "tests/common_blocks/block5.g01",
        "key": "Storage Area 2D Points",
        "value_width": 16,
        "values_per_line": 4,
        "items_per_value": 2,
    },
]


FULL_FILE_TESTS = [
    {
        "test_name": "all.g01",
        "file_path": "tests/all.g01",
    },
    {
        "test_name": "leak.g01",
        "file_path": "tests/leak.g01",
    },
    {
        "test_name": "Muncie.g01",
        "file_path": "tests/Muncie.g01",
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


def test_block(test_config: Dict[str, Any]) -> bool:
    with open(test_config["file_path"], "r") as f:
        original_lines = f.readlines()

    block = Block(
        original_lines,
        test_config["key"],
        test_config["value_width"],
        test_config["values_per_line"],
        test_config["items_per_value"],
    )

    generated_lines = block.generate()
    output_file = test_config["file_path"].replace(".g01", ".output.g01")
    with open(output_file, "w") as f:
        f.writelines(generated_lines)

    generated_text = "".join(generated_lines)
    original_text = "".join(original_lines)
    return original_text == generated_text


def main():
    geometry_results = {}
    for test_config in GEOMETRY_TESTS:
        geometry_results[test_config["test_name"]] = test_geometry(test_config)

    block_results = {}
    for test_config in BLOCK_TESTS:
        block_results[test_config["test_name"]] = test_block(test_config)

    full_file_results = {}
    for test_config in FULL_FILE_TESTS:
        full_file_results[test_config["test_name"]] = test_full_file(test_config["file_path"])

    print("=" * 80)
    print("Test Summary")
    print("=" * 80)

    all_passed = True

    for test_name, passed in geometry_results.items():
        print(f"{'✅' if passed else '❌'} {test_name} test: {'PASSED' if passed else 'FAILED'}")
        all_passed = all_passed and passed

    print("=" * 60)

    for test_name, passed in block_results.items():
        print(f"{'✅' if passed else '❌'} {test_name} test: {'PASSED' if passed else 'FAILED'}")
        all_passed = all_passed and passed

    print("=" * 60)

    for test_name, passed in full_file_results.items():
        print(f"{'✅' if passed else '❌'} {test_name} test: {'PASSED' if passed else 'FAILED'}")
        all_passed = all_passed and passed

    print("=" * 80)

    if all_passed:
        print("\n🎉 All tests passed successfully!")
        return 0
    else:
        print("\n❌ Some tests failed.")
        return 1


def test_full_file(file_path: str) -> bool:
    with open(file_path, "r") as f:
        original_lines = f.readlines()

    geometry_file = GeometryFile(file_path=file_path)

    generated_lines = geometry_file.generate()
    output_file = file_path.replace(".g01", ".output.g01")
    with open(output_file, "w") as f:
        f.writelines(generated_lines)

    generated_text = "".join(generated_lines)
    original_text = "".join(original_lines)
    return original_text == generated_text


if __name__ == "__main__":
    exit(main())
