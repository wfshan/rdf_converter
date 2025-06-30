# RDF数据转换器

一个功能强大的Python库，用于在不同数据格式之间进行RDF知识图谱转换。支持自然语言文本、图数据结构、Excel表格等多种格式与RDF之间的双向转换。

## 🚀 主要功能

- **文本 ↔ RDF**: 自然语言文本与RDF知识图谱的双向转换
- **图数据 ↔ RDF**: 支持多种图数据格式（JSON、NetworkX、Cypher等）
- **Excel ↔ RDF**: Excel表格数据与RDF的转换
- **SPARQL查询**: 对RDF数据进行灵活查询
- **多格式支持**: 支持Turtle、RDF/XML、N-Triples、JSON-LD等RDF格式
- **统一管理**: 通过转换器管理器实现一站式转换服务

## 📦 安装依赖

```bash
pip install -r requirements.txt
```

## 🎯 快速开始

### 1. 文本转RDF知识图谱

```python
from text_to_rdf import TextToRDFConverter

# 创建转换器
converter = TextToRDFConverter(use_llm=False)

# 转换文本
text = "张三是一名软件工程师，在北京的科技公司工作。"
success = converter.convert_to_rdf(text)

if success:
    # 保存为文件
    converter.save_to_file("output.ttl")
    
    # 获取统计信息
    stats = converter.get_statistics()
    print(f"提取了 {stats['total_triples']} 个三元组")
else:
    print("转换失败")
```

### 2. 图数据转RDF

```python
from graph_to_rdf import GraphToRDFConverter

# 创建图数据
graph_data = {
    "nodes": [
        {"id": "person1", "label": "张三", "type": "Person", 
         "properties": {"age": 30, "city": "北京"}},
        {"id": "company1", "label": "科技公司", "type": "Company"}
    ],
    "edges": [
        {"source": "person1", "target": "company1", "relation": "worksAt"}
    ]
}

# 转换为RDF
converter = GraphToRDFConverter()
success = converter.convert_to_rdf(graph_data)

if success:
    converter.save_to_file("graph_output.ttl")
```

### 3. RDF转文本

```python
from rdf_to_text import RDFToTextConverter

# 加载RDF数据
converter = RDFToTextConverter(use_llm=False)
converter.load_from_file("input.ttl")

# 生成不同格式的文本
summary = converter.convert_from_rdf('summary')
narrative = converter.convert_from_rdf('narrative')
structured = converter.convert_from_rdf('structured')

print("摘要:", summary)
print("叙述:", narrative)
print("结构化:", structured)
```

### 4. SPARQL查询

```python
# 查询所有人员信息
query = """
PREFIX kg: <http://example.org/kg/>
SELECT ?person ?name ?age
WHERE {
    ?person a kg:Person .
    ?person kg:name ?name .
    OPTIONAL { ?person kg:age ?age }
}
"""

results = converter.query_sparql(query)
for result in results:
    print(f"人员: {result['name']}, 年龄: {result.get('age', '未知')}")
```

### 5. 使用转换器管理器

```python
from converter_manager import RDFConverterManager, quick_convert

# 快速转换
result = quick_convert(
    data="李四是医生，在医院工作。",
    source_format='text',
    target_format='graph_json',
    use_llm=False
)

print(f"转换结果: {len(result['nodes'])} 个节点, {len(result['edges'])} 条边")

# 使用管理器
manager = RDFConverterManager(use_llm=False)
formats = manager.get_supported_formats()
print("支持的格式:", formats)
```

## 📊 支持的数据格式

### 输入格式
- **text**: 自然语言文本
- **graph_json**: JSON格式的图数据
- **graph_networkx**: NetworkX图对象
- **graph_cypher**: Cypher查询语句
- **excel**: Excel表格文件

### 输出格式
- **文本格式**: narrative（叙述）, summary（摘要）, report（报告）, qa（问答）, structured（结构化）
- **图格式**: json, networkx, cypher, gexf, graphml, edgelist, adjacency
- **RDF格式**: turtle, xml, n3, nt, json-ld

## 🔧 配置选项

### 环境变量

创建 `.env` 文件配置大模型API（可选）:

```env
# OpenAI配置
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=https://api.openai.com/v1

# 其他大模型配置
LLM_PROVIDER=openai
LLM_MODEL=gpt-3.5-turbo
```

### 转换器参数

```python
# 使用大模型进行智能转换
converter = TextToRDFConverter(use_llm=True)

# 使用基于规则的方法（默认）
converter = TextToRDFConverter(use_llm=False)

# 自定义基础URI
converter = TextToRDFConverter(base_uri="http://mycompany.com/kg/")
```

## 📝 示例和测试

### 运行完整演示

```bash
python demo.py
```

### 运行功能测试

```bash
python simple_test.py
```

### 运行完整测试套件

```bash
python test_converter.py
```

## 🏗️ 项目结构

```
rdf_converter/
├── base_converter.py      # 转换器基类
├── text_to_rdf.py        # 文本转RDF转换器
├── rdf_to_text.py        # RDF转文本转换器
├── graph_to_rdf.py       # 图数据转RDF转换器
├── rdf_to_graph.py       # RDF转图数据转换器
├── converter_manager.py   # 转换器管理器
├── demo.py               # 功能演示脚本
├── simple_test.py        # 简单测试脚本
├── test_converter.py     # 完整测试套件
├── requirements.txt      # 依赖包列表
└── README.md            # 项目说明文档
```

## 🔍 高级用法

### 自定义命名空间

```python
from rdflib import Namespace

converter = TextToRDFConverter()
converter.namespaces['custom'] = Namespace('http://example.com/custom/')
converter._bind_namespaces()
```

### 批量处理

```python
texts = [
    "张三是工程师",
    "李四是医生", 
    "王五是教师"
]

converter = TextToRDFConverter(use_llm=False)
for i, text in enumerate(texts):
    success = converter.convert_to_rdf(text)
    if success:
        converter.save_to_file(f"output_{i}.ttl")
```

### 数据融合

```python
# 合并多个RDF图
converter1 = TextToRDFConverter(use_llm=False)
converter1.convert_to_rdf("张三是工程师")

converter2 = TextToRDFConverter(use_llm=False)
converter2.convert_to_rdf("李四是医生")

# 合并图数据
converter1.graph += converter2.graph
converter1.save_to_file("merged.ttl")
```

## ⚠️ 注意事项

1. **依赖版本**: 确保NumPy版本 < 2.0 以避免兼容性问题
2. **大模型使用**: 使用大模型功能需要配置相应的API密钥
3. **内存使用**: 处理大型数据集时注意内存使用情况
4. **编码格式**: 确保输入文本使用UTF-8编码

## 🤝 贡献指南

欢迎提交Issue和Pull Request来改进这个项目！

## 📄 许可证

本项目采用MIT许可证。

## 📞 联系方式

如有问题或建议，请通过GitHub Issues联系我们。