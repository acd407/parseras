"""
BreakLineModel 类 - 提供断线的业务逻辑封装
"""

import json
from typing import List
from parseras.core.file import GeometryFile
from parseras.core.structures import BreakLine, SingleBreakLine, BreakLineMeta
from parseras.core.values import (
    DataBlockValue,
    DataValue,
    IntValue,
    StringValue,
)


class BreakLineModel:
    def __init__(self, geometry_file: GeometryFile):
        self.geometry_file = geometry_file
        self.breaklines = geometry_file.get_blocks_by_type(BreakLine)

    def _get_all_single_breaklines(self) -> List[SingleBreakLine]:
        result = []
        for bl in self.breaklines:
            for item in bl._value:
                if isinstance(item, SingleBreakLine):
                    result.append(item)
        return result

    def get_all_breaklines(self) -> str:
        """返回所有断线的折线点

        返回格式：
        {
            "status": "success",
            "data": {
                "Breakline 1": [[x1, y1], [x2, y2], ...],
                "breakline2": [[x1, y1], [x2, y2], ...]
            },
            "message": ""
        }
        """
        try:
            result = {}
            for sbl in self._get_all_single_breaklines():
                if "BreakLine Name" in sbl and "BreakLine Polyline" in sbl:
                    name = sbl["BreakLine Name"].value
                    polyline = sbl["BreakLine Polyline"].value
                    points = []
                    data = polyline.data
                    for i in range(0, len(data), 2):
                        if i + 1 < len(data):
                            x = data[i].value
                            y = data[i + 1].value
                            points.append([x, y])
                    result[name] = points
            return json.dumps({"status": "success", "data": result, "message": ""}, indent=2)
        except Exception as e:
            return json.dumps({"status": "error", "data": {}, "message": str(e)}, indent=2)

    def get_single_breakline_info(self, name: str) -> str:
        """返回特定断线的所有属性信息

        返回格式：
        {
            "status": "success",
            "data": {
                "BreakLine Name": "breakline2",
                "BreakLine Polyline": [[x1, y1], [x2, y2], ...],
                "BreakLine CellSize Min": "",
                "BreakLine CellSize Max": "",
                "BreakLine Near Repeats": 1,
                "BreakLine Protection Radius": 0
            },
            "message": ""
        }
        """
        try:
            target_sbl = None
            for sbl in self._get_all_single_breaklines():
                if "BreakLine Name" in sbl and sbl["BreakLine Name"].value == name:
                    target_sbl = sbl
                    break

            if not target_sbl:
                return json.dumps(
                    {"status": "error", "data": {}, "message": f"BreakLine with name '{name}' not found"},
                    indent=2,
                )

            result = {}

            if "BreakLine Name" in target_sbl:
                result["BreakLine Name"] = target_sbl["BreakLine Name"].value

            if "BreakLine Polyline" in target_sbl:
                polyline = target_sbl["BreakLine Polyline"].value
                points = []
                data = polyline.data
                for i in range(0, len(data), 2):
                    if i + 1 < len(data):
                        x = data[i].value
                        y = data[i + 1].value
                        points.append([x, y])
                result["BreakLine Polyline"] = points

            if "BreakLine CellSize Min" in target_sbl:
                val = target_sbl["BreakLine CellSize Min"].value
                if val:
                    result["BreakLine CellSize Min"] = val

            if "BreakLine CellSize Max" in target_sbl:
                val = target_sbl["BreakLine CellSize Max"].value
                if val:
                    result["BreakLine CellSize Max"] = val

            if "BreakLine Near Repeats" in target_sbl:
                result["BreakLine Near Repeats"] = target_sbl["BreakLine Near Repeats"].value

            if "BreakLine Protection Radius" in target_sbl:
                result["BreakLine Protection Radius"] = target_sbl["BreakLine Protection Radius"].value

            return json.dumps({"status": "success", "data": result, "message": ""}, indent=2)
        except Exception as e:
            return json.dumps({"status": "error", "data": {}, "message": str(e)}, indent=2)

    def get_breakline_meta(self) -> str:
        """返回LCMann元数据

        返回格式：
        {
            "status": "success",
            "data": {
                "LCMann Time": "Dec/30/1899 00:00:00",
                "LCMann Region Time": "Dec/30/1899 00:00:00",
                "LCMann Table": "0",
                "Chan Stop Cuts": -1
            },
            "message": ""
        }
        """
        try:
            result = {}
            for bl in self.breaklines:
                for item in bl._value:
                    if isinstance(item, BreakLineMeta):
                        if "LCMann Time" in item:
                            val = item["LCMann Time"].value
                            if val:
                                result["LCMann Time"] = val

                        if "LCMann Region Time" in item:
                            val = item["LCMann Region Time"].value
                            if val:
                                result["LCMann Region Time"] = val

                        if "LCMann Table" in item:
                            val = item["LCMann Table"].value
                            if val:
                                result["LCMann Table"] = val

                        if "Chan Stop Cuts" in item:
                            result["Chan Stop Cuts"] = item["Chan Stop Cuts"].value

            return json.dumps({"status": "success", "data": result, "message": ""}, indent=2)
        except Exception as e:
            return json.dumps({"status": "error", "data": {}, "message": str(e)}, indent=2)

    def update_or_create_single_breakline(self, input_json: str) -> str:
        """更新或创建单个断线

        输入格式：
        {
            "BreakLine Name": "new_breakline",
            "BreakLine Polyline": [[x1, y1], [x2, y2], ...],
            "BreakLine CellSize Min": "",
            "BreakLine CellSize Max": "",
            "BreakLine Near Repeats": 0,
            "BreakLine Protection Radius": -1
        }

        返回格式：
        {
            "status": "success",
            "data": {},
            "message": "BreakLine updated/created successfully"
        }
        """
        try:
            input_data = json.loads(input_json)
            name = input_data.get("BreakLine Name")
            polyline = input_data.get("BreakLine Polyline", [])

            if not name or not polyline:
                return json.dumps(
                    {"status": "error", "data": {}, "message": "BreakLine Name and BreakLine Polyline are required"},
                    indent=2,
                )

            target_sbl = None
            target_bl = None
            for bl in self.breaklines:
                for item in bl._value:
                    if isinstance(item, SingleBreakLine):
                        if "BreakLine Name" in item and item["BreakLine Name"].value == name:
                            target_sbl = item
                            target_bl = bl
                            break

            if target_sbl is None:
                target_sbl = SingleBreakLine([])

                if target_bl is None:
                    target_bl = BreakLine([])
                    self.breaklines.append(target_bl)
                    self.geometry_file._blocks.append(target_bl)

                target_bl._value.append(target_sbl)
                message = "BreakLine created successfully"
            else:
                message = "BreakLine updated successfully"

            polyline_data = []
            for point in polyline:
                polyline_data.extend([StringValue(str(point[0])), StringValue(str(point[1]))])

            count = len(polyline)
            polyline_block = DataBlockValue(value_width=16, values_per_line=4, items_per_value=2)
            polyline_value = DataValue(
                tuple(polyline_data), 16, 4, 2, (str(count),), count
            )
            polyline_block.value = polyline_value
            target_sbl["BreakLine Polyline"] = polyline_block

            target_sbl["BreakLine Name"] = StringValue(name)

            if "BreakLine CellSize Min" in input_data:
                val = input_data["BreakLine CellSize Min"]
                target_sbl["BreakLine CellSize Min"] = StringValue(val if val else "")

            if "BreakLine CellSize Max" in input_data:
                val = input_data["BreakLine CellSize Max"]
                target_sbl["BreakLine CellSize Max"] = StringValue(val if val else "")

            if "BreakLine Near Repeats" in input_data:
                target_sbl["BreakLine Near Repeats"] = IntValue(str(input_data["BreakLine Near Repeats"]))

            if "BreakLine Protection Radius" in input_data:
                target_sbl["BreakLine Protection Radius"] = IntValue(str(input_data["BreakLine Protection Radius"]))

            return json.dumps({"status": "success", "data": {}, "message": message}, indent=2)
        except Exception as e:
            return json.dumps({"status": "error", "data": {}, "message": str(e)}, indent=2)

    def delete_single_breakline(self, name: str) -> str:
        """删除单个断线

        输入：name - BreakLine Name

        返回格式：
        {
            "status": "success",
            "data": {},
            "message": "BreakLine deleted successfully"
        }
        """
        try:
            target_sbl = None
            target_bl = None
            for bl in self.breaklines:
                for item in bl._value:
                    if isinstance(item, SingleBreakLine):
                        if "BreakLine Name" in item and item["BreakLine Name"].value == name:
                            target_sbl = item
                            target_bl = bl
                            break

            if target_sbl is None:
                return json.dumps(
                    {"status": "error", "data": {}, "message": f"BreakLine with name '{name}' not found"},
                    indent=2,
                )

            target_bl._value.remove(target_sbl)

            remaining_items = [item for item in target_bl._value if isinstance(item, SingleBreakLine)]
            if not remaining_items:
                self.breaklines.remove(target_bl)
                self.geometry_file._blocks.remove(target_bl)

            return json.dumps({"status": "success", "data": {}, "message": "BreakLine deleted successfully"}, indent=2)
        except Exception as e:
            return json.dumps({"status": "error", "data": {}, "message": str(e)}, indent=2)