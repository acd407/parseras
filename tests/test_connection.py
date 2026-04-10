import json
import os

from parseras import GeometryFile, ConnectionModel


def test_connection_read_write():
    """测试Connection的读写功能"""
    test_file = os.path.join(os.path.dirname(__file__), "data", "conn.g01")
    output_file = os.path.join(os.path.dirname(__file__), "data", "conn.model.output.g01")

    if not os.path.exists(test_file):
        print(f"测试文件不存在: {test_file}")
        return False

    geometry_file = GeometryFile(file_path=test_file)
    conn_model = ConnectionModel(geometry_file)

    all_conns = conn_model.get_all_connections()
    all_conns_data = json.loads(all_conns)

    if all_conns_data.get("status") != "success":
        print(f"获取连接列表失败")
        return False

    conn_name = "Storage Area 1 T"
    conn_info = conn_model.get_connection_info(conn_name)
    conn_info_data = json.loads(conn_info)

    if conn_info_data.get("status") != "success":
        print(f"获取连接信息失败")
        return False

    generated_lines = geometry_file.generate()
    with open(output_file, "w") as f:
        f.writelines(generated_lines)

    with open(output_file, "r") as f:
        updated_content = f.readlines()

    updated_geometry_file = GeometryFile(lines=updated_content)
    updated_conn_model = ConnectionModel(updated_geometry_file)

    updated_all_conns = updated_conn_model.get_all_connections()
    updated_all_conns_data = json.loads(updated_all_conns)

    if all_conns_data["data"] != updated_all_conns_data["data"]:
        print("连接列表不匹配")
        return False

    updated_conn_info = updated_conn_model.get_connection_info(conn_name)
    updated_conn_info_data = json.loads(updated_conn_info)

    if conn_info_data["data"] != updated_conn_info_data["data"]:
        print("连接信息不匹配")
        return False

    return True


def test_connection_create_validation():
    """测试Connection创建时的验证"""
    geometry_file = GeometryFile()
    conn_model = ConnectionModel(geometry_file)

    input_missing_line = json.dumps({
        "Connection Name": "Test Conn",
        "Connection Up SA": "SA1",
        "Connection Dn SA": "SA2",
        "Conn Weir WD": 100
    })
    result = json.loads(conn_model.update_or_create_connection(input_missing_line))
    if result["status"] != "error" or "Connection Line" not in result["message"]:
        print("应该检测到缺少Connection Line")
        return False

    input_missing_up_sa = json.dumps({
        "Connection Name": "Test Conn",
        "Connection Line": [[0, 0], [100, 100]],
        "Connection Dn SA": "SA2",
        "Conn Weir WD": 100
    })
    result = json.loads(conn_model.update_or_create_connection(input_missing_up_sa))
    if result["status"] != "error" or "Connection Up SA" not in result["message"]:
        print("应该检测到缺少Connection Up SA")
        return False

    input_missing_weir_wd = json.dumps({
        "Connection Name": "Test Conn",
        "Connection Line": [[0, 0], [100, 100]],
        "Connection Up SA": "SA1",
        "Connection Dn SA": "SA2"
    })
    result = json.loads(conn_model.update_or_create_connection(input_missing_weir_wd))
    if result["status"] != "error" or "Conn Weir WD" not in result["message"]:
        print("应该检测到缺少Conn Weir WD")
        return False

    return True


def test_connection_update():
    """测试Connection的更新"""
    test_file = os.path.join(os.path.dirname(__file__), "data", "conn.g01")
    if not os.path.exists(test_file):
        print(f"测试文件不存在: {test_file}")
        return False

    geometry_file = GeometryFile(file_path=test_file)
    conn_model = ConnectionModel(geometry_file)

    original_info = conn_model.get_connection_info("Storage Area 1 T")
    original_data = json.loads(original_info)

    if original_data["data"].get("Conn Weir WD") != 200:
        print("原始Conn Weir WD值不正确")
        return False

    update_input = json.dumps({
        "Connection Name": "Storage Area 1 T",
        "Conn Weir WD": 300
    })
    result = json.loads(conn_model.update_or_create_connection(update_input))
    if result["status"] != "success":
        print(f"更新失败: {result['message']}")
        return False

    updated_info = conn_model.get_connection_info("Storage Area 1 T")
    updated_data = json.loads(updated_info)

    if updated_data["data"].get("Conn Weir WD") != 300:
        print("更新后的Conn Weir WD值不正确")
        return False

    return True


def run_connection_tests():
    results = {
        "test_connection_read_write": test_connection_read_write(),
        "test_connection_create_validation": test_connection_create_validation(),
        "test_connection_update": test_connection_update(),
    }
    return results