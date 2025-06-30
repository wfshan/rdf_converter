#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RDF转换器使用示例

展示各种转换功能的使用方法
"""

import json
import logging
from pathlib import Path

# 导入转换器
from converter_manager import RDFConverterManager, quick_convert, convert_file

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def example_text_to_rdf():
    """示例：文本转RDF"""
    print("\n=== 文本转RDF示例 ===")
    
    # 示例文本
    text = """
    张三是一名软件工程师，在北京的科技公司工作。
    他拥有一个银行账户，账户号码是123456789。
    昨天他向李四转账了5000元，李四是他的朋友。
    李四在上海工作，是一名数据分析师。
    """
    
    # 创建转换器管理器
    manager = RDFConverterManager(use_llm=False)  # 不使用大模型进行演示
    
    # 转换为RDF
    success = manager.convert_to_rdf(text, 'text')
    
    if success:
        print("✓ 文本成功转换为RDF")
        
        # 获取统计信息
        stats = manager.get_rdf_statistics()
        print(f"三元组数量: {stats['total_triples']}")
        print(f"实体数量: {stats['individuals']}")
        
        # 保存RDF文件
        output_file = "example_text.ttl"
        manager.save_current_rdf(output_file)
        print(f"RDF已保存到: {output_file}")
        
        return manager
    else:
        print("✗ 文本转RDF失败")
        return None

def example_graph_to_rdf():
    """示例：图数据转RDF"""
    print("\n=== 图数据转RDF示例 ===")
    
    # 示例图数据（JSON格式）
    graph_data = {
        "nodes": [
            {"id": "person1", "label": "张三", "type": "Person", "properties": {"age": 30, "city": "北京"}},
            {"id": "person2", "label": "李四", "type": "Person", "properties": {"age": 28, "city": "上海"}},
            {"id": "company1", "label": "科技公司", "type": "Company", "properties": {"location": "北京"}},
            {"id": "account1", "label": "账户123456789", "type": "Account", "properties": {"number": "123456789"}}
        ],
        "edges": [
            {"source": "person1", "target": "company1", "relation": "worksAt"},
            {"source": "person1", "target": "account1", "relation": "owns"},
            {"source": "person1", "target": "person2", "relation": "friendOf"},
            {"source": "account1", "target": "person2", "relation": "transfersTo"}
        ]
    }
    
    # 创建转换器管理器
    manager = RDFConverterManager()
    
    # 转换为RDF
    success = manager.convert_to_rdf(graph_data, 'graph_json')
    
    if success:
        print("✓ 图数据成功转换为RDF")
        
        # 获取统计信息
        stats = manager.get_rdf_statistics()
        print(f"三元组数量: {stats['total_triples']}")
        print(f"实体数量: {stats['individuals']}")
        
        # 保存RDF文件
        output_file = "example_graph.ttl"
        manager.save_current_rdf(output_file)
        print(f"RDF已保存到: {output_file}")
        
        return manager
    else:
        print("✗ 图数据转RDF失败")
        return None

def example_rdf_to_text(manager):
    """示例：RDF转文本"""
    print("\n=== RDF转文本示例 ===")
    
    if manager is None:
        print("✗ 没有可用的RDF数据")
        return
    
    # 转换为不同的文本格式
    formats = ['narrative', 'summary', 'report', 'qa', 'structured']
    
    for format_type in formats:
        print(f"\n--- {format_type.upper()} 格式 ---")
        result = manager.convert_from_rdf(f'text_{format_type}')
        
        if result:
            print(result[:200] + "..." if len(result) > 200 else result)
            
            # 保存到文件
            output_file = f"example_{format_type}.txt"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(result)
            print(f"已保存到: {output_file}")
        else:
            print(f"✗ 转换为{format_type}格式失败")

def example_rdf_to_graph(manager):
    """示例：RDF转图数据"""
    print("\n=== RDF转图数据示例 ===")
    
    if manager is None:
        print("✗ 没有可用的RDF数据")
        return
    
    # 转换为不同的图格式
    formats = ['json', 'cypher', 'edgelist']
    
    for format_type in formats:
        print(f"\n--- {format_type.upper()} 格式 ---")
        result = manager.convert_from_rdf(f'graph_{format_type}')
        
        if result is not None:
            if format_type == 'json':
                print(f"节点数量: {len(result['nodes'])}")
                print(f"边数量: {len(result['edges'])}")
                
                # 保存JSON文件
                output_file = f"example_graph.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                print(f"已保存到: {output_file}")
                
            elif format_type == 'cypher':
                print(f"Cypher语句长度: {len(result)}")
                print("前3行:")
                lines = result.split('\n')[:3]
                for line in lines:
                    print(f"  {line}")
                
                # 保存Cypher文件
                output_file = f"example_graph.cypher"
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(result)
                print(f"已保存到: {output_file}")
                
            elif format_type == 'edgelist':
                print(f"边列表长度: {len(result)}")
                print("前3条边:")
                for edge in result[:3]:
                    print(f"  {edge[0]} -> {edge[1]} ({edge[2]['relation']})")
        else:
            print(f"✗ 转换为{format_type}格式失败")

def example_networkx_integration():
    """示例：NetworkX集成"""
    print("\n=== NetworkX集成示例 ===")
    
    try:
        import networkx as nx
        import matplotlib.pyplot as plt
        
        # 创建NetworkX图
        G = nx.DiGraph()
        
        # 添加节点
        G.add_node("张三", type="Person", age=30)
        G.add_node("李四", type="Person", age=28)
        G.add_node("科技公司", type="Company")
        G.add_node("账户123", type="Account")
        
        # 添加边
        G.add_edge("张三", "科技公司", relation="worksAt")
        G.add_edge("张三", "账户123", relation="owns")
        G.add_edge("张三", "李四", relation="friendOf")
        
        print(f"NetworkX图: {G.number_of_nodes()}个节点, {G.number_of_edges()}条边")
        
        # 转换为RDF
        manager = RDFConverterManager()
        success = manager.convert_to_rdf(G, 'graph_networkx')
        
        if success:
            print("✓ NetworkX图成功转换为RDF")
            
            # 转换回NetworkX
            result_graph = manager.convert_from_rdf('graph_networkx')
            
            if result_graph is not None:
                print(f"✓ RDF成功转换回NetworkX图: {result_graph.number_of_nodes()}个节点, {result_graph.number_of_edges()}条边")
                
                # 可视化（可选）
                try:
                    plt.figure(figsize=(10, 6))
                    pos = nx.spring_layout(result_graph)
                    nx.draw(result_graph, pos, with_labels=True, node_color='lightblue', 
                           node_size=1000, font_size=8, arrows=True)
                    plt.title("RDF Knowledge Graph (NetworkX)")
                    plt.savefig("example_networkx_graph.png", dpi=300, bbox_inches='tight')
                    print("图谱可视化已保存到: example_networkx_graph.png")
                    plt.close()
                except Exception as e:
                    print(f"可视化失败: {e}")
            else:
                print("✗ RDF转换回NetworkX失败")
        else:
            print("✗ NetworkX图转RDF失败")
            
    except ImportError:
        print("NetworkX或matplotlib未安装，跳过此示例")

def example_sparql_query(manager):
    """示例：SPARQL查询"""
    print("\n=== SPARQL查询示例 ===")
    
    if manager is None:
        print("✗ 没有可用的RDF数据")
        return
    
    # 示例查询
    queries = [
        {
            "name": "查询所有人员",
            "query": """
            SELECT ?person ?label
            WHERE {
                ?person a ?type .
                ?type rdfs:subClassOf* <http://example.org/kg/Person> .
                OPTIONAL { ?person rdfs:label ?label }
            }
            """
        },
        {
            "name": "查询工作关系",
            "query": """
            SELECT ?person ?company
            WHERE {
                ?person <http://example.org/kg/worksAt> ?company .
            }
            """
        },
        {
            "name": "查询所有关系",
            "query": """
            SELECT ?subject ?predicate ?object
            WHERE {
                ?subject ?predicate ?object .
                FILTER(?predicate != rdf:type && ?predicate != rdfs:label)
            }
            LIMIT 10
            """
        }
    ]
    
    for query_info in queries:
        print(f"\n--- {query_info['name']} ---")
        try:
            results = manager.query_rdf(query_info['query'])
            print(f"查询结果数量: {len(results)}")
            
            for i, result in enumerate(results[:3]):  # 只显示前3个结果
                print(f"  结果{i+1}: {result}")
                
            if len(results) > 3:
                print(f"  ... 还有{len(results)-3}个结果")
                
        except Exception as e:
            print(f"查询失败: {e}")

def example_batch_conversion():
    """示例：批量转换"""
    print("\n=== 批量转换示例 ===")
    
    # 创建示例文件
    input_dir = Path("example_input")
    output_dir = Path("example_output")
    
    input_dir.mkdir(exist_ok=True)
    output_dir.mkdir(exist_ok=True)
    
    # 创建示例文本文件
    sample_texts = [
        "张三在北京工作，是一名工程师。",
        "李四住在上海，从事数据分析工作。",
        "王五是一名医生，在医院工作。"
    ]
    
    for i, text in enumerate(sample_texts, 1):
        with open(input_dir / f"sample_{i}.txt", 'w', encoding='utf-8') as f:
            f.write(text)
    
    print(f"已创建{len(sample_texts)}个示例文件")
    
    # 执行批量转换
    manager = RDFConverterManager(use_llm=False)
    results = manager.batch_convert(str(input_dir), str(output_dir), 'text', 'text_summary')
    
    print(f"批量转换结果: {results}")
    
    success_count = sum(results.values())
    total_count = len(results)
    print(f"成功转换: {success_count}/{total_count} 个文件")

def example_quick_convert():
    """示例：快速转换函数"""
    print("\n=== 快速转换函数示例 ===")
    
    # 使用快速转换函数
    text = "这是一个测试文本，包含张三和李四两个人。"
    
    # 文本 -> RDF -> JSON图
    result = quick_convert(text, 'text', 'graph_json', use_llm=False)
    
    if result:
        print("✓ 快速转换成功")
        print(f"节点数量: {len(result['nodes'])}")
        print(f"边数量: {len(result['edges'])}")
    else:
        print("✗ 快速转换失败")

def main():
    """主函数：运行所有示例"""
    print("RDF转换器使用示例")
    print("=" * 50)
    
    # 文本转RDF示例
    text_manager = example_text_to_rdf()
    
    # 图数据转RDF示例
    graph_manager = example_graph_to_rdf()
    
    # 选择一个管理器进行后续示例
    manager = graph_manager if graph_manager else text_manager
    
    if manager:
        # RDF转文本示例
        example_rdf_to_text(manager)
        
        # RDF转图数据示例
        example_rdf_to_graph(manager)
        
        # SPARQL查询示例
        example_sparql_query(manager)
    
    # NetworkX集成示例
    example_networkx_integration()
    
    # 批量转换示例
    example_batch_conversion()
    
    # 快速转换示例
    example_quick_convert()
    
    print("\n=== 所有示例运行完成 ===")
    print("生成的文件:")
    
    # 列出生成的文件
    current_dir = Path(".")
    generated_files = [
        "example_text.ttl",
        "example_graph.ttl", 
        "example_narrative.txt",
        "example_summary.txt",
        "example_report.txt",
        "example_qa.txt",
        "example_structured.txt",
        "example_graph.json",
        "example_graph.cypher",
        "example_networkx_graph.png"
    ]
    
    for file_name in generated_files:
        file_path = current_dir / file_name
        if file_path.exists():
            print(f"  ✓ {file_name}")
        else:
            print(f"  - {file_name} (未生成)")

if __name__ == "__main__":
    main()