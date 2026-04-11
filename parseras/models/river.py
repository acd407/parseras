from typing import Dict, List, Tuple
import json
from parseras.core.file import GeometryFile
from parseras.core.structures import River
from parseras.core.values import CommaSeparatedValue, DataBlockValue, SpaceSeparatedValue, IntValue, StringValue


class RiverModel:
    def __init__(self, geometry_file: GeometryFile):
        self.geometry_file = geometry_file
        self.rivers = geometry_file.get_blocks_by_type(River)

    def get_all_river_reach_lines(self) -> str:
        """返回所有河段的折线点

        返回格式：
        {
            "status": "success",
            "data": {
                "River1": {
                    "Reach1": [[x1, y1], [x2, y2], ...],
                    "Reach2": [[x1, y1], [x2, y2], ...],
                    ...
                },
                "River2": {
                    "Reach1": [[x1, y1], [x2, y2], ...],
                    ...
                },
                ...
            },
            "message": ""
        }
        """
        try:
            result = {}
            for river in self.rivers:
                if "River Reach" in river and "Reach XY" in river:
                    # 提取河流和河段名称
                    river_reach = river["River Reach"].value
                    if len(river_reach) >= 2:
                        river_name = river_reach[0].value
                        reach_name = river_reach[1].value
                        # 提取折线点
                        reach_xy = river["Reach XY"].value
                        points = []
                        data = reach_xy.data
                        for i in range(0, len(data), 2):
                            if i + 1 < len(data):
                                x = data[i].value
                                y = data[i + 1].value
                                points.append([x, y])
                        # 按照河流名称和河段名称组织数据
                        if river_name not in result:
                            result[river_name] = {}
                        result[river_name][reach_name] = points
            return json.dumps({"status": "success", "data": result, "message": ""}, indent=2)
        except Exception as e:
            return json.dumps({"status": "error", "data": {}, "message": str(e)}, indent=2)

    def update_or_create_river_reach(self, input_json: str) -> str:
        """修改或创建河段

        输入格式：
        {
            "River": "name1",
            "Reach": "name2",
            "Reach XY": [[x1, y1], [x2, y2], ...]
        }

        返回格式：
        {
            "status": "success",
            "data": {},
            "message": "River reach updated/created successfully"
        }
        """
        try:
            # 解析输入JSON
            input_data = json.loads(input_json)
            river_name = input_data.get("River")
            reach_name = input_data.get("Reach")
            reach_xy = input_data.get("Reach XY", [])

            if not river_name or not reach_name or not reach_xy:
                return json.dumps({"status": "error", "data": {}, "message": "Missing required fields"}, indent=2)

            # 计算中间点作为Rch Text X Y
            if len(reach_xy) > 0:
                middle_index = len(reach_xy) // 2
                middle_point = reach_xy[middle_index]
            else:
                middle_point = [0, 0]

            # 为DataBlockValue创建正确的格式
            reach_xy_str = f"{len(reach_xy)}"
            if reach_xy:
                reach_xy_str += "\n"
                for i, point in enumerate(reach_xy):
                    if i % 2 == 0 and i > 0:
                        reach_xy_str += "\n"
                    reach_xy_str += f"{point[0]:16.6f}{point[1]:16.6f}"

            # 查找并删除旧的River-Reach
            old_river_index = None
            for i, block in enumerate(self.geometry_file._blocks):
                if isinstance(block, River) and "River Reach" in block:
                    river_reach = block["River Reach"].value
                    if len(river_reach) >= 2:
                        if river_reach[0].value == river_name and river_reach[1].value == reach_name:
                            old_river_index = i
                            break

            if old_river_index is not None:
                del self.geometry_file._blocks[old_river_index]

            # 创建新河段
            new_river = River([])
            new_river["River Reach"] = CommaSeparatedValue(f"{river_name},{reach_name}")
            new_river["Reach XY"] = DataBlockValue(reach_xy_str, value_width=16, values_per_line=4, items_per_value=2)
            new_river["Rch Text X Y"] = CommaSeparatedValue(
                f"{middle_point[0]},{middle_point[1]}", element_type=StringValue
            )
            new_river["Reverse River Text"] = IntValue("0")

            # 添加到geometry_file
            self.geometry_file._blocks.append(new_river)

            # 更新rivers列表
            self.rivers = self.geometry_file.get_blocks_by_type(River)

            return json.dumps(
                {"status": "success", "data": {}, "message": "River reach updated/created successfully"}, indent=2
            )
        except Exception as e:
            return json.dumps({"status": "error", "data": {}, "message": str(e)}, indent=2)

    def delete_river_reach(self, input_json: str) -> str:
        """删除河段

        输入格式：
        {
            "River": "name1",
            "Reach": "name2"
        }

        返回格式：
        {
            "status": "success",
            "data": {},
            "message": "River reach deleted successfully"
        }
        """
        try:
            input_data = json.loads(input_json)
            river_name = input_data.get("River")
            reach_name = input_data.get("Reach")

            if not river_name or not reach_name:
                return json.dumps({"status": "error", "data": {}, "message": "Missing required fields"}, indent=2)

            river_index = None
            for i, block in enumerate(self.geometry_file._blocks):
                if isinstance(block, River) and "River Reach" in block:
                    river_reach = block["River Reach"].value
                    if len(river_reach) >= 2:
                        if river_reach[0].value == river_name and river_reach[1].value == reach_name:
                            river_index = i
                            break

            if river_index is None:
                return json.dumps(
                    {"status": "error", "data": {}, "message": f"River reach {river_name}/{reach_name} not found"},
                    indent=2,
                )

            del self.geometry_file._blocks[river_index]
            self.rivers = self.geometry_file.get_blocks_by_type(River)

            return json.dumps(
                {"status": "success", "data": {}, "message": "River reach deleted successfully"}, indent=2
            )
        except Exception as e:
            return json.dumps({"status": "error", "data": {}, "message": str(e)}, indent=2)
