# parseras：HEC-RAS 几何文件读写库

这是一个用于解析和生成 HEC-RAS 几何数据文件（.g01）的 Python 库。该库提供了底层存储结构抽象和业务模型层，使得处理 HEC-RAS 几何数据更加便捷。

## 添加新测试

RAS的文件很不规范，要添加新测试，请先使用如下命令处理测试文件，
例如对于待测试文件`tests/leak.g01`

```bash
sed -i -e 's/= */=/g' -e 's/ *, */,/g' -e 's/ \./0\./g' -e 's/[[:space:]]*$//' tests/leak.g01
sed -i -e '/^$/N;/^\n$/D' tests/leak.g01
```

## 核心功能

### 1. 文件解析与生成
- 解析 HEC-RAS .g01 格式文件
- 生成符合 HEC-RAS 格式的 .g01 文件
- 支持文件块的自动识别和解析

### 2. 数据块结构
- 支持多种数据块类型：Head、River、CrossSection、BreakLine、LateralWeir、StorageArea、Foot
- 每个数据块类型都有对应的类实现
- 支持数据块的优先级排序，确保生成文件的结构一致性

### 3. 业务模型层
- **CrossSectionModel**：提供断面相关的业务逻辑
- **RiverModel**：提供河流相关的业务逻辑
- **TODO**
