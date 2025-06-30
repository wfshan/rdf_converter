#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的RDF转换器测试脚本

避免NumPy兼容性问题，专注测试核心功能
"""

import sys
import os
import logging
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_basic_rdf_operations():
    """测试基本RDF操作"""
    print("\n=== 测试基本RDF操作 ===")
    
    try:
        # 测试文本转换器（具体实现类）
        from text_to_rdf import TextToRDFConverter
        
        converter = TextToRDFConverter(use_llm=False)
        print("✓ 基础转换器创建成功")
        
        # 添加一些测试数据
        from rdflib import Literal
        
        converter.add_triple(
            converter.create_uri("person1"),
            converter.create_uri("name"),
            Literal("张三")
        )
        
        converter.add_triple(
            converter.create_uri("person1"),
            converter.create_uri("age"),
            Literal(30)
        )
        
        print("✓ 三元组添加成功")
        
        # 获取统计信息
        stats = converter.get_statistics()
        print(f"  - 三元组数量: {stats.get('total_triples', 0)}")
        
        # 测试SPARQL查询
        query = """
        SELECT ?subject ?predicate ?object
        WHERE {
            ?subject ?predicate ?object .
        }
        """
        
        results = converter.query(query)
        print(f"✓ SPARQL查询成功，返回{len(results)}个结果")
        
        return True
        
    except Exception as e:
        print(f"✗ 基本RDF操作测试失败: {e}")
        return False

def test_text_conversion():
    """测试文本转换功能"""
    print("\n=== 测试文本转换功能 ===")
    
    try:
        from text_to_rdf import TextToRDFConverter
        
        converter = TextToRDFConverter(use_llm=False)
        print("✓ 文本转换器创建成功")
        
        # 测试简单文本转换
        test_text = "张三是工程师，在北京工作。"
        success = converter.convert_to_rdf(test_text)
        
        if success:
            print("✓ 文本转RDF成功")
            
            # 获取统计信息
            stats = converter.get_statistics()
            print(f"  - 提取的三元组数量: {stats.get('total_triples', 0)}")
            
            return True
        else:
            print("✗ 文本转RDF失败")
            return False
            
    except Exception as e:
        print(f"✗ 文本转换测试失败: {e}")
        return False

def test_graph_conversion():
    """测试图数据转换功能"""
    print("\n=== 测试图数据转换功能 ===")
    
    try:
        from graph_to_rdf import GraphToRDFConverter
        
        converter = GraphToRDFConverter()
        print("✓ 图数据转换器创建成功")
        
        # 创建测试图数据
        graph_data = {
            "nodes": [
                {"id": "person1", "label": "张三", "type": "Person"},
                {"id": "company1", "label": "科技公司", "type": "Company"}
            ],
            "edges": [
                {"source": "person1", "target": "company1", "relation": "worksAt"}
            ]
        }
        
        success = converter.convert_to_rdf(graph_data)
        
        if success:
            print("✓ 图数据转RDF成功")
            
            # 获取统计信息
            stats = converter.get_statistics()
            print(f"  - 转换的三元组数量: {stats.get('total_triples', 0)}")
            
            return True
        else:
            print("✗ 图数据转RDF失败")
            return False
            
    except Exception as e:
        print(f"✗ 图数据转换测试失败: {e}")
        return False

def test_rdf_to_text():
    """测试RDF转文本功能"""
    print("\n=== 测试RDF转文本功能 ===")
    
    try:
        from rdf_to_text import RDFToTextConverter
        from text_to_rdf import TextToRDFConverter
        
        # 先创建一些RDF数据
        text_converter = TextToRDFConverter(use_llm=False)
        text_converter.convert_to_rdf("李四是医生，在医院工作。")
        
        # 转换为文本
        rdf_converter = RDFToTextConverter(use_llm=False)
        rdf_converter.graph = text_converter.graph  # 复制图数据
        
        summary = rdf_converter.convert_from_rdf('summary')
        
        if summary:
            print("✓ RDF转文本成功")
            print(f"  - 生成摘要长度: {len(summary)}字符")
            print(f"  - 摘要内容: {summary[:100]}...")
            return True
        else:
            print("✗ RDF转文本失败")
            return False
            
    except Exception as e:
        print(f"✗ RDF转文本测试失败: {e}")
        return False

def test_rdf_to_graph():
    """测试RDF转图数据功能"""
    print("\n=== 测试RDF转图数据功能 ===")
    
    try:
        from rdf_to_graph import RDFToGraphConverter
        from text_to_rdf import TextToRDFConverter
        
        # 先创建一些RDF数据
        text_converter = TextToRDFConverter(use_llm=False)
        text_converter.convert_to_rdf("王五是教师，在学校工作。")
        
        # 转换为图数据
        graph_converter = RDFToGraphConverter()
        graph_converter.graph = text_converter.graph  # 复制图数据
        
        graph_data = graph_converter.convert_from_rdf('json')
        
        if graph_data:
            print("✓ RDF转图数据成功")
            print(f"  - 节点数量: {len(graph_data.get('nodes', []))}")
            print(f"  - 边数量: {len(graph_data.get('edges', []))}")
            return True
        else:
            print("✗ RDF转图数据失败")
            return False
            
    except Exception as e:
        print(f"✗ RDF转图数据测试失败: {e}")
        return False

def test_file_operations():
    """测试文件操作"""
    print("\n=== 测试文件操作 ===")
    
    try:
        from text_to_rdf import TextToRDFConverter
        
        converter = TextToRDFConverter(use_llm=False)
        
        # 添加测试数据
        from rdflib import Literal
        
        converter.add_triple(
            converter.create_uri("test_person"),
            converter.create_uri("name"),
            Literal("测试人员")
        )
        
        # 保存文件
        test_file = "test_output.ttl"
        success = converter.save_to_file(test_file)
        
        if success:
            print("✓ RDF文件保存成功")
            
            # 加载文件
            new_converter = TextToRDFConverter(use_llm=False)
            load_success = new_converter.load_from_file(test_file)
            
            if load_success:
                print("✓ RDF文件加载成功")
                
                # 验证数据
                stats = new_converter.get_statistics()
                print(f"  - 加载的三元组数量: {stats.get('total_triples', 0)}")
                
                # 清理测试文件
                Path(test_file).unlink(missing_ok=True)
                print("✓ 测试文件清理完成")
                
                return True
            else:
                print("✗ RDF文件加载失败")
                return False
        else:
            print("✗ RDF文件保存失败")
            return False
            
    except Exception as e:
        print(f"✗ 文件操作测试失败: {e}")
        return False

def run_simple_tests():
    """运行简化测试"""
    print("RDF转换器简化测试套件")
    print("=" * 50)
    
    tests = [
        ("基本RDF操作", test_basic_rdf_operations),
        ("文本转换", test_text_conversion),
        ("图数据转换", test_graph_conversion),
        ("RDF转文本", test_rdf_to_text),
        ("RDF转图数据", test_rdf_to_graph),
        ("文件操作", test_file_operations)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name}测试异常: {e}")
            results.append((test_name, False))
    
    # 输出测试结果汇总
    print("\n" + "=" * 50)
    print("测试结果汇总")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{test_name:<15} {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！RDF转换器核心功能正常。")
        return True
    else:
        print(f"⚠ {total - passed} 个测试失败，请检查相关功能。")
        return False

def main():
    """主函数"""
    try:
        success = run_simple_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n测试运行异常: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()