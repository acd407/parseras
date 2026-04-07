from typing import List, Dict, Any

from parseras import RASStructure, DataBlockValue


class Block(RASStructure):
    def __init__(self, lines: List[str], key: str, value_width: int, values_per_line: int, items_per_value: int):
        self._key_value_types = {
            key: (
                DataBlockValue,
                {"value_width": value_width, "values_per_line": values_per_line, "items_per_value": items_per_value},
            ),
        }
        super().__init__(lines)


BLOCK_TESTS = [
    {
        "test_name": "ReachXY",
        "file_path": "tests/data/common_blocks/block1.g01",
        "key": "Reach XY",
        "value_width": 16,
        "values_per_line": 4,
        "items_per_value": 2,
    },
    {
        "test_name": "StaElev",
        "file_path": "tests/data/common_blocks/block2.g01",
        "key": "#Sta/Elev",
        "value_width": 8,
        "values_per_line": 10,
        "items_per_value": 2,
    },
    {
        "test_name": "XSGisCutLine",
        "file_path": "tests/data/common_blocks/block3.g01",
        "key": "XS GIS Cut Line",
        "value_width": 16,
        "values_per_line": 4,
        "items_per_value": 2,
    },
    {
        "test_name": "StorageAreaSurfaceLine",
        "file_path": "tests/data/common_blocks/block4.g01",
        "key": "Storage Area Surface Line",
        "value_width": 16,
        "values_per_line": 2,
        "items_per_value": 2,
    },
    {
        "test_name": "StorageArea2DPoints",
        "file_path": "tests/data/common_blocks/block5.g01",
        "key": "Storage Area 2D Points",
        "value_width": 16,
        "values_per_line": 4,
        "items_per_value": 2,
    },
]


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


def run_block_tests():
    block_results = {}
    for test_config in BLOCK_TESTS:
        block_results[test_config["test_name"]] = test_block(test_config)
    return block_results
