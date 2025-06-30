#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
转换器测试脚本

测试RDF转换器的基本功能
"""

import sys
import json
import logging
from pathlib import Path

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_imports():
    """测试模块导入"""
    print("\n=== 测试模块导入 ===")
    
    try:
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        from converter_manager import RDFConverterManager, quick_convert
        from base_converter import BaseRDFConverter
        from graph_to_rdf import GraphToRDFConverter
        from text_to_rdf import TextToRDFConverter
        from rdf_to_text import RDFToTextConverter
        from rdf_to_graph import RDFToGraphConverter
        
        print("✓ 所有模块导入成功")
        return True
    except ImportError as e:
        print(f"✗ 模块导入失败: {e}")
        return False

def test_basic_functionality():
    """测试基本功能"""
    print("\n=== 测试基本功能 ===")
    
    try:
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        from converter_manager import RDFConverterManager
        
        # 创建管理器
        manager = RDFConverterManager(use_llm=False)
        print("✓ 转换器管理器创建成功")
        
        # 测试文本转RDF
        test_text = "张三是一名工程师，在北京工作。李四是他的朋友。"
        success = manager.convert_to_rdf(test_text, 'text')
        
        if success:
            print("✓ 文本转RDF成功")
            
            # 获取统计信息
            stats = manager.get_rdf_statistics()
            print(f"  - 三元组数量: {stats.get('total_triples', 0)}")
            print(f"  - 实体数量: {stats.get('individuals', 0)}")
            
            # 测试RDF转文本
            summary = manager.convert_from_rdf('text_summary')
            if summary:
                print("✓ RDF转文本成功")
                print(f"  - 摘要长度: {len(summary)}字符")
            else:
                print("✗ RDF转文本失败")
            
            # 测试RDF转图数据
            graph_data = manager.convert_from_rdf('graph_json')
            if graph_data:
                print("✓ RDF转图数据成功")
                print(f"  - 节点数量: {len(graph_data.get('nodes', []))}")
                print(f"  - 边数量: {len(graph_data.get('edges', []))}")
            else:
                print("✗ RDF转图数据失败")
            
            return True
        else:
            print("✗ 文本转RDF失败")
            return False
            
    except Exception as e:
        print(f"✗ 基本功能测试失败: {e}")
        return False

def test_graph_conversion():
    """测试图数据转换"""
    print("\n=== 测试图数据转换 ===")
    
    try:
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        from converter_manager import RDFConverterManager
        
        # 创建测试图数据
        graph_data = {
            "nodes": [
                {"id": "person1", "label": "张三", "type": "Person", "properties": {"age": 30}},
                {"id": "person2", "label": "李四", "type": "Person", "properties": {"age": 28}},
                {"id": "company1", "label": "科技公司", "type": "Company"}
            ],
            "edges": [
                {"source": "person1", "target": "company1", "relation": "worksAt"},
                {"source": "person1", "target": "person2", "relation": "friendOf"}
            ]
        }
        
        manager = RDFConverterManager()
        
        # 图数据转RDF
        success = manager.convert_to_rdf(graph_data, 'graph_json')
        
        if success:
            print("✓ 图数据转RDF成功")
            
            # RDF转回图数据
            result_graph = manager.convert_from_rdf('graph_json')
            
            if result_graph:
                print("✓ RDF转回图数据成功")
                print(f"  - 原始节点: {len(graph_data['nodes'])}, 转换后节点: {len(result_graph['nodes'])}")
                print(f"  - 原始边: {len(graph_data['edges'])}, 转换后边: {len(result_graph['edges'])}")
                return True
            else:
                print("✗ RDF转回图数据失败")
                return False
        else:
            print("✗ 图数据转RDF失败")
            return False
            
    except Exception as e:
        print(f"✗ 图数据转换测试失败: {e}")
        return False

def test_networkx_integration():
    """测试NetworkX集成"""
    print("\n=== 测试NetworkX集成 ===")
    
    try:
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        import networkx as nx
        from converter_manager import RDFConverterManager
        
        # 创建NetworkX图
        G = nx.DiGraph()
        G.add_node("张三", type="Person", age=30)
        G.add_node("李四", type="Person", age=28)
        G.add_node("科技公司", type="Company")
        G.add_edge("张三", "科技公司", relation="worksAt")
        G.add_edge("张三", "李四", relation="friendOf")
        
        print(f"原始NetworkX图: {G.number_of_nodes()}个节点, {G.number_of_edges()}条边")
        
        manager = RDFConverterManager()
        
        # NetworkX转RDF
        success = manager.convert_to_rdf(G, 'graph_networkx')
        
        if success:
            print("✓ NetworkX转RDF成功")
            
            # RDF转回NetworkX
            result_G = manager.convert_from_rdf('graph_networkx')
            
            if result_G:
                print("✓ RDF转回NetworkX成功")
                print(f"转换后NetworkX图: {result_G.number_of_nodes()}个节点, {result_G.number_of_edges()}条边")
                return True
            else:
                print("✗ RDF转回NetworkX失败")
                return False
        else:
            print("✗ NetworkX转RDF失败")
            return False
            
    except ImportError:
        print("⚠ NetworkX未安装，跳过测试")
        return True
    except Exception as e:
        print(f"✗ NetworkX集成测试失败: {e}")
        return False

def test_sparql_query():
    """测试SPARQL查询"""
    print("\n=== 测试SPARQL查询 ===")
    
    try:
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        from converter_manager import RDFConverterManager
        
        # 创建测试数据
        manager = RDFConverterManager(use_llm=False)
        test_text = "张三是工程师，李四是医生。张三和李四是朋友。"
        
        success = manager.convert_to_rdf(test_text, 'text')
        
        if success:
            print("✓ 测试数据创建成功")
            
            # 测试简单查询
            query = """
            SELECT ?subject ?predicate ?object
            WHERE {
                ?subject ?predicate ?object .
            }
            LIMIT 5
            """
            
            results = manager.query_rdf(query)
            
            if results:
                print(f"✓ SPARQL查询成功，返回{len(results)}个结果")
                for i, result in enumerate(results[:3]):
                    print(f"  结果{i+1}: {result}")
                return True
            else:
                print("✗ SPARQL查询返回空结果")
                return False
        else:
            print("✗ 测试数据创建失败")
            return False
            
    except Exception as e:
        print(f"✗ SPARQL查询测试失败: {e}")
        return False

def test_file_operations():
    """测试文件操作"""
    print("\n=== 测试文件操作 ===")
    
    try:
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        from converter_manager import RDFConverterManager
        
        manager = RDFConverterManager(use_llm=False)
        
        # 创建测试数据
        test_text = "王五是一名教师，在学校工作。"
        success = manager.convert_to_rdf(test_text, 'text')
        
        if success:
            print("✓ 测试数据创建成功")
            
            # 保存RDF文件
            rdf_file = "test_output.ttl"
            save_success = manager.save_current_rdf(rdf_file)
            
            if save_success:
                print(f"✓ RDF文件保存成功: {rdf_file}")
                
                # 加载RDF文件
                new_manager = RDFConverterManager()
                load_success = new_manager.load_rdf_from_file(rdf_file)
                
                if load_success:
                    print("✓ RDF文件加载成功")
                    
                    # 验证数据
                    stats = new_manager.get_rdf_statistics()
                    print(f"  - 加载的三元组数量: {stats.get('total_triples', 0)}")
                    
                    # 清理测试文件
                    Path(rdf_file).unlink(missing_ok=True)
                    print("✓ 测试文件清理完成")
                    
                    return True
                else:
                    print("✗ RDF文件加载失败")
                    return False
            else:
                print("✗ RDF文件保存失败")
                return False
        else:
            print("✗ 测试数据创建失败")
            return False
            
    except Exception as e:
        print(f"✗ 文件操作测试失败: {e}")
        return False

def test_quick_convert():
    """测试快速转换函数"""
    print("\n=== 测试快速转换函数 ===")
    
    try:
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        from converter_manager import quick_convert
        
        # 测试文本到图数据的快速转换
        text = "赵六是一名设计师，在广告公司工作。"
        
        result = quick_convert(
            data=text,
            source_format='text',
            target_format='graph_json',
            use_llm=False
        )
        
        if result:
            print("✓ 快速转换成功")
            print(f"  - 节点数量: {len(result.get('nodes', []))}")
            print(f"  - 边数量: {len(result.get('edges', []))}")
            return True
        else:
            print("✗ 快速转换失败")
            return False
            
    except Exception as e:
        print(f"✗ 快速转换测试失败: {e}")
        return False

def test_error_handling():
    """测试错误处理"""
    print("\n=== 测试错误处理 ===")
    
    try:
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        from converter_manager import RDFConverterManager
        
        manager = RDFConverterManager()
        
        # 测试无效格式
        success = manager.convert_to_rdf("test", 'invalid_format')
        if not success:
            print("✓ 无效格式错误处理正确")
        else:
            print("✗ 无效格式错误处理失败")
            return False
        
        # 测试空数据转换
        result = manager.convert_from_rdf('text_summary')
        if result is None or result == "":
            print("✓ 空数据错误处理正确")
        else:
            print("✗ 空数据错误处理失败")
            return False
        
        # 测试无效SPARQL查询
        results = manager.query_rdf("INVALID SPARQL")
        if not results:
            print("✓ 无效SPARQL查询错误处理正确")
        else:
            print("✗ 无效SPARQL查询错误处理失败")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ 错误处理测试失败: {e}")
        return False

def run_all_tests():
    """运行所有测试"""
    print("RDF转换器测试套件")
    print("=" * 50)
    
    tests = [
        ("模块导入", test_imports),
        ("基本功能", test_basic_functionality),
        ("图数据转换", test_graph_conversion),
        ("NetworkX集成", test_networkx_integration),
        ("SPARQL查询", test_sparql_query),
        ("文件操作", test_file_operations),
        ("快速转换", test_quick_convert),
        ("错误处理", test_error_handling)
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
        print("🎉 所有测试通过！转换器工作正常。")
        return True
    else:
        print(f"⚠ {total - passed} 个测试失败，请检查相关功能。")
        return False

def main():
    """主函数"""
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n测试运行异常: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()