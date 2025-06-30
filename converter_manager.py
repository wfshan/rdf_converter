#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据转换管理器

统一管理各种数据格式之间的转换
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

from base_converter import BaseRDFConverter
from graph_to_rdf import GraphToRDFConverter
from text_to_rdf import TextToRDFConverter
from rdf_to_text import RDFToTextConverter
from rdf_to_graph import RDFToGraphConverter

logger = logging.getLogger(__name__)

class RDFConverterManager:
    """RDF转换管理器
    
    统一管理各种数据格式之间的转换，提供简单易用的接口
    """
    
    def __init__(self, base_uri: str = "http://example.org/kg/", use_llm: bool = True):
        self.base_uri = base_uri
        self.use_llm = use_llm
        
        # 初始化各种转换器
        self.graph_to_rdf = GraphToRDFConverter(base_uri)
        self.text_to_rdf = TextToRDFConverter(base_uri, use_llm)
        self.rdf_to_text = RDFToTextConverter(base_uri, use_llm)
        self.rdf_to_graph = RDFToGraphConverter(base_uri)
        
        # 当前活跃的RDF图
        self.current_rdf = None
        self.current_converter = None
        
        logger.info(f"RDF转换管理器初始化完成，基础URI: {base_uri}")
    
    def convert_to_rdf(self, data: Any, source_format: str, 
                      output_file: str = None) -> bool:
        """将数据转换为RDF格式
        
        Args:
            data: 输入数据
            source_format: 源数据格式 ('text', 'graph_networkx', 'graph_json', 'graph_cypher', 'excel')
            output_file: 输出文件路径（可选）
        
        Returns:
            转换是否成功
        """
        try:
            if source_format.startswith('text'):
                converter = self.text_to_rdf
            elif source_format.startswith('graph'):
                converter = self.graph_to_rdf
            else:
                logger.error(f"不支持的源格式: {source_format}")
                return False
            
            # 执行转换
            success = converter.convert_to_rdf(data, source_format.split('_')[-1] if '_' in source_format else 'auto')
            
            if success:
                self.current_rdf = converter.graph
                self.current_converter = converter
                
                # 保存到文件
                if output_file:
                    converter.save_rdf(output_file)
                
                logger.info(f"成功转换为RDF格式，三元组数量: {len(converter.graph)}")
                return True
            else:
                logger.error("转换为RDF失败")
                return False
                
        except Exception as e:
            logger.error(f"转换为RDF时发生异常: {e}")
            return False
    
    def convert_from_rdf(self, target_format: str, rdf_file: str = None, 
                        output_file: str = None) -> Any:
        """从RDF转换为其他格式
        
        Args:
            target_format: 目标格式 ('text_narrative', 'text_summary', 'text_report', 
                         'graph_networkx', 'graph_json', 'graph_cypher', etc.)
            rdf_file: RDF文件路径（如果不使用当前RDF）
            output_file: 输出文件路径（可选）
        
        Returns:
            转换结果
        """
        try:
            # 确定使用哪个RDF图
            if rdf_file:
                # 加载指定的RDF文件
                if target_format.startswith('text'):
                    converter = self.rdf_to_text
                else:
                    converter = self.rdf_to_graph
                
                converter.load_rdf(rdf_file)
            else:
                # 使用当前RDF图
                if self.current_rdf is None:
                    logger.error("没有可用的RDF数据，请先转换数据为RDF或指定RDF文件")
                    return None
                
                if target_format.startswith('text'):
                    converter = self.rdf_to_text
                    converter.graph = self.current_rdf
                else:
                    converter = self.rdf_to_graph
                    converter.graph = self.current_rdf
            
            # 执行转换
            if target_format.startswith('text'):
                format_type = target_format.split('_', 1)[1] if '_' in target_format else 'narrative'
                result = converter.convert_from_rdf(format_type)
            else:
                format_type = target_format.split('_', 1)[1] if '_' in target_format else 'networkx'
                result = converter.convert_from_rdf(format_type)
            
            # 保存结果到文件
            if output_file and result is not None:
                self._save_result_to_file(result, output_file, target_format)
            
            logger.info(f"成功转换为{target_format}格式")
            return result
            
        except Exception as e:
            logger.error(f"从RDF转换时发生异常: {e}")
            return None
    
    def convert_direct(self, data: Any, source_format: str, target_format: str, 
                      output_file: str = None) -> Any:
        """直接转换（先转为RDF，再转为目标格式）
        
        Args:
            data: 输入数据
            source_format: 源格式
            target_format: 目标格式
            output_file: 输出文件路径（可选）
        
        Returns:
            转换结果
        """
        try:
            # 第一步：转换为RDF
            if not self.convert_to_rdf(data, source_format):
                return None
            
            # 第二步：从RDF转换为目标格式
            result = self.convert_from_rdf(target_format, output_file=output_file)
            
            return result
            
        except Exception as e:
            logger.error(f"直接转换时发生异常: {e}")
            return None
    
    def load_rdf_from_file(self, file_path: str) -> bool:
        """从文件加载RDF数据
        
        Args:
            file_path: RDF文件路径
        
        Returns:
            加载是否成功
        """
        try:
            # 使用text_to_rdf作为默认加载器
            success = self.text_to_rdf.load_rdf(file_path)
            
            if success:
                self.current_rdf = self.text_to_rdf.graph
                self.current_converter = self.text_to_rdf
                logger.info(f"成功加载RDF文件: {file_path}")
                return True
            else:
                logger.error(f"加载RDF文件失败: {file_path}")
                return False
                
        except Exception as e:
            logger.error(f"加载RDF文件时发生异常: {e}")
            return False
    
    def save_current_rdf(self, file_path: str, format: str = "turtle") -> bool:
        """保存当前RDF数据到文件
        
        Args:
            file_path: 输出文件路径
            format: RDF格式 ('turtle', 'xml', 'n3', 'nt', 'json-ld')
        
        Returns:
            保存是否成功
        """
        try:
            if self.current_converter is None:
                logger.error("没有可用的RDF数据")
                return False
            
            return self.current_converter.save_rdf(file_path, format)
            
        except Exception as e:
            logger.error(f"保存RDF文件时发生异常: {e}")
            return False
    
    def get_rdf_statistics(self) -> Dict[str, Any]:
        """获取当前RDF的统计信息
        
        Returns:
            统计信息字典
        """
        if self.current_converter is None:
            return {"error": "没有可用的RDF数据"}
        
        return self.current_converter.get_statistics()
    
    def query_rdf(self, sparql_query: str) -> List[Dict[str, Any]]:
        """查询当前RDF数据
        
        Args:
            sparql_query: SPARQL查询语句
        
        Returns:
            查询结果列表
        """
        if self.current_converter is None:
            logger.error("没有可用的RDF数据")
            return []
        
        return self.current_converter.query_sparql(sparql_query)
    
    def clear_rdf(self) -> None:
        """清空当前RDF数据"""
        if self.current_converter:
            self.current_converter.clear_graph()
        
        self.current_rdf = None
        self.current_converter = None
        logger.info("已清空RDF数据")
    
    def _save_result_to_file(self, result: Any, file_path: str, format_type: str) -> bool:
        """保存转换结果到文件
        
        Args:
            result: 转换结果
            file_path: 文件路径
            format_type: 格式类型
        
        Returns:
            保存是否成功
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            if format_type.startswith('text'):
                # 文本格式
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(str(result))
            
            elif format_type.endswith('json'):
                # JSON格式
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
            
            elif format_type.endswith('cypher'):
                # Cypher格式
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(str(result))
            
            else:
                # 其他格式，尝试直接写入
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(str(result))
            
            logger.info(f"结果已保存到文件: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"保存结果到文件失败: {e}")
            return False
    
    def get_supported_formats(self) -> Dict[str, List[str]]:
        """获取支持的格式列表
        
        Returns:
            支持的格式字典
        """
        return {
            'input_formats': [
                'text',
                'graph_networkx',
                'graph_json', 
                'graph_cypher',
                'excel'
            ],
            'output_formats': [
                'text_narrative',
                'text_summary',
                'text_report',
                'text_qa',
                'text_structured',
                'graph_networkx',
                'graph_json',
                'graph_cypher',
                'graph_gexf',
                'graph_graphml',
                'graph_edgelist',
                'graph_adjacency'
            ],
            'rdf_formats': [
                'turtle',
                'xml',
                'n3',
                'nt',
                'json-ld'
            ]
        }
    
    def batch_convert(self, input_dir: str, output_dir: str, 
                     source_format: str, target_format: str) -> Dict[str, bool]:
        """批量转换文件
        
        Args:
            input_dir: 输入目录
            output_dir: 输出目录
            source_format: 源格式
            target_format: 目标格式
        
        Returns:
            转换结果字典（文件名 -> 是否成功）
        """
        results = {}
        
        try:
            input_path = Path(input_dir)
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # 获取所有输入文件
            if source_format == 'text':
                file_pattern = '*.txt'
            elif source_format.startswith('graph'):
                if source_format.endswith('json'):
                    file_pattern = '*.json'
                elif source_format.endswith('cypher'):
                    file_pattern = '*.cypher'
                else:
                    file_pattern = '*.*'
            else:
                file_pattern = '*.*'
            
            input_files = list(input_path.glob(file_pattern))
            
            for input_file in input_files:
                try:
                    # 读取输入文件
                    if source_format == 'text':
                        with open(input_file, 'r', encoding='utf-8') as f:
                            data = f.read()
                    elif source_format.endswith('json'):
                        with open(input_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                    else:
                        with open(input_file, 'r', encoding='utf-8') as f:
                            data = f.read()
                    
                    # 确定输出文件名
                    if target_format.startswith('text'):
                        output_file = output_path / f"{input_file.stem}.txt"
                    elif target_format.endswith('json'):
                        output_file = output_path / f"{input_file.stem}.json"
                    elif target_format.endswith('cypher'):
                        output_file = output_path / f"{input_file.stem}.cypher"
                    else:
                        output_file = output_path / f"{input_file.stem}_converted.txt"
                    
                    # 执行转换
                    result = self.convert_direct(data, source_format, target_format, str(output_file))
                    
                    results[input_file.name] = result is not None
                    
                    if result is not None:
                        logger.info(f"成功转换文件: {input_file.name}")
                    else:
                        logger.error(f"转换文件失败: {input_file.name}")
                
                except Exception as e:
                    logger.error(f"处理文件 {input_file.name} 时发生异常: {e}")
                    results[input_file.name] = False
            
            success_count = sum(results.values())
            total_count = len(results)
            logger.info(f"批量转换完成: {success_count}/{total_count} 个文件成功")
            
            return results
            
        except Exception as e:
            logger.error(f"批量转换时发生异常: {e}")
            return {}
    
    def create_conversion_pipeline(self, steps: List[Dict[str, str]]) -> bool:
        """创建转换流水线
        
        Args:
            steps: 转换步骤列表，每个步骤包含 {'action': 'convert_to_rdf'/'convert_from_rdf', 
                                        'format': '格式', 'output': '输出文件'}
        
        Returns:
            流水线执行是否成功
        """
        try:
            for i, step in enumerate(steps):
                action = step.get('action')
                format_type = step.get('format')
                output_file = step.get('output')
                
                logger.info(f"执行流水线步骤 {i+1}: {action} -> {format_type}")
                
                if action == 'convert_to_rdf':
                    # 这里需要数据输入，暂时跳过
                    logger.warning("流水线中的convert_to_rdf步骤需要数据输入")
                    continue
                
                elif action == 'convert_from_rdf':
                    result = self.convert_from_rdf(format_type, output_file=output_file)
                    if result is None:
                        logger.error(f"流水线步骤 {i+1} 失败")
                        return False
                
                else:
                    logger.error(f"未知的流水线动作: {action}")
                    return False
            
            logger.info("转换流水线执行完成")
            return True
            
        except Exception as e:
            logger.error(f"执行转换流水线时发生异常: {e}")
            return False


# 便捷函数
def quick_convert(data: Any, source_format: str, target_format: str, 
                 output_file: str = None, base_uri: str = "http://example.org/kg/", 
                 use_llm: bool = True) -> Any:
    """快速转换函数
    
    Args:
        data: 输入数据
        source_format: 源格式
        target_format: 目标格式
        output_file: 输出文件路径（可选）
        base_uri: 基础URI
        use_llm: 是否使用大模型
    
    Returns:
        转换结果
    """
    manager = RDFConverterManager(base_uri, use_llm)
    return manager.convert_direct(data, source_format, target_format, output_file)


def convert_file(input_file: str, output_file: str, source_format: str, 
                target_format: str, base_uri: str = "http://example.org/kg/", 
                use_llm: bool = True) -> bool:
    """文件转换函数
    
    Args:
        input_file: 输入文件路径
        output_file: 输出文件路径
        source_format: 源格式
        target_format: 目标格式
        base_uri: 基础URI
        use_llm: 是否使用大模型
    
    Returns:
        转换是否成功
    """
    try:
        # 读取输入文件
        if source_format == 'text':
            with open(input_file, 'r', encoding='utf-8') as f:
                data = f.read()
        elif source_format.endswith('json'):
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            with open(input_file, 'r', encoding='utf-8') as f:
                data = f.read()
        
        # 执行转换
        result = quick_convert(data, source_format, target_format, output_file, base_uri, use_llm)
        
        return result is not None
        
    except Exception as e:
        logger.error(f"文件转换失败: {e}")
        return False