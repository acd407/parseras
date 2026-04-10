import json
import os

from parseras import GeometryFile, BCLine, BCLineItem


def test_bcline_read_write():
    """测试BCLine的读写功能"""
    test_file = os.path.join(os.path.dirname(__file__), "data", "bcline.g01")
    output_file = os.path.join(os.path.dirname(__file__), "data", "bcline.output.g01")

    if not os.path.exists(test_file):
        print(f"测试文件不存在: {test_file}")
        return False

    geometry_file = GeometryFile(file_path=test_file)

    bc_lines = geometry_file.get_blocks_by_type(BCLine)
    if not bc_lines:
        print("未找到BCLine块")
        return False

    bc_line = bc_lines[0]
    bc_items = bc_line.value

    original_data = []
    for bc_item in bc_items:
        bc_data = {
            "name": bc_item["BC Line Name"].value if "BC Line Name" in bc_item else None,
            "storage_area": bc_item["BC Line Storage Area"].value if "BC Line Storage Area" in bc_item else None,
        }
        if "BC Line Arc" in bc_item:
            arc_data = bc_item["BC Line Arc"].value
            points = []
            data = arc_data.data
            for i in range(0, len(data), 2):
                if i + 1 < len(data):
                    x = data[i].value
                    y = data[i + 1].value
                    points.append([x, y])
            bc_data["points"] = points
        original_data.append(bc_data)

    generated_lines = geometry_file.generate()
    with open(output_file, "w") as f:
        f.writelines(generated_lines)

    with open(output_file, "r") as f:
        updated_content = f.readlines()

    updated_geometry_file = GeometryFile(lines=updated_content)
    updated_bc_lines = updated_geometry_file.get_blocks_by_type(BCLine)

    if len(bc_lines) != len(updated_bc_lines):
        print(f"BCLine数量不匹配: 原始={len(bc_lines)}, 更新后={len(updated_bc_lines)}")
        return False

    updated_bc_items = updated_bc_lines[0].value

    if len(original_data) != len(updated_bc_items):
        print(f"BCLineItem数量不匹配: 原始={len(original_data)}, 更新后={len(updated_bc_items)}")
        return False

    for i, orig_bc in enumerate(original_data):
        updated_bc = updated_bc_items[i]
        if orig_bc["name"] != updated_bc["BC Line Name"].value:
            print(f"BCLine名称不匹配: {orig_bc['name']} != {updated_bc['BC Line Name'].value}")
            return False
        if orig_bc["storage_area"] != updated_bc["BC Line Storage Area"].value:
            return False

        if "points" in orig_bc:
            updated_arc = updated_bc["BC Line Arc"].value
            updated_points = []
            for j in range(0, len(updated_arc.data), 2):
                if j + 1 < len(updated_arc.data):
                    x = updated_arc.data[j].value
                    y = updated_arc.data[j + 1].value
                    updated_points.append([x, y])
            if orig_bc["points"] != updated_points:
                print(f"BCLine点数据不匹配")
                return False

    return True


def run_bcline_tests():
    return test_bcline_read_write()