# parseras

## 添加新测试

RAS的文件很不规范，请先使用如下命令处理测试文件，
例如待测试文件为`tests/leak.g01`

```bash
sed -i -e 's/ *= */=/g' -e 's/ *, */,/g' -e 's/ \./0\./g' -e 's/[[:space:]]*$//' tests/leak.g01
sed -i -e '/^$/N;/^\n$/D' tests/leak.g01
```
