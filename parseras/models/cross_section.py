import json
from parseras.core.file import GeometryFile
from parseras.core.structures import CrossSection
from typing import Optional


class CrossSectionModel:
    def __init__(self, geometry_file: GeometryFile):
        self.geometry_file = geometry_file
        self.cross_sections = geometry_file.get_blocks_by_type(CrossSection)

    def get_all_cross_section_lines(self) -> str:
        """返回所有断面的折线点数值，也就是XS GIS Cut Line对应的点

        返回格式：
        {
            "status": "success",
            "data": {
                "station1": [[x1, y1], [x2, y2], ...],
                "station2": [[x1, y1], [x2, y2], ...],
                ...
            },
            "message": ""
        }
        """
        try:
            result = {}
            for xs in self.cross_sections:
                if "Type RM Length L Ch R " in xs and "XS GIS Cut Line" in xs:
                    # 提取断面在河流上的Station
                    type_rm = xs["Type RM Length L Ch R "].value
                    if len(type_rm) >= 2:
                        station = float(type_rm[1].value)
                        # 提取折线点
                        cut_line = xs["XS GIS Cut Line"].value
                        points = []
                        data = cut_line.data
                        for i in range(0, len(data), 2):
                            if i + 1 < len(data):
                                x = data[i].value
                                y = data[i + 1].value
                                points.append([x, y])
                        result[station] = points
            return json.dumps({"status": "success", "data": result, "message": ""}, indent=2)
        except Exception as e:
            return json.dumps({"status": "error", "data": {}, "message": str(e)}, indent=2)

    def get_station_elev_table(self, station: float) -> str:
        """返回特定断面的Station/Elev表

        返回格式：
        {
            "status": "success",
            "data": {
                "stations": [station1, station2, ...],
                "elevations": [elevation1, elevation2, ...]
            },
            "message": ""
        }
        """
        try:
            for xs in self.cross_sections:
                if "Type RM Length L Ch R " in xs and "#Sta/Elev" in xs:
                    # 提取断面在河流上的Station
                    type_rm = xs["Type RM Length L Ch R "].value
                    if len(type_rm) >= 2:
                        xs_station = float(type_rm[1].value)
                        if xs_station == station:
                            # 提取Sta/Elev表
                            sta_elev = xs["#Sta/Elev"].value
                            stations = []
                            elevations = []
                            data = sta_elev.data
                            for i in range(0, len(data), 2):
                                if i + 1 < len(data):
                                    sta = data[i].value
                                    elev = data[i + 1].value
                                    stations.append(sta)
                                    elevations.append(elev)
                            # 转置格式，Station一个表，elevation一个表
                            result = {"stations": stations, "elevations": elevations}
                            return json.dumps({"status": "success", "data": result, "message": ""}, indent=2)
            return json.dumps(
                {"status": "success", "data": {"stations": [], "elevations": []}, "message": ""}, indent=2
            )
        except Exception as e:
            return json.dumps(
                {"status": "error", "data": {"stations": [], "elevations": []}, "message": str(e)}, indent=2
            )

    def get_all_mann_values(self) -> str:
        """返回所有断面的曼宁值，也就是Mann

        返回格式：
        {
            "status": "success",
            "data": {
                "station1": {
                    "Station": [sta1, sta2, ...],
                    "Manning": [mann1, mann2, ...]
                },
                "station2": {
                    "Station": [sta1, sta2, ...],
                    "Manning": [mann1, mann2, ...]
                },
                ...
            },
            "message": ""
        }
        """
        try:
            result = {}
            for xs in self.cross_sections:
                if "Type RM Length L Ch R " in xs and "#Mann" in xs:
                    # 提取断面在河流上的Station
                    type_rm = xs["Type RM Length L Ch R "].value
                    if len(type_rm) >= 2:
                        station = float(type_rm[1].value)
                        # 提取曼宁值
                        data = xs["#Mann"].value.data
                        stations = []
                        mannings = []
                        for i in range(0, len(data), 3):
                            if i + 2 < len(data):
                                sta = data[i].value
                                mann = data[i + 1].value
                                stations.append(sta)
                                mannings.append(mann)
                        # 构建转置后的格式
                        result[station] = {"Station": stations, "Manning": mannings}
            return json.dumps({"status": "success", "data": result, "message": ""}, indent=2)
        except Exception as e:
            return json.dumps({"status": "error", "data": {}, "message": str(e)}, indent=2)

    def get_all_bank_stations(self) -> str:
        """返回所有断面的Bank Sta值

        返回格式：
        {
            "status": "success",
            "data": {
                "station1": [bank_sta1, bank_sta2],
                "station2": [bank_sta1, bank_sta2],
                ...
            },
            "message": ""
        }
        """
        try:
            result = {}
            for xs in self.cross_sections:
                if "Type RM Length L Ch R " in xs and "Bank Sta" in xs:
                    # 提取断面在河流上的Station
                    type_rm = xs["Type RM Length L Ch R "].value
                    if len(type_rm) >= 2:
                        station = float(type_rm[1].value)
                        # 提取Bank Sta值
                        bank_sta = xs["Bank Sta"].value
                        values: list[Optional[float]] = [float(item.value) for item in bank_sta if item.value]
                        # 确保只返回前两个值，分别对应左岸和右岸
                        if len(values) > 2:
                            values = values[:2]
                        # 如果不足两个值，用None填充
                        elif len(values) < 2:
                            values.extend([None] * (2 - len(values)))
                        result[station] = values
            return json.dumps({"status": "success", "data": result, "message": ""}, indent=2)
        except Exception as e:
            return json.dumps({"status": "error", "data": {}, "message": str(e)}, indent=2)

    def update_mann_values(self, input_json: str) -> str:
        """更新特定断面的曼宁值

        输入格式：
        {
            "XS Station": 5000,
            "Station": [0, 25, ...],
            "Manning": [0.3, 0.7, ...]
        }

        返回格式：
        {
            "status": "success",
            "data": {},
            "message": "Mann values updated successfully"
        }
        """
        try:
            # 解析输入JSON
            input_data = json.loads(input_json)
            xs_station = input_data.get("XS Station")
            stations = input_data.get("Station", [])
            mannings = input_data.get("Manning", [])

            if xs_station is None or not stations or not mannings:
                return json.dumps({"status": "error", "data": {}, "message": "Missing required fields"}, indent=2)

            if len(stations) != len(mannings):
                return json.dumps(
                    {"status": "error", "data": {}, "message": "Station and Manning lists must have the same length"},
                    indent=2,
                )

            # 查找对应的断面
            target_xs = None
            for xs in self.cross_sections:
                if "Type RM Length L Ch R " in xs:
                    type_rm = xs["Type RM Length L Ch R "].value
                    if len(type_rm) >= 2:
                        current_station = float(type_rm[1].value)
                        if current_station == xs_station:
                            target_xs = xs
                            break

            if not target_xs:
                return json.dumps(
                    {"status": "error", "data": {}, "message": f"Cross section with station {xs_station} not found"},
                    indent=2,
                )

            # 构建Mann数据
            # Mann是3个数值一对，格式为 [station, left_manning, right_manning]
            # 这里我们将right_manning设为0，因为用户只提供了一个Manning值
            from parseras.core.values import FloatValue

            mann_data = []
            for station, manning in zip(stations, mannings):
                mann_data.extend([FloatValue(str(station)), FloatValue(str(manning)), FloatValue("0")])

            # 创建并更新DataBlockValue
            from parseras.core.values import DataBlockValue, DataValue

            count = len(stations)
            mann_block = DataBlockValue(value_width=8, values_per_line=9, items_per_value=3)
            mann_block_value = DataValue(tuple(mann_data), 8, 9, 3, (str(count), "-1", "0"), count)
            mann_block.value = mann_block_value
            target_xs["#Mann"] = mann_block

            return json.dumps(
                {"status": "success", "data": {}, "message": "Mann values updated successfully"}, indent=2
            )
        except Exception as e:
            return json.dumps({"status": "error", "data": {}, "message": str(e)}, indent=2)

    def update_bank_stations(self, input_json: str) -> str:
        """更新特定断面的Bank Sta值

        输入格式：
        {
            "XS Station": 5000,
            "Bank Sta": [bank_sta1, bank_sta2]
        }

        返回格式：
        {
            "status": "success",
            "data": {},
            "message": "Bank Sta values updated successfully"
        }
        """
        try:
            # 解析输入JSON
            input_data = json.loads(input_json)
            xs_station = input_data.get("XS Station")
            bank_sta = input_data.get("Bank Sta", [])

            if xs_station is None or not bank_sta:
                return json.dumps({"status": "error", "data": {}, "message": "Missing required fields"}, indent=2)

            if len(bank_sta) < 2:
                return json.dumps(
                    {"status": "error", "data": {}, "message": "Bank Sta must have at least two values"}, indent=2
                )

            # 查找对应的断面
            target_xs = None
            for xs in self.cross_sections:
                if "Type RM Length L Ch R " in xs:
                    type_rm = xs["Type RM Length L Ch R "].value
                    if len(type_rm) >= 2:
                        current_station = float(type_rm[1].value)
                        if current_station == xs_station:
                            target_xs = xs
                            break

            if not target_xs:
                return json.dumps(
                    {"status": "error", "data": {}, "message": f"Cross section with station {xs_station} not found"},
                    indent=2,
                )

            # 创建并更新CommaSeparatedValue
            from parseras.core.values import CommaSeparatedValue, StringValue

            bank_sta_str = ",".join(map(str, bank_sta))
            bank_sta_value = CommaSeparatedValue(bank_sta_str, element_type=StringValue)
            target_xs["Bank Sta"] = bank_sta_value

            return json.dumps(
                {"status": "success", "data": {}, "message": "Bank Sta values updated successfully"}, indent=2
            )
        except Exception as e:
            return json.dumps({"status": "error", "data": {}, "message": str(e)}, indent=2)

    def update_or_create_cross_section(self, input_json: str, tif_path: str | None = None) -> str:
        """更新或创建断面的基本信息和折线数据，并同步更新Sta/Elev

        输入格式：
        {
            "Station": 5000,
            "XS GIS Cut Line": [[x1, y1], [x2, y2], ...]
        }

        参数：
        - input_json: 包含断面信息的JSON字符串
        - tif_path: 可选，DEM数据文件路径，用于获取高程

        返回格式：
        {
            "status": "success",
            "data": {},
            "message": "Cross section updated successfully" 或 "Cross section created successfully"
        }
        """
        try:
            # 解析输入JSON
            input_data = json.loads(input_json)
            station = input_data.get("Station")
            xs_gis_cut_line = input_data.get("XS GIS Cut Line", [])

            if station is None or not xs_gis_cut_line:
                return json.dumps({"status": "error", "data": {}, "message": "Missing required fields"}, indent=2)

            # 查找对应的断面
            target_xs = None
            for xs in self.cross_sections:
                if "Type RM Length L Ch R " in xs:
                    type_rm = xs["Type RM Length L Ch R "].value
                    if len(type_rm) >= 2:
                        current_station = float(type_rm[1].value)
                        if current_station == station:
                            target_xs = xs
                            break

            # 如果找不到断面，创建新的
            if not target_xs:
                from parseras.core.structures import CrossSection

                target_xs = CrossSection([])  # 提供空的lines列表
                self.cross_sections.append(target_xs)
                self.geometry_file._blocks.append(target_xs)  # 使用正确的私有属性名
                message = "Cross section created successfully"
            else:
                message = "Cross section updated successfully"

            # 计算几何中心的函数
            def calculate_centroid(points):
                if not points:
                    return (0, 0)
                x_coords = [p[0] for p in points]
                y_coords = [p[1] for p in points]
                centroid_x = sum(x_coords) / len(x_coords)
                centroid_y = sum(y_coords) / len(y_coords)
                return (centroid_x, centroid_y)

            # 计算两点之间的距离
            def calculate_distance(p1, p2):
                import math

                return math.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2)

            # 计算折线的总长度
            def calculate_total_length(points):
                total_length = 0
                for i in range(1, len(points)):
                    total_length += calculate_distance(points[i - 1], points[i])
                return total_length

            # 在折线上根据距离获取点
            def get_point_at_distance(points, distance):
                if not points:
                    return (0, 0)
                if len(points) == 1:
                    return points[0]

                total_length = 0
                for i in range(1, len(points)):
                    segment_length = calculate_distance(points[i - 1], points[i])
                    if total_length + segment_length >= distance:
                        # 在当前线段上插值
                        ratio = (distance - total_length) / segment_length
                        x = points[i - 1][0] + ratio * (points[i][0] - points[i - 1][0])
                        y = points[i - 1][1] + ratio * (points[i][1] - points[i - 1][1])
                        return (x, y)
                    total_length += segment_length
                # 如果距离超过总长度，返回最后一个点
                return points[-1]

            # 从tif获取高程（支持批量处理）
            def get_elevation_from_tif(xs, ys, tif_path):
                try:
                    import rasterio
                    import numpy as np
                    from rasterio.transform import rowcol

                    with rasterio.open(tif_path) as src:
                        # 计算像素坐标
                        rows, cols = rowcol(src.transform, xs, ys)
                        rows = np.array(rows)
                        cols = np.array(cols)

                        # 过滤有效像素
                        valid = (rows >= 0) & (rows < src.height) & (cols >= 0) & (cols < src.width)

                        elevations = np.full_like(xs, 0.0, dtype=np.float32)

                        if not np.any(valid):
                            return elevations.tolist()

                        # 计算包围窗口
                        row_min, row_max = rows[valid].min(), rows[valid].max()
                        col_min, col_max = cols[valid].min(), cols[valid].max()

                        # 读取窗口
                        window = ((row_min, row_max + 1), (col_min, col_max + 1))
                        data = src.read(1, window=window)

                        # 提取值
                        local_rows = rows[valid] - row_min
                        local_cols = cols[valid] - col_min
                        elevations[valid] = data[local_rows, local_cols]

                        # 处理可能的空值
                        elevations = np.nan_to_num(elevations, nan=0.0)

                        return elevations.tolist()
                except Exception:
                    return [0.0] * len(xs)

            # 计算当前断面的几何中心
            current_centroid = calculate_centroid(xs_gis_cut_line)

            # 找到比当前Station大的最小断面
            next_xs = None
            next_station = float("inf")
            for xs in self.cross_sections:
                if "Type RM Length L Ch R" in xs and "XS GIS Cut Line" in xs:
                    type_rm = xs["Type RM Length L Ch R"].value
                    if len(type_rm) >= 2:
                        current_station = float(type_rm[1].value)
                        if current_station > station and current_station < next_station:
                            next_station = current_station
                            next_xs = xs

            # 计算距离
            distance = 1000  # 默认值
            if next_xs:
                # 提取下一个断面的折线点
                cut_line = next_xs["XS GIS Cut Line"].value
                next_points = []
                data = cut_line.data
                for i in range(0, len(data), 2):
                    if i + 1 < len(data):
                        x = data[i].value
                        y = data[i + 1].value
                        next_points.append([x, y])
                # 计算下一个断面的几何中心
                next_centroid = calculate_centroid(next_points)
                # 计算两个中心的距离
                import math

                distance = math.sqrt(
                    (next_centroid[0] - current_centroid[0]) ** 2 + (next_centroid[1] - current_centroid[1]) ** 2
                )

            # 更新Type RM Length L Ch R
            from parseras.core.values import CommaSeparatedValue, StringValue

            type_rm_str = f"1,{station},{distance},{distance},{distance}"
            type_rm_value = CommaSeparatedValue(type_rm_str, element_type=StringValue)
            target_xs["Type RM Length L Ch R "] = type_rm_value

            # 手动更新order属性
            try:
                if station > 0:
                    target_xs.order = 30 + 1 / station
            except (ValueError, AttributeError):
                pass

            # 更新XS GIS Cut Line
            from parseras.core.values import DataBlockValue, DataValue, FloatValue

            cut_line_data = []
            for point in xs_gis_cut_line:
                cut_line_data.extend([FloatValue(str(point[0])), FloatValue(str(point[1]))])

            count = len(xs_gis_cut_line)
            cut_line_block = DataBlockValue(value_width=16, values_per_line=4, items_per_value=2)
            cut_line_value = DataValue(tuple(cut_line_data), 16, 4, 2, (str(count),), count)
            cut_line_block.value = cut_line_value
            target_xs["XS GIS Cut Line"] = cut_line_block

            # 更新Sta/Elev
            if tif_path:
                # 计算折线总长度
                total_length = calculate_total_length(xs_gis_cut_line)
                # 生成101个采样点
                num_points = 101
                stations = []
                points = []

                for i in range(num_points):
                    # 计算当前距离
                    current_distance = (i / (num_points - 1)) * total_length
                    # 获取对应点的坐标
                    point = get_point_at_distance(xs_gis_cut_line, current_distance)
                    # 添加到列表
                    stations.append(current_distance)
                    points.append(point)

                # 批量获取高程
                xs = [p[0] for p in points]
                ys = [p[1] for p in points]
                elevations = get_elevation_from_tif(xs, ys, tif_path)

                # 构建Sta/Elev数据
                sta_elev_data = []
                for s, e in zip(stations, elevations):
                    sta_elev_data.extend([FloatValue(str(s)), FloatValue(str(e))])

                # 创建并更新DataBlockValue
                count = len(stations)
                sta_elev_block = DataBlockValue(value_width=8, values_per_line=10, items_per_value=2)
                sta_elev_value = DataValue(tuple(sta_elev_data), 8, 10, 2, (str(count),), count)
                sta_elev_block.value = sta_elev_value
                target_xs["#Sta/Elev"] = sta_elev_block
            else:
                # 没有tif路径，置空Sta/Elev
                if "#Sta/Elev" in target_xs:
                    del target_xs["#Sta/Elev"]

            return json.dumps({"status": "success", "data": {}, "message": message}, indent=2)
        except Exception as e:
            return json.dumps({"status": "error", "data": {}, "message": str(e)}, indent=2)
