from parseras import GeometryFile


FULL_FILE_TESTS = [
    {
        "test_name": "all.g01",
        "file_path": "tests/data/all.g01",
    },
    {
        "test_name": "leak.g01",
        "file_path": "tests/data/leak.g01",
    },
    {
        "test_name": "thin.g01",
        "file_path": "tests/data/thin.g01",
    },
    {
        "test_name": "Muncie.g01",
        "file_path": "tests/data/Muncie.g01",
    },
]


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


def run_full_file_tests():
    full_file_results = {}
    for test_config in FULL_FILE_TESTS:
        full_file_results[test_config["test_name"]] = test_full_file(test_config["file_path"])
    return full_file_results
