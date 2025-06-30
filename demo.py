#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RDF转换器演示脚本

展示RDF转换器的主要功能和使用方法
"""

import sys
import os
import json
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def demo_text_to_rdf():
    """演示文本转RDF功能"""
    print("\n" + "=" * 60)
    print("📝 演示：自然语言文本转RDF知识图谱")
    print("=" * 60)
    
    from text_to_rdf import TextToRDFConverter
    
    # 创建转换器（不使用大模型，使用基于规则的方法）
    converter = TextToRDFConverter(use_llm=False)
    
    # 测试文本
    texts = [
        "张三是一名软件工程师，在北京的科技公司工作。",
        "李四是医生，在上海的医院工作。张三和李四是朋友。",
        "王五是教师，在学校教数学。他住在广州。"
    ]
    
    for i, text in enumerate(texts, 1):
        print(f"\n📄 文本 {i}: {text}")
        
        # 转换为RDF
        success = converter.convert_to_rdf(text)
        
        if success:
            stats = converter.get_statistics()
            print(f"✅ 转换成功！")
            print(f"   - 提取的三元组数量: {stats.get('total_triples', 0)}")
            print(f"   - 实体数量: {stats.get('individuals', 0)}")
            print(f"   - 类数量: {stats.get('classes', 0)}")
            
            # 显示部分三元组
            query = """
            SELECT ?s ?p ?o
            WHERE {
                ?s ?p ?o .
            }
            LIMIT 5
            """
            results = converter.query_sparql(query)
            if results:
                print("   📋 部分三元组:")
                for j, result in enumerate(results[:3], 1):
                    s = str(result['s']).split('/')[-1] if '/' in str(result['s']) else str(result['s'])
                    p = str(result['p']).split('/')[-1] if '/' in str(result['p']) else str(result['p'])
                    o = str(result['o'])
                    print(f"      {j}. {s} -> {p} -> {o}")
        else:
            print("❌ 转换失败")
    
    return converter

def demo_rdf_to_text(rdf_converter):
    """演示RDF转文本功能"""
    print("\n" + "=" * 60)
    print("📖 演示：RDF知识图谱转自然语言文本")
    print("=" * 60)
    
    from rdf_to_text import RDFToTextConverter
    
    # 创建RDF转文本转换器
    text_converter = RDFToTextConverter(use_llm=False)
    text_converter.graph = rdf_converter.graph  # 复制RDF图数据
    
    # 生成不同格式的文本
    formats = [
        ('summary', '📄 摘要'),
        ('narrative', '📚 叙述'),
        ('structured', '📊 结构化')
    ]
    
    for format_type, format_name in formats:
        print(f"\n{format_name}:")
        result = text_converter.convert_from_rdf(format_type)
        if result:
            print(f"   {result[:200]}{'...' if len(result) > 200 else ''}")
        else:
            print("   生成失败")

def demo_graph_conversion():
    """演示图数据转换功能"""
    print("\n" + "=" * 60)
    print("🕸️ 演示：图数据与RDF互转")
    print("=" * 60)
    
    from graph_to_rdf import GraphToRDFConverter
    from rdf_to_graph import RDFToGraphConverter
    
    # 创建示例图数据
    graph_data = {
        "nodes": [
            {"id": "person1", "label": "张三", "type": "Person", "properties": {"age": 30, "city": "北京"}},
            {"id": "person2", "label": "李四", "type": "Person", "properties": {"age": 28, "city": "上海"}},
            {"id": "company1", "label": "科技公司", "type": "Company", "properties": {"location": "北京"}},
            {"id": "hospital1", "label": "医院", "type": "Hospital", "properties": {"location": "上海"}}
        ],
        "edges": [
            {"source": "person1", "target": "company1", "relation": "worksAt"},
            {"source": "person2", "target": "hospital1", "relation": "worksAt"},
            {"source": "person1", "target": "person2", "relation": "friendOf"}
        ]
    }
    
    print(f"\n📊 原始图数据:")
    print(f"   - 节点数量: {len(graph_data['nodes'])}")
    print(f"   - 边数量: {len(graph_data['edges'])}")
    
    # 图数据转RDF
    graph_converter = GraphToRDFConverter()
    success = graph_converter.convert_to_rdf(graph_data)
    
    if success:
        stats = graph_converter.get_statistics()
        print(f"\n✅ 图数据转RDF成功!")
        print(f"   - RDF三元组数量: {stats.get('total_triples', 0)}")
        
        # RDF转回图数据
        rdf_graph_converter = RDFToGraphConverter()
        rdf_graph_converter.graph = graph_converter.graph
        
        result_graph = rdf_graph_converter.convert_from_rdf('json')
        
        if result_graph:
            print(f"\n🔄 RDF转回图数据成功!")
            print(f"   - 转换后节点数量: {len(result_graph['nodes'])}")
            print(f"   - 转换后边数量: {len(result_graph['edges'])}")
            
            # 显示部分节点信息
            print("\n   📋 部分节点信息:")
            for i, node in enumerate(result_graph['nodes'][:3], 1):
                print(f"      {i}. {node.get('label', node.get('id', 'Unknown'))} ({node.get('type', 'Unknown')})")
        else:
            print("❌ RDF转图数据失败")
    else:
        print("❌ 图数据转RDF失败")
    
    return graph_converter

def demo_sparql_query(converter):
    """演示SPARQL查询功能"""
    print("\n" + "=" * 60)
    print("🔍 演示：SPARQL查询")
    print("=" * 60)
    
    queries = [
        {
            "name": "查询所有人员",
            "query": """
            PREFIX kg: <http://example.org/kg/>
            SELECT ?person ?name
            WHERE {
                ?person a kg:Person .
                ?person kg:name ?name .
            }
            """
        },
        {
            "name": "查询工作关系",
            "query": """
            PREFIX kg: <http://example.org/kg/>
            SELECT ?person ?company
            WHERE {
                ?person kg:worksAt ?company .
            }
            """
        },
        {
            "name": "统计实体类型",
            "query": """
            SELECT ?type (COUNT(?entity) as ?count)
            WHERE {
                ?entity a ?type .
            }
            GROUP BY ?type
            ORDER BY DESC(?count)
            """
        }
    ]
    
    for query_info in queries:
        print(f"\n🔎 {query_info['name']}:")
        results = converter.query_sparql(query_info['query'])
        
        if results:
            print(f"   ✅ 查询成功，返回 {len(results)} 个结果:")
            for i, result in enumerate(results[:3], 1):
                result_str = ", ".join([f"{k}: {str(v).split('/')[-1] if '/' in str(v) else str(v)}" for k, v in result.items()])
                print(f"      {i}. {result_str}")
            if len(results) > 3:
                print(f"      ... 还有 {len(results) - 3} 个结果")
        else:
            print("   ❌ 查询无结果")

def demo_file_operations(converter):
    """演示文件操作功能"""
    print("\n" + "=" * 60)
    print("💾 演示：文件保存和加载")
    print("=" * 60)
    
    # 保存为不同格式
    formats = [
        ('demo_output.ttl', 'Turtle格式'),
        ('demo_output.rdf', 'RDF/XML格式'),
        ('demo_output.nt', 'N-Triples格式')
    ]
    
    for filename, format_name in formats:
        success = converter.save_to_file(filename)
        if success:
            file_size = Path(filename).stat().st_size
            print(f"✅ {format_name}保存成功: {filename} ({file_size} 字节)")
        else:
            print(f"❌ {format_name}保存失败: {filename}")
    
    # 演示加载
    print(f"\n📂 加载演示:")
    from text_to_rdf import TextToRDFConverter
    
    new_converter = TextToRDFConverter(use_llm=False)
    success = new_converter.load_from_file('demo_output.ttl')
    
    if success:
        stats = new_converter.get_statistics()
        print(f"✅ 文件加载成功!")
        print(f"   - 加载的三元组数量: {stats.get('total_triples', 0)}")
    else:
        print(f"❌ 文件加载失败")
    
    # 清理文件
    print(f"\n🧹 清理临时文件...")
    for filename, _ in formats:
        Path(filename).unlink(missing_ok=True)
    print("✅ 清理完成")

def demo_converter_manager():
    """演示转换器管理器功能"""
    print("\n" + "=" * 60)
    print("🎛️ 演示：转换器管理器")
    print("=" * 60)
    
    from converter_manager import RDFConverterManager, quick_convert
    
    # 创建管理器
    manager = RDFConverterManager(use_llm=False)
    
    # 演示快速转换
    print("\n⚡ 快速转换演示:")
    
    text = "赵六是一名设计师，在广告公司工作。"
    print(f"📝 输入文本: {text}")
    
    # 文本 -> RDF -> 图数据
    graph_result = quick_convert(
        data=text,
        source_format='text',
        target_format='graph_json',
        use_llm=False
    )
    
    if graph_result:
        print(f"✅ 文本转图数据成功!")
        print(f"   - 节点数量: {len(graph_result.get('nodes', []))}")
        print(f"   - 边数量: {len(graph_result.get('edges', []))}")
        
        # 显示节点信息
        print("   📋 节点信息:")
        for i, node in enumerate(graph_result['nodes'][:3], 1):
            print(f"      {i}. {node.get('label', node.get('id', 'Unknown'))} ({node.get('type', 'Unknown')})")
    else:
        print("❌ 快速转换失败")
    
    # 演示支持的格式
    print(f"\n📋 支持的转换格式:")
    formats = manager.get_supported_formats()
    for category, format_list in formats.items():
        print(f"   {category}: {', '.join(format_list)}")

def main():
    """主演示函数"""
    print("🚀 RDF数据转换器功能演示")
    print("=" * 80)
    print("本演示将展示RDF转换器的主要功能，包括:")
    print("• 自然语言文本 ↔ RDF知识图谱")
    print("• 图数据格式 ↔ RDF知识图谱")
    print("• SPARQL查询")
    print("• 文件保存和加载")
    print("• 转换器管理器")
    print("=" * 80)
    
    try:
        # 1. 文本转RDF演示
        rdf_converter = demo_text_to_rdf()
        
        # 2. RDF转文本演示
        demo_rdf_to_text(rdf_converter)
        
        # 3. 图数据转换演示
        graph_converter = demo_graph_conversion()
        
        # 4. SPARQL查询演示
        demo_sparql_query(graph_converter)
        
        # 5. 文件操作演示
        demo_file_operations(graph_converter)
        
        # 6. 转换器管理器演示
        demo_converter_manager()
        
        print("\n" + "=" * 80)
        print("🎉 演示完成！")
        print("\n📚 更多功能请参考:")
        print("   • README.md - 详细使用说明")
        print("   • examples.py - 更多使用示例")
        print("   • simple_test.py - 功能测试")
        print("=" * 80)
        
    except KeyboardInterrupt:
        print("\n\n⏹️ 演示被用户中断")
    except Exception as e:
        print(f"\n\n❌ 演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()