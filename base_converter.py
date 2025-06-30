#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RDF转换器基类

提供RDF数据转换的基础功能和通用接口
"""

import os
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union, Tuple
from pathlib import Path

import rdflib
from rdflib import Graph, Namespace, URIRef, Literal, BNode
from rdflib.namespace import RDF, RDFS, OWL, XSD, SKOS, DCTERMS
import pandas as pd
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BaseRDFConverter(ABC):
    """RDF转换器基类"""
    
    def __init__(self, base_uri: str = "http://example.org/kg/"):
        self.base_uri = base_uri
        self.graph = Graph()
        self.namespaces = self._init_namespaces()
        self._bind_namespaces()
        
    def _init_namespaces(self) -> Dict[str, Namespace]:
        """初始化命名空间"""
        return {
            'kg': Namespace(self.base_uri),
            'rdf': RDF,
            'rdfs': RDFS,
            'owl': OWL,
            'xsd': XSD,
            'skos': SKOS,
            'dcterms': DCTERMS,
            'foaf': Namespace('http://xmlns.com/foaf/0.1/'),
            'schema': Namespace('http://schema.org/'),
            'finance': Namespace('http://example.org/finance/'),
            'aml': Namespace('http://example.org/aml/'),
            'risk': Namespace('http://example.org/risk/')
        }
    
    def _bind_namespaces(self):
        """绑定命名空间到图"""
        for prefix, namespace in self.namespaces.items():
            self.graph.bind(prefix, namespace)
    
    def create_uri(self, local_name: str, namespace: str = 'kg') -> URIRef:
        """创建URI引用"""
        if namespace in self.namespaces:
            return self.namespaces[namespace][local_name]
        else:
            return URIRef(f"{self.base_uri}{local_name}")
    
    def add_triple(self, subject: Union[URIRef, BNode], 
                   predicate: URIRef, 
                   obj: Union[URIRef, Literal, BNode]):
        """添加三元组到图"""
        self.graph.add((subject, predicate, obj))
    
    def add_class(self, class_uri: URIRef, label: str = None, 
                  comment: str = None, parent_class: URIRef = None):
        """添加类定义"""
        self.add_triple(class_uri, RDF.type, OWL.Class)
        
        if label:
            self.add_triple(class_uri, RDFS.label, Literal(label, lang='zh'))
        
        if comment:
            self.add_triple(class_uri, RDFS.comment, Literal(comment, lang='zh'))
        
        if parent_class:
            self.add_triple(class_uri, RDFS.subClassOf, parent_class)
    
    def add_property(self, property_uri: URIRef, label: str = None,
                     comment: str = None, domain: URIRef = None,
                     range_: URIRef = None, property_type: URIRef = OWL.ObjectProperty):
        """添加属性定义"""
        self.add_triple(property_uri, RDF.type, property_type)
        
        if label:
            self.add_triple(property_uri, RDFS.label, Literal(label, lang='zh'))
        
        if comment:
            self.add_triple(property_uri, RDFS.comment, Literal(comment, lang='zh'))
        
        if domain:
            self.add_triple(property_uri, RDFS.domain, domain)
        
        if range_:
            self.add_triple(property_uri, RDFS.range, range_)
    
    def add_individual(self, individual_uri: URIRef, class_uri: URIRef,
                       label: str = None, properties: Dict[URIRef, Any] = None):
        """添加个体实例"""
        self.add_triple(individual_uri, RDF.type, class_uri)
        
        if label:
            self.add_triple(individual_uri, RDFS.label, Literal(label, lang='zh'))
        
        if properties:
            for prop, value in properties.items():
                if isinstance(value, str):
                    self.add_triple(individual_uri, prop, Literal(value))
                elif isinstance(value, (int, float)):
                    self.add_triple(individual_uri, prop, Literal(value))
                elif isinstance(value, URIRef):
                    self.add_triple(individual_uri, prop, value)
                else:
                    self.add_triple(individual_uri, prop, Literal(str(value)))
    
    def load_from_file(self, file_path: str, format: str = None) -> bool:
        """从文件加载RDF数据"""
        try:
            if format is None:
                # 根据文件扩展名推断格式
                ext = Path(file_path).suffix.lower()
                format_map = {
                    '.rdf': 'xml',
                    '.xml': 'xml',
                    '.ttl': 'turtle',
                    '.n3': 'n3',
                    '.nt': 'nt',
                    '.jsonld': 'json-ld'
                }
                format = format_map.get(ext, 'turtle')
            
            self.graph.parse(file_path, format=format)
            logger.info(f"成功从 {file_path} 加载了 {len(self.graph)} 个三元组")
            return True
        except Exception as e:
            logger.error(f"加载文件 {file_path} 失败: {e}")
            return False
    
    def save_to_file(self, file_path: str, format: str = 'turtle') -> bool:
        """保存RDF数据到文件"""
        try:
            # 确保目录存在
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            self.graph.serialize(destination=file_path, format=format)
            logger.info(f"成功保存 {len(self.graph)} 个三元组到 {file_path}")
            return True
        except Exception as e:
            logger.error(f"保存文件 {file_path} 失败: {e}")
            return False
    
    def query_sparql(self, query: str) -> List[Dict[str, Any]]:
        """执行SPARQL查询"""
        try:
            results = self.graph.query(query)
            return [dict(row.asdict()) for row in results]
        except Exception as e:
            logger.error(f"SPARQL查询失败: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, int]:
        """获取图的统计信息"""
        stats = {
            'total_triples': len(self.graph),
            'classes': 0,
            'properties': 0,
            'individuals': 0
        }
        
        # 统计类的数量
        class_query = """
        SELECT (COUNT(DISTINCT ?class) as ?count)
        WHERE {
            ?class a owl:Class .
        }
        """
        result = self.query_sparql(class_query)
        if result:
            stats['classes'] = int(result[0]['count'])
        
        # 统计属性的数量
        property_query = """
        SELECT (COUNT(DISTINCT ?prop) as ?count)
        WHERE {
            { ?prop a owl:ObjectProperty } UNION
            { ?prop a owl:DatatypeProperty } UNION
            { ?prop a owl:AnnotationProperty }
        }
        """
        result = self.query_sparql(property_query)
        if result:
            stats['properties'] = int(result[0]['count'])
        
        # 统计个体的数量
        individual_query = """
        SELECT (COUNT(DISTINCT ?ind) as ?count)
        WHERE {
            ?ind a ?class .
            ?class a owl:Class .
        }
        """
        result = self.query_sparql(individual_query)
        if result:
            stats['individuals'] = int(result[0]['count'])
        
        return stats
    
    def clear_graph(self):
        """清空图"""
        self.graph = Graph()
        self._bind_namespaces()
    
    @abstractmethod
    def convert_to_rdf(self, data: Any) -> bool:
        """转换数据到RDF格式"""
        pass
    
    @abstractmethod
    def convert_from_rdf(self, target_format: str) -> Any:
        """从RDF格式转换数据"""
        pass
    
    def __str__(self) -> str:
        stats = self.get_statistics()
        return f"RDF图: {stats['total_triples']} 三元组, {stats['classes']} 类, {stats['properties']} 属性, {stats['individuals']} 个体"