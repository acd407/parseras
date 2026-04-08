"""
工具函数模块，提供几何计算和DEM处理等通用功能
"""

import math
from typing import List, Tuple, Optional


def calculate_centroid(points: List[List[float]]) -> Tuple[float, float]:
    """计算点集的几何中心

    Args:
        points: 点列表，每个点为[x, y]

    Returns:
        几何中心坐标(x, y)
    """
    if not points:
        return (0.0, 0.0)
    x_coords = [p[0] for p in points]
    y_coords = [p[1] for p in points]
    centroid_x = sum(x_coords) / len(x_coords)
    centroid_y = sum(y_coords) / len(y_coords)
    return (centroid_x, centroid_y)


def calculate_distance(p1: List[float], p2: List[float]) -> float:
    """计算两点之间的欧几里得距离

    Args:
        p1: 第一个点[x1, y1]
        p2: 第二个点[x2, y2]

    Returns:
        两点之间的距离
    """
    return math.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2)


def calculate_total_length(points: List[List[float]]) -> float:
    """计算折线的总长度

    Args:
        points: 折线点列表

    Returns:
        折线总长度
    """
    total_length = 0.0
    for i in range(1, len(points)):
        total_length += calculate_distance(points[i - 1], points[i])
    return total_length


def get_point_at_distance(points: List[List[float]], distance: float) -> Tuple[float, float]:
    """在折线上根据距离获取点

    Args:
        points: 折线点列表
        distance: 从起点开始的距离

    Returns:
        距离起点指定距离的点坐标(x, y)
    """
    if not points:
        return (0.0, 0.0)
    if len(points) == 1:
        return (points[0][0], points[0][1])

    total_length = 0.0
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
    return (points[-1][0], points[-1][1])


def get_elevation_from_tif(xs: List[float], ys: List[float], tif_path: str) -> List[float]:
    """从DEM栅格文件获取点的高程

    Args:
        xs: x坐标列表
        ys: y坐标列表
        tif_path: DEM栅格文件路径

    Returns:
        高程值列表，与输入坐标一一对应
    """
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
        # 如果无法读取DEM，返回0高程
        return [0.0] * len(xs)


def generate_se_from_centerline(
    centerline: List[List[float]],
    tif_path: Optional[str] = None,
    num_points: int = 101
) -> List[List[float]]:
    """从中心线生成SE（Station-Elevation）表

    Args:
        centerline: 中心线点列表
        tif_path: 可选，DEM栅格文件路径
        num_points: 采样点数量，默认101

    Returns:
        SE表，每个点为[distance, elevation]
    """
    if not centerline:
        return []

    # 计算中心线总长度
    total_length = calculate_total_length(centerline)

    # 生成采样点和距离
    distances = []
    points = []
    for i in range(num_points):
        # 计算当前距离
        current_distance = (i / (num_points - 1)) * total_length if num_points > 1 else 0.0
        distances.append(current_distance)

        # 获取对应点的坐标
        point = get_point_at_distance(centerline, current_distance)
        points.append(point)

    # 如果有DEM，获取高程
    if tif_path:
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        elevations = get_elevation_from_tif(xs, ys, tif_path)
    else:
        elevations = [0.0] * len(points)

    # 构建SE表
    se_table = []
    for dist, elev in zip(distances, elevations):
        se_table.append([dist, elev])

    return se_table