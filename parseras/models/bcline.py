"""
BCLineModel 类 - 提供BC Line的业务逻辑封装
"""

import json
from typing import List
from parseras.core.file import GeometryFile
from parseras.core.structures import BCLine, BCLineItem
from parseras.core.values import (
    DataBlockValue,
    DataValue,
    FloatValue,
    StringValue,
)


class BCLineModel:
    def __init__(self, geometry_file: GeometryFile):
        self.geometry_file = geometry_file
        self.bc_lines = geometry_file.get_blocks_by_type(BCLine)

    def _get_all_items(self) -> List[BCLineItem]:
        result = []
        for bl in self.bc_lines:
            for item in bl._value:
                if isinstance(item, BCLineItem):
                    result.append(item)
        return result

    def get_all_bc_lines(self) -> str:
        """返回所有BC Line的弧线点

        返回格式：
        {
            "status": "success",
            "data": {
                "BC Line 1": [[x1, y1], [x2, y2], ...],
                "BC Line 2": [[x1, y1], [x2, y2], ...]
            },
            "message": ""
        }
        """
        try:
            result = {}
            for item in self._get_all_items():
                if "BC Line Name" in item and "BC Line Arc" in item:
                    name = item["BC Line Name"].value
                    arc = item["BC Line Arc"].value
                    points = []
                    data = arc.data
                    for i in range(0, len(data), 2):
                        if i + 1 < len(data):
                            x = data[i].value
                            y = data[i + 1].value
                            points.append([x, y])
                    result[name] = points
            return json.dumps({"status": "success", "data": result, "message": ""}, indent=2)
        except Exception as e:
            return json.dumps({"status": "error", "data": {}, "message": str(e)}, indent=2)

    def get_bc_line_info(self, name: str) -> str:
        """返回特定BC Line的完整属性信息

        返回格式：
        {
            "status": "success",
            "data": {
                "BC Line Name": "BC Line 1",
                "BC Line Storage Area": "Storage Area 1",
                "BC Line Arc": [[x1, y1], [x2, y2], ...]
            },
            "message": ""
        }
        """
        try:
            target_item = None
            for item in self._get_all_items():
                if "BC Line Name" in item and item["BC Line Name"].value == name:
                    target_item = item
                    break

            if not target_item:
                return json.dumps(
                    {"status": "error", "data": {}, "message": f"BC Line with name '{name}' not found"},
                    indent=2,
                )

            result = {}

            if "BC Line Name" in target_item:
                result["BC Line Name"] = target_item["BC Line Name"].value

            if "BC Line Storage Area" in target_item:
                result["BC Line Storage Area"] = target_item["BC Line Storage Area"].value

            if "BC Line Arc" in target_item:
                arc = target_item["BC Line Arc"].value
                points = []
                data = arc.data
                for i in range(0, len(data), 2):
                    if i + 1 < len(data):
                        x = data[i].value
                        y = data[i + 1].value
                        points.append([x, y])
                result["BC Line Arc"] = points

            return json.dumps({"status": "success", "data": result, "message": ""}, indent=2)
        except Exception as e:
            return json.dumps({"status": "error", "data": {}, "message": str(e)}, indent=2)

    def update_or_create_bc_line(self, input_json: str) -> str:
        """更新或创建BC Line

        输入格式：
        {
            "BC Line Name": "BC Line 1",
            "BC Line Storage Area": "Storage Area 1",
            "BC Line Arc": [[x1, y1], [x2, y2], ...]
        }

        create模式：必须包含全部3个键
        update模式：可以缺少Storage Area或Arc

        返回格式：
        {
            "status": "success",
            "data": {},
            "message": "BC Line updated/created successfully"
        }
        """
        try:
            input_data = json.loads(input_json)
            name = input_data.get("BC Line Name")

            if not name:
                return json.dumps(
                    {"status": "error", "data": {}, "message": "BC Line Name is required"},
                    indent=2,
                )

            target_item = None
            target_bc_line = None
            for bc_line in self.bc_lines:
                for item in bc_line._value:
                    if isinstance(item, BCLineItem):
                        if "BC Line Name" in item and item["BC Line Name"].value == name:
                            target_item = item
                            target_bc_line = bc_line
                            break

            if target_item is None:
                if "BC Line Storage Area" not in input_data or "BC Line Arc" not in input_data:
                    return json.dumps(
                        {"status": "error", "data": {}, "message": "BC Line Storage Area and BC Line Arc are required for creation"},
                        indent=2,
                    )
                target_item = BCLineItem([])
                if target_bc_line is None:
                    target_bc_line = BCLine([])
                    self.bc_lines.append(target_bc_line)
                    self.geometry_file._blocks.append(target_bc_line)
                target_bc_line._value.append(target_item)
                message = "BC Line created successfully"
            else:
                message = "BC Line updated successfully"

            target_item["BC Line Name"] = StringValue(name)

            if "BC Line Storage Area" in input_data:
                target_item["BC Line Storage Area"] = StringValue(input_data["BC Line Storage Area"])

            if "BC Line Arc" in input_data:
                arc_points = input_data["BC Line Arc"]
                arc_data = []
                for point in arc_points:
                    arc_data.extend([FloatValue(str(point[0])), FloatValue(str(point[1]))])

                count = len(arc_points)
                arc_block = DataBlockValue(value_width=16, values_per_line=4, items_per_value=2)
                arc_value = DataValue(tuple(arc_data), 16, 4, 2, (str(count),), count)
                arc_block.value = arc_value
                target_item["BC Line Arc"] = arc_block

            return json.dumps({"status": "success", "data": {}, "message": message}, indent=2)
        except Exception as e:
            return json.dumps({"status": "error", "data": {}, "message": str(e)}, indent=2)

    def delete_bc_line(self, name: str) -> str:
        """删除BC Line

        返回格式：
        {
            "status": "success",
            "data": {},
            "message": "BC Line deleted successfully"
        }
        """
        try:
            target_item = None
            target_bc_line = None
            item_index = None

            for bc_line in self.bc_lines:
                for i, item in enumerate(bc_line._value):
                    if isinstance(item, BCLineItem):
                        if "BC Line Name" in item and item["BC Line Name"].value == name:
                            target_item = item
                            target_bc_line = bc_line
                            item_index = i
                            break

            if target_item is None:
                return json.dumps(
                    {"status": "error", "data": {}, "message": f"BC Line with name '{name}' not found"},
                    indent=2,
                )

            target_bc_line._value.pop(item_index)

            if len(target_bc_line._value) == 0:
                bc_line_index = None
                for i, block in enumerate(self.geometry_file._blocks):
                    if block == target_bc_line:
                        bc_line_index = i
                        break
                if bc_line_index is not None:
                    self.geometry_file._blocks.pop(bc_line_index)
                bc_line_list_index = None
                for i, bl in enumerate(self.bc_lines):
                    if bl == target_bc_line:
                        bc_line_list_index = i
                        break
                if bc_line_list_index is not None:
                    self.bc_lines.pop(bc_line_list_index)

            return json.dumps({"status": "success", "data": {}, "message": "BC Line deleted successfully"}, indent=2)
        except Exception as e:
            return json.dumps({"status": "error", "data": {}, "message": str(e)}, indent=2)