import os
import json
from parseras import GeometryFile, RiverModel


def test_river_modification() -> bool:
    """测试河流修改功能"""
    g_file = GeometryFile(file_path="tests/data/all.g01")

    river_model = RiverModel(g_file)

    river_data_json = river_model.get_all_river_reach_lines()
    river_data = json.loads(river_data_json)

    if river_data.get("status") == "success" and river_data.get("data"):
        # 遍历所有河流和河段
        for river_name, reaches in river_data["data"].items():
            for reach_name, points in reaches.items():
                # 修改每个点的坐标：x加10，y减10
                modified_points = []
                for point in points:
                    x, y = point
                    modified_points.append([x + 10, y - 10])

                # 更新河段
                update_data = {"River": river_name, "Reach": reach_name, "Reach XY": modified_points}
                river_model.update_or_create_river_reach(json.dumps(update_data))

    # 生成新的g01文件
    output_file = "tests/data/all.river.output.g01"
    generated_lines = g_file.generate()
    with open(output_file, "w") as f:
        f.writelines(generated_lines)

    # 检查是否存在模板文件
    template_file = "tests/data/all.river.template.g01"
    if os.path.exists(template_file):
        with open(template_file, "r") as f:
            template_content = f.read()

        with open(output_file, "r") as f:
            output_content = f.read()

        return template_content == output_content
    else:
        return False
