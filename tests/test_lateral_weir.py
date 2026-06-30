import json
import os

from parseras.core.file import GeometryFile
from parseras.models.lateral_weir import LateralWeirModel


def test_lateral_weir_read_write():
    """测试侧堰的读写功能：保存侧堰数据，删除后重建，验证数据一致性"""
    test_file = os.path.join(os.path.dirname(__file__), "data", "leak.g01")
    output_file = os.path.join(
        os.path.dirname(__file__), "data", "leak.lateral_weir.output.g01"
    )

    if not os.path.exists(test_file):
        print(f"测试文件不存在: {test_file}")
        return False

    lines = open(test_file).readlines()

    geometry_file = GeometryFile(lines=lines)
    lateral_weir_model = LateralWeirModel(geometry_file)

    node_name = "bank"

    lateral_weir_info = lateral_weir_model.get_lateral_weir_info(node_name)
    lateral_weir_info_data = json.loads(lateral_weir_info)

    if lateral_weir_info_data.get("status") != "success":
        print(f"获取侧堰信息失败: {lateral_weir_info_data.get('message')}")
        return False

    lateral_weir_data = lateral_weir_info_data.get("data", {})

    type_rm = lateral_weir_data.get("Type RM Length L Ch R", [])
    station = float(type_rm[1]) if len(type_rm) >= 2 else None

    centerline = lateral_weir_data.get("Lateral Weir Centerline", [])
    lw_end_param = lateral_weir_data.get(
        "Lateral Weir End", [None, None, None, "Perimeter 1"]
    )[3]
    lw_distance = lateral_weir_data.get("Lateral Weir Distance", 0)
    lw_wd = lateral_weir_data.get("Lateral Weir WD", 100)

    if not centerline or station is None:
        return False

    for i, block in enumerate(geometry_file.get_blocks()):
        if hasattr(block, "_key_value_pairs") and "Node Name" in block._key_value_pairs:
            if block["Node Name"].value == node_name:
                geometry_file.get_blocks().pop(i)
                for j, lw in enumerate(lateral_weir_model.lateral_weirs):
                    if lw == block:
                        lateral_weir_model.lateral_weirs.pop(j)
                        break
                break

    input_json = json.dumps(
        {
            "Node Name": node_name,
            "Station": station,
            "Lateral Weir End Parameter": lw_end_param,
            "Lateral Weir Distance": lw_distance,
            "Lateral Weir WD": lw_wd,
            "Lateral Weir Centerline": centerline,
        }
    )

    tif_path = os.path.join(os.path.dirname(__file__), "data", "leak.tif")
    lateral_weir_model.update_or_create_lateral_weir(input_json, tif_path)

    updated_lines = geometry_file.generate()
    with open(output_file, "w") as f:
        f.writelines(updated_lines)

    with open(output_file, "r") as f:
        updated_content = f.readlines()

    updated_geometry_file = GeometryFile(lines=updated_content)
    updated_lateral_weir_model = LateralWeirModel(updated_geometry_file)

    updated_lateral_weir_info = updated_lateral_weir_model.get_lateral_weir_info(
        node_name
    )
    updated_lateral_weir_info_data = json.loads(updated_lateral_weir_info)

    if updated_lateral_weir_info_data.get("status") != "success":
        return False

    updated_lateral_weir_data = updated_lateral_weir_info_data.get("data", {})

    updated_centerline = updated_lateral_weir_data.get("Lateral Weir Centerline", [])

    if centerline != updated_centerline:
        return False

    updated_type_rm = updated_lateral_weir_data.get("Type RM Length L Ch R", [])
    updated_station = float(updated_type_rm[1]) if len(updated_type_rm) >= 2 else None

    if station != updated_station:
        return False

    return True
