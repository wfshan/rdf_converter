#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RDF数据转换包

提供完整的RDF数据转换功能，支持：
- 图谱数据到RDF的转换
- 自然语言到RDF的转换  
- RDF到自然语言的转换
- RDF到图谱数据的转换
"""

__version__ = "1.0.0"
__author__ = "RDF Converter Team"
__email__ = "contact@example.com"

# 导入主要类
from .base_converter import BaseRDFConverter
from .graph_to_rdf import GraphToRDFConverter
from .text_to_rdf import TextToRDFConverter
from .rdf_to_text import RDFToTextConverter
from .rdf_to_graph import RDFToGraphConverter
from .converter_manager import RDFConverterManager, quick_convert, convert_file

# 导出的公共接口
__all__ = [
    # 基础类
    'BaseRDFConverter',
    
    # 转换器类
    'GraphToRDFConverter',
    'TextToRDFConverter', 
    'RDFToTextConverter',
    'RDFToGraphConverter',
    
    # 管理器和便捷函数
    'RDFConverterManager',
    'quick_convert',
    'convert_file',
    
    # 版本信息
    '__version__',
    '__author__',
    '__email__'
]

# 设置日志
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 如果没有处理器，添加一个控制台处理器
if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)

# 包级别的便捷函数
def get_supported_formats():
    """获取支持的格式列表
    
    Returns:
        Dict: 支持的格式字典
    """
    manager = RDFConverterManager()
    return manager.get_supported_formats()

def create_converter_manager(base_uri="http://example.org/kg/", use_llm=True):
    """创建转换器管理器
    
    Args:
        base_uri (str): 基础URI
        use_llm (bool): 是否使用大模型
    
    Returns:
        RDFConverterManager: 转换器管理器实例
    """
    return RDFConverterManager(base_uri, use_llm)

# 包信息
print(f"RDF Converter Package v{__version__} loaded successfully!")
print("支持的转换类型:")
print("  - 图谱数据 ↔ RDF")
print("  - 自然语言 ↔ RDF")
print("  - RDF ↔ 各种格式")
print("\n使用示例:")
print("  from rdf_converter import RDFConverterManager")
print("  manager = RDFConverterManager()")
print("  result = manager.convert_direct(data, 'text', 'graph_json')")