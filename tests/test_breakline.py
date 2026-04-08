import os
import json
from parseras import GeometryFile, BreakLineModel


def test_breakline_modification() -> bool:
    """测试断线修改功能"""
    test_file = "tests/data/breakline.g01"
    output_file = "tests/data/breakline.output.g01"

    if not os.path.exists(test_file):
        print(f"Test file not found: {test_file}")
        return False

    g_file = GeometryFile(file_path=test_file)
    bl_model = BreakLineModel(g_file)

    all_breaklines = bl_model.get_all_breaklines()
    all_breaklines_data = json.loads(all_breaklines)

    if all_breaklines_data.get("status") != "success" or not all_breaklines_data.get("data"):
        print("Failed to get breaklines")
        return False

    original_data = {}
    for name, points in all_breaklines_data["data"].items():
        original_data[name] = points

    for name, points in all_breaklines_data["data"].items():
        modified_points = []
        for point in points:
            x, y = point
            modified_points.append([float(x) + 10, float(y) - 10])

        update_data = {"BreakLine Name": name, "BreakLine Polyline": modified_points}
        bl_model.update_or_create_single_breakline(json.dumps(update_data))

    new_bl_data = {
        "BreakLine Name": "new_breakline_test",
        "BreakLine Polyline": [[1, 2], [3, 4], [5, 6]],
        "BreakLine Near Repeats": 1,
    }
    bl_model.update_or_create_single_breakline(json.dumps(new_bl_data))

    verify_result = bl_model.get_all_breaklines()
    verify_data = json.loads(verify_result)

    if not verify_data["data"].get("new_breakline_test"):
        print("Failed to create new breakline")
        return False

    bl_model.delete_single_breakline("new_breakline_test")

    after_delete_result = bl_model.get_all_breaklines()
    after_delete_data = json.loads(after_delete_result)

    if after_delete_data["data"].get("new_breakline_test"):
        print("Failed to delete breakline")
        return False

    generated_lines = g_file.generate()
    with open(output_file, "w") as f:
        f.writelines(generated_lines)

    template_file = "tests/data/breakline.template.g01"
    if os.path.exists(template_file):
        with open(template_file, "r") as f:
            template_content = f.read()

        with open(output_file, "r") as f:
            output_content = f.read()

        return template_content == output_content
    else:
        return False