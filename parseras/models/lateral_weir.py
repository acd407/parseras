"""
LateralWeirModel 类 - 提供侧堰的业务逻辑封装
"""

import json
from typing import Optional
from shapely.geometry import LineString, Point
from parseras.core.file import GeometryFile
from parseras.core.structures import LateralWeir, StorageArea
from parseras.core.values import (
    CommaSeparatedValue,
    DataBlockValue,
    DataValue,
    FloatValue,
    StringValue,
)
from parseras.utils import generate_se_from_centerline, calculate_total_length


class LateralWeirModel:
    def __init__(self, geometry_file: GeometryFile):
        self.geometry_file = geometry_file
        self.lateral_weirs = geometry_file.get_blocks_by_type(LateralWeir)

    def get_all_lateral_weir_centerlines(self) -> str:
        """返回所有侧堰的中心线点

        返回格式：
        {
            "status": "success",
            "data": {
                "node_name1": [[x1, y1], [x2, y2], ...],
                "node_name2": [[x1, y1], [x2, y2], ...],
                ...
            },
            "message": ""
        }
        """
        try:
            result = {}
            for lw in self.lateral_weirs:
                if "Node Name" in lw and "Lateral Weir Centerline" in lw:
                    node_name = lw["Node Name"].value
                    centerline = lw["Lateral Weir Centerline"].value
                    points = []
                    data = centerline.data
                    for i in range(0, len(data), 2):
                        if i + 1 < len(data):
                            x = data[i].value
                            y = data[i + 1].value
                            points.append([x, y])
                    result[node_name] = points
            return json.dumps({"status": "success", "data": result, "message": ""}, indent=2)
        except Exception as e:
            return json.dumps({"status": "error", "data": {}, "message": str(e)}, indent=2)

    def get_lateral_weir_info(self, node_name: str) -> str:
        """返回特定侧堰的所有属性信息

        返回格式：
        {
            "status": "success",
            "data": {
                "Type RM Length L Ch R": ["6", "8926", "", "", ""],
                "Node Name": "bank",
                "Lateral Weir End": ["", "", "", "Perimeter 1"],
                "Lateral Weir Distance": 0.0,
                "Lateral Weir WD": 100.0,
                "Lateral Weir SE": [[0.0, 937.5], [24.5, 937.5], ...],
                "Lateral Weir Centerline": [[405847.800625798, 1802488.50152492], ...],
                // 其他可选属性
                "Node Last Edited Time": "...",
                "Lateral Weir Pos": 0,
                ...
            },
            "message": ""
        }
        """
        try:
            target_lw = None
            for lw in self.lateral_weirs:
                if "Node Name" in lw and lw["Node Name"].value == node_name:
                    target_lw = lw
                    break

            if not target_lw:
                return json.dumps(
                    {"status": "error", "data": {}, "message": f"Lateral weir with node name '{node_name}' not found"},
                    indent=2,
                )

            # 提取所有属性
            result = {}

            # 必需键
            if "Type RM Length L Ch R " in target_lw:
                type_rm = target_lw["Type RM Length L Ch R "].value
                result["Type RM Length L Ch R"] = [item.value for item in type_rm]

            if "Node Name" in target_lw:
                result["Node Name"] = target_lw["Node Name"].value

            if "Lateral Weir End" in target_lw:
                lw_end = target_lw["Lateral Weir End"].value
                result["Lateral Weir End"] = [item.value for item in lw_end]

            if "Lateral Weir Distance" in target_lw:
                result["Lateral Weir Distance"] = target_lw["Lateral Weir Distance"].value

            if "Lateral Weir WD" in target_lw:
                result["Lateral Weir WD"] = target_lw["Lateral Weir WD"].value

            # SE表
            if "Lateral Weir SE" in target_lw:
                se = target_lw["Lateral Weir SE"].value
                se_data = []
                data = se.data
                for i in range(0, len(data), 2):
                    if i + 1 < len(data):
                        dist = data[i].value
                        elev = data[i + 1].value
                        se_data.append([dist, elev])
                result["Lateral Weir SE"] = se_data

            # 中心线
            if "Lateral Weir Centerline" in target_lw:
                centerline = target_lw["Lateral Weir Centerline"].value
                centerline_data = []
                data = centerline.data
                for i in range(0, len(data), 2):
                    if i + 1 < len(data):
                        x = data[i].value
                        y = data[i + 1].value
                        centerline_data.append([x, y])
                result["Lateral Weir Centerline"] = centerline_data

            # 可选键
            optional_keys = [
                "Node Last Edited Time",
                "Lateral Weir Pos",
                "Lateral Weir TW Multiple XS",
                "Lateral Weir Coef",
                "LW OverFlow Method 2D",
                "LW OverFlow Use Velocity Into 2D",
                "Lateral Weir WSCriteria",
                "Lateral Weir Flap Gates",
                "Lateral Weir Hagers EQN",
                "Lateral Weir SS",
                "Lateral Weir Type",
                "Lateral Weir Connection Pos and Dist",
                "LW Div RC",
            ]

            for key in optional_keys:
                if key in target_lw:
                    value = target_lw[key]
                    if isinstance(value.value, tuple):
                        result[key] = [item.value for item in value.value]
                    else:
                        result[key] = value.value

            return json.dumps({"status": "success", "data": result, "message": ""}, indent=2)
        except Exception as e:
            return json.dumps({"status": "error", "data": {}, "message": str(e)}, indent=2)

    def _get_surface_line_coords(self, storage_area: StorageArea) -> Optional[list]:
        """从StorageArea块提取Storage Area Surface Line坐标列表，并确保闭合"""
        if "Storage Area Surface Line" not in storage_area:
            return None
        surface_line = storage_area["Storage Area Surface Line"].value
        if not hasattr(surface_line, 'data') or not surface_line.data:
            return None
        coords = []
        data = surface_line.data
        for i in range(0, len(data), 2):
            if i + 1 < len(data):
                coords.append((float(data[i].value), float(data[i + 1].value)))
        if len(coords) < 2:
            return None
        # 若首尾不相同，主动闭合（将首点追加到末尾）
        if coords[0] != coords[-1]:
            coords = coords + [coords[0]]
        return coords

    def _find_perimeter_intersection(self, endpoint: tuple, centerline_segment_start: tuple, centerline_segment_end: tuple, perimeter_coords: list) -> tuple:
        """从centerline端点，向perimeter做最近点投影，返回投影点坐标

        Args:
            endpoint: 中心线端点 (x, y)
            centerline_segment_start: 端点所在线段的起点 (x, y) — 仅用于兼容签名
            centerline_segment_end: 端点所在线段的终点 (x, y) — 仅用于兼容签名
            perimeter_coords: perimeter折线的坐标列表 [(x,y), ...]

        Returns:
            (x, y) 投影点坐标
        """
        from shapely.ops import nearest_points

        perimeter_line = LineString(perimeter_coords)
        np_pt = nearest_points(Point(endpoint), perimeter_line)[1]
        return (np_pt.x, np_pt.y)

    def _extract_polyline_xy(self, perimeter_coords: list, pt_x: tuple, pt_y: tuple, centerline: list) -> list:
        """从闭合的 perimeter 折线中提取 X 到 Y 之间的部分

        Perimeter 被 X、Y 切成两段，计算每段所有点到 centerline 的平均距离，
        选平均距离较小的那一段作为结果。返回的折线以 X 为起点、Y 为终点。

        Args:
            perimeter_coords: perimeter 折线坐标（闭合，首==尾）[(x,y), ...]
            pt_x: 点 X（centerline 端点 A 在 perimeter 上的最近投影）
            pt_y: 点 Y（centerline 端点 B 在 perimeter 上的最近投影）
            centerline: lateral weir centerline 坐标 [[x,y], ...]

        Returns:
            折线 XY 坐标列表（首=X，末=Y）

        Raises:
            ValueError: X、Y 落在同一边上无法区分
        """
        from shapely.geometry import Point, LineString
        from shapely.ops import nearest_points

        if len(perimeter_coords) < 2:
            raise ValueError("Perimeter line has fewer than 2 points")

        n = len(perimeter_coords)
        closed = perimeter_coords[0] == perimeter_coords[-1]

        def proj_t(pt, s, e):
            """pt 到线段 s->e 的投影参数 t（0≤t≤1）"""
            dx, dy = e[0] - s[0], e[1] - s[1]
            l2 = dx * dx + dy * dy
            if l2 < 1e-12:
                return 0.0
            return max(0.0, min(1.0, ((pt[0] - s[0]) * dx + (pt[1] - s[1]) * dy) / l2))

        def is_on_edge(pt, s, e, tol=1e-6):
            """判断 pt 是否在线段 s->e 上（含端点）"""
            t = proj_t(pt, s, e)
            proj = (s[0] + t * (e[0] - s[0]), s[1] + t * (e[1] - s[1]))
            return (pt[0] - proj[0]) ** 2 + (pt[1] - proj[1]) ** 2 < tol

        # 找 X、Y 所在的边索引
        idx_x = None
        for i in range(n - 1):
            if is_on_edge(pt_x, perimeter_coords[i], perimeter_coords[i + 1]):
                idx_x = i
                break
        idx_y = None
        for i in range(n - 1):
            if is_on_edge(pt_y, perimeter_coords[i], perimeter_coords[i + 1]):
                idx_y = i
                break

        if idx_x is None or idx_y is None:
            raise ValueError(f"X or Y not on perimeter edge (idx_x={idx_x}, idx_y={idx_y})")

        # 构建路径：将 X、Y 作为插值端点插入到顶点列表中
        # 处理闭合折线的去重（末尾=首点）
        unique_coords = perimeter_coords[:-1] if closed else perimeter_coords
        n_u = len(unique_coords)

        seg_x_s, seg_x_e = unique_coords[idx_x], unique_coords[(idx_x + 1) % n_u]
        seg_y_s, seg_y_e = unique_coords[idx_y], unique_coords[(idx_y + 1) % n_u]
        tx = proj_t(pt_x, seg_x_s, seg_x_e)
        ty = proj_t(pt_y, seg_y_s, seg_y_e)
        x_interp = (seg_x_s[0] + tx * (seg_x_e[0] - seg_x_s[0]),
                     seg_x_s[1] + tx * (seg_x_e[1] - seg_x_s[1]))
        y_interp = (seg_y_s[0] + ty * (seg_y_e[0] - seg_y_s[0]),
                     seg_y_s[1] + ty * (seg_y_e[1] - seg_y_s[1]))

        def build_path(start_i, end_i, start_pt, end_pt):
            """沿折线从 start_i 边前进到 end_i 边（含两端插值点）。"""
            path = [start_pt]
            i = (start_i + 1) % n_u
            # 当 start_i == end_i 时，走完整一圈回到同一条边
            while True:
                path.append(unique_coords[i])
                if i == end_i:
                    break
                i = (i + 1) % n_u
            path.append(end_pt)
            return path

        if idx_x == idx_y:
            # 同一条边：X→Y 沿该边的短路径 vs 绕 perimeter 的长路径
            t1, t2 = min(tx, ty), max(tx, ty)
            pt1 = (seg_x_s[0] + t1 * (seg_x_e[0] - seg_x_s[0]),
                   seg_x_s[1] + t1 * (seg_x_e[1] - seg_x_s[1]))
            pt2 = (seg_x_s[0] + t2 * (seg_x_e[0] - seg_x_s[0]),
                   seg_x_s[1] + t2 * (seg_x_e[1] - seg_x_s[1]))
            # 短路径：同一边上 X↔Y 直连（保证以 X 为起点）
            if x_interp == pt1:
                path1 = [pt1, pt2]
            else:
                path1 = [pt2, pt1]
            # 长路径：从另一个端点沿折线绕一圈回来
            path2 = build_path(idx_x, idx_x, path1[1], path1[0])
        else:
            path1 = build_path(idx_x, idx_y, x_interp, y_interp)
            path2 = build_path(idx_y, idx_x, y_interp, x_interp)

        # 用 centerline 计算平均距离选路径
        cl_line = LineString(centerline)

        def avg_dist(path):
            if len(path) < 2:
                return float("inf")
            total = sum(Point(p).distance(cl_line) for p in path)
            return total / len(path)

        return path1 if avg_dist(path1) <= avg_dist(path2) else path2

    def update_or_create_lateral_weir(self, input_json: str, tif_path: Optional[str] = None) -> str:
        """更新或创建侧堰

        输入格式：
        {
            "Node Name": "bank",           // 必需，用于定位
            "Station": 8926,               // 必需（创建时）
            "Lateral Weir End Parameter": "Perimeter 1",  // 必需（创建时）
            "Lateral Weir Distance": 0,    // 必需（创建时）
            "Lateral Weir WD": 100,        // 必需（创建时）
            "Lateral Weir Centerline": [[x1, y1], [x2, y2], ...]  // 必需（创建时）
        }

        参数：
        - input_json: 包含侧堰信息的JSON字符串
        - tif_path: 可选，DEM数据文件路径，用于生成Lateral Weir SE

        返回格式：
        {
            "status": "success",
            "data": {},
            "message": "Lateral weir updated/created successfully"
        }
        """
        try:
            input_data = json.loads(input_json)
            node_name = input_data.get("Node Name")

            if not node_name:
                return json.dumps(
                    {"status": "error", "data": {}, "message": "Missing required field 'Node Name'"},
                    indent=2,
                )

            target_lw = None
            for lw in self.lateral_weirs:
                if "Node Name" in lw and lw["Node Name"].value == node_name:
                    target_lw = lw
                    break

            is_create = target_lw is None

            station = input_data.get("Station")
            lw_end_param = input_data.get("Lateral Weir End Parameter")
            lw_distance = input_data.get("Lateral Weir Distance")
            lw_wd = input_data.get("Lateral Weir WD")
            lw_centerline = input_data.get("Lateral Weir Centerline")

            if is_create:
                missing_fields = []
                if station is None:
                    missing_fields.append("Station")
                if lw_end_param is None:
                    missing_fields.append("Lateral Weir End Parameter")
                if lw_distance is None:
                    missing_fields.append("Lateral Weir Distance")
                if lw_wd is None:
                    missing_fields.append("Lateral Weir WD")
                if not lw_centerline:
                    missing_fields.append("Lateral Weir Centerline")

                if missing_fields:
                    return json.dumps(
                        {"status": "error", "data": {}, "message": f"Missing required fields for create: {missing_fields}"},
                        indent=2,
                    )

                target_lw = LateralWeir([])
                self.lateral_weirs.append(target_lw)
                self.geometry_file._blocks.append(target_lw)

            if station is not None:
                type_rm_str = f"6,{station},,,"
                target_lw["Type RM Length L Ch R "] = CommaSeparatedValue(type_rm_str, element_type=StringValue)
                if station > 0:
                    target_lw.order = 30 + 1 / station

            if node_name is not None:
                target_lw["Node Name"] = StringValue(node_name)

            if lw_end_param is not None:
                lw_end_str = f",,,{lw_end_param}"
                target_lw["Lateral Weir End"] = CommaSeparatedValue(lw_end_str, element_type=StringValue)

            if lw_distance is not None:
                target_lw["Lateral Weir Distance"] = FloatValue(str(lw_distance))

            if lw_wd is not None:
                target_lw["Lateral Weir WD"] = FloatValue(str(lw_wd))

            if lw_centerline:
                centerline_data = []
                for point in lw_centerline:
                    centerline_data.extend([FloatValue(str(point[0])), FloatValue(str(point[1]))])

                count = len(lw_centerline)
                centerline_block = DataBlockValue(value_width=16, values_per_line=4, items_per_value=2)
                centerline_value = DataValue(tuple(centerline_data), 16, 4, 2, (str(count),), count)
                centerline_block.value = centerline_value
                target_lw["Lateral Weir Centerline"] = centerline_block

                # 确定传入generate_se_from_centerline的折线
                se_input_coords = lw_centerline  # 默认使用lw_centerline

                if lw_end_param:
                    # 查找lw_end_param对应的StorageArea（2D Flow Area）
                    target_sa = None
                    for sa in self.geometry_file.get_blocks_by_type(StorageArea):
                        if "Storage Area" in sa:
                            sa_value = sa["Storage Area"].value
                            if sa_value and len(sa_value) > 0 and sa_value[0].value == lw_end_param:
                                target_sa = sa
                                break

                    if target_sa is None:
                        return json.dumps(
                            {"status": "error", "data": {}, "message": f"Storage area '{lw_end_param}' not found for Lateral Weir End Parameter"},
                            indent=2,
                        )

                    perimeter_coords = self._get_surface_line_coords(target_sa)
                    if not perimeter_coords:
                        return json.dumps(
                            {"status": "error", "data": {}, "message": f"Storage area '{lw_end_param}' has no valid Surface Line"},
                            indent=2,
                        )

                    if len(lw_centerline) < 2:
                        return json.dumps(
                            {"status": "error", "data": {}, "message": "Lateral Weir Centerline must have at least 2 points"},
                            indent=2,
                        )

                    # 点A：lw_centerline第一个端点
                    pt_a = (float(lw_centerline[0][0]), float(lw_centerline[0][1]))
                    # 点A所在的线段：第一个点与其下一个点
                    seg_a_start = pt_a
                    seg_a_end = (float(lw_centerline[1][0]), float(lw_centerline[1][1]))
                    pt_x = self._find_perimeter_intersection(pt_a, seg_a_start, seg_a_end, perimeter_coords)

                    # 点B：lw_centerline另一个端点
                    pt_b = (float(lw_centerline[-1][0]), float(lw_centerline[-1][1]))
                    seg_b_start = (float(lw_centerline[-2][0]), float(lw_centerline[-2][1]))
                    seg_b_end = pt_b
                    pt_y = self._find_perimeter_intersection(pt_b, seg_b_start, seg_b_end, perimeter_coords)

                    # 从perimeter折线提取点X、Y之间的部分
                    se_input_coords = self._extract_polyline_xy(perimeter_coords, pt_x, pt_y, lw_centerline)

                se_table = generate_se_from_centerline(se_input_coords, tif_path)

                # 当用了 perimeter 折线时，按 centerline 长度比例缩放距离，使 ratio = 100%
                if lw_end_param:
                    xy_len = calculate_total_length(se_input_coords)
                    cl_len = calculate_total_length(lw_centerline)
                    if xy_len > 0:
                        scale = cl_len / xy_len
                        se_table = [[d * scale, e] for d, e in se_table]

                se_data = []
                for dist, elev in se_table:
                    se_data.extend([FloatValue(str(dist)), FloatValue(str(elev))])

                count = len(se_table)
                se_block = DataBlockValue(value_width=8, values_per_line=10, items_per_value=2)
                se_value = DataValue(tuple(se_data), 8, 10, 2, (str(count),), count)
                se_block.value = se_value
                target_lw["Lateral Weir SE"] = se_block

            message = "Lateral weir created successfully" if is_create else "Lateral weir updated successfully"
            return json.dumps({"status": "success", "data": {}, "message": message}, indent=2)

        except Exception as e:
            import traceback
            return json.dumps({"status": "error", "data": {}, "message": str(e), "trace": traceback.format_exc()}, indent=2)

    def delete_lateral_weir(self, node_name: str) -> str:
        """删除侧堰

        返回格式：
        {
            "status": "success",
            "data": {},
            "message": "Lateral weir deleted successfully"
        }
        """
        try:
            target_index = None
            for i, lw in enumerate(self.lateral_weirs):
                if "Node Name" in lw and lw["Node Name"].value == node_name:
                    target_index = i
                    break

            if target_index is None:
                return json.dumps(
                    {"status": "error", "data": {}, "message": f"Lateral weir with node name '{node_name}' not found"},
                    indent=2,
                )

            self.lateral_weirs.pop(target_index)

            block_index = None
            for i, block in enumerate(self.geometry_file._blocks):
                if isinstance(block, LateralWeir) and "Node Name" in block:
                    if block["Node Name"].value == node_name:
                        block_index = i
                        break

            if block_index is not None:
                self.geometry_file._blocks.pop(block_index)

            return json.dumps({"status": "success", "data": {}, "message": "Lateral weir deleted successfully"}, indent=2)
        except Exception as e:
            return json.dumps({"status": "error", "data": {}, "message": str(e)}, indent=2)
