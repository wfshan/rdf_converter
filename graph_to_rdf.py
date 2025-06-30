#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图谱数据转RDF转换器

支持从各种图数据格式（Neo4j、NetworkX、JSON等）转换为RDF
"""

import json
import logging
from typing import Dict, List, Any, Optional, Union
from urllib.parse import quote

import networkx as nx
import pandas as pd
from rdflib import URIRef, Literal, BNode
from rdflib.namespace import RDF, RDFS, OWL, XSD

from base_converter import BaseRDFConverter

logger = logging.getLogger(__name__)

class GraphToRDFConverter(BaseRDFConverter):
    """图谱数据转RDF转换器"""
    
    def __init__(self, base_uri: str = "http://example.org/kg/"):
        super().__init__(base_uri)
        self.node_uri_map = {}  # 节点ID到URI的映射
        self.edge_counter = 0   # 边的计数器
    
    def convert_to_rdf(self, data: Any, data_type: str = "networkx") -> bool:
        """转换图数据到RDF格式
        
        Args:
            data: 图数据
            data_type: 数据类型 ('networkx', 'cypher_result', 'json_graph', 'excel')
        """
        try:
            if data_type == "networkx":
                return self._convert_networkx_to_rdf(data)
            elif data_type == "cypher_result":
                return self._convert_cypher_result_to_rdf(data)
            elif data_type == "json_graph":
                return self._convert_json_graph_to_rdf(data)
            elif data_type == "excel":
                return self._convert_excel_to_rdf(data)
            else:
                logger.error(f"不支持的数据类型: {data_type}")
                return False
        except Exception as e:
            logger.error(f"转换图数据到RDF失败: {e}")
            return False
    
    def _convert_networkx_to_rdf(self, graph: nx.Graph) -> bool:
        """转换NetworkX图到RDF"""
        logger.info(f"开始转换NetworkX图，节点数: {graph.number_of_nodes()}, 边数: {graph.number_of_edges()}")
        
        # 转换节点
        for node_id, node_data in graph.nodes(data=True):
            self._add_node_to_rdf(node_id, node_data)
        
        # 转换边
        for source, target, edge_data in graph.edges(data=True):
            self._add_edge_to_rdf(source, target, edge_data)
        
        logger.info(f"NetworkX图转换完成，生成 {len(self.graph)} 个三元组")
        return True
    
    def _convert_cypher_result_to_rdf(self, cypher_result: List[Dict]) -> bool:
        """转换Cypher查询结果到RDF"""
        logger.info(f"开始转换Cypher结果，记录数: {len(cypher_result)}")
        
        for record in cypher_result:
            for key, value in record.items():
                if isinstance(value, dict) and 'labels' in value:
                    # 这是一个节点
                    self._add_node_to_rdf(value.get('id', key), value)
                elif isinstance(value, dict) and 'type' in value:
                    # 这是一个关系
                    self._add_relationship_to_rdf(value)
        
        logger.info(f"Cypher结果转换完成，生成 {len(self.graph)} 个三元组")
        return True
    
    def _convert_json_graph_to_rdf(self, json_data: Union[str, Dict]) -> bool:
        """转换JSON图数据到RDF"""
        if isinstance(json_data, str):
            json_data = json.loads(json_data)
        
        logger.info("开始转换JSON图数据")
        
        # 处理节点
        if 'nodes' in json_data:
            for node in json_data['nodes']:
                node_id = node.get('id', node.get('name'))
                self._add_node_to_rdf(node_id, node)
        
        # 处理边
        if 'edges' in json_data:
            for edge in json_data['edges']:
                source = edge.get('source', edge.get('from'))
                target = edge.get('target', edge.get('to'))
                self._add_edge_to_rdf(source, target, edge)
        
        # 处理links（另一种边的表示）
        if 'links' in json_data:
            for link in json_data['links']:
                source = link.get('source', link.get('from'))
                target = link.get('target', link.get('to'))
                self._add_edge_to_rdf(source, target, link)
        
        logger.info(f"JSON图数据转换完成，生成 {len(self.graph)} 个三元组")
        return True
    
    def _convert_excel_to_rdf(self, file_path: str) -> bool:
        """转换Excel文件到RDF"""
        logger.info(f"开始转换Excel文件: {file_path}")
        
        try:
            # 读取节点表
            if 'nodes' in pd.ExcelFile(file_path).sheet_names:
                nodes_df = pd.read_excel(file_path, sheet_name='nodes')
                for _, row in nodes_df.iterrows():
                    node_id = row.get('id', row.get('name'))
                    node_data = row.to_dict()
                    self._add_node_to_rdf(node_id, node_data)
            
            # 读取边表
            if 'edges' in pd.ExcelFile(file_path).sheet_names:
                edges_df = pd.read_excel(file_path, sheet_name='edges')
                for _, row in edges_df.iterrows():
                    source = row.get('source', row.get('from'))
                    target = row.get('target', row.get('to'))
                    edge_data = row.to_dict()
                    self._add_edge_to_rdf(source, target, edge_data)
            
            # 如果只有一个表，尝试推断结构
            else:
                df = pd.read_excel(file_path)
                self._infer_graph_from_dataframe(df)
            
            logger.info(f"Excel文件转换完成，生成 {len(self.graph)} 个三元组")
            return True
        
        except Exception as e:
            logger.error(f"转换Excel文件失败: {e}")
            return False
    
    def _add_node_to_rdf(self, node_id: Any, node_data: Dict[str, Any]):
        """添加节点到RDF图"""
        # 创建节点URI
        node_uri = self._get_or_create_node_uri(node_id)
        
        # 获取节点类型
        node_labels = node_data.get('labels', node_data.get('label', ['Entity']))
        if isinstance(node_labels, str):
            node_labels = [node_labels]
        
        # 添加类型信息
        for label in node_labels:
            class_uri = self.create_uri(self._sanitize_name(label))
            self.add_triple(node_uri, RDF.type, class_uri)
            
            # 确保类存在
            self.add_class(class_uri, label)
        
        # 添加属性
        for key, value in node_data.items():
            if key in ['id', 'labels', 'label']:
                continue
            
            prop_uri = self.create_uri(self._sanitize_name(key))
            
            if isinstance(value, (str, int, float, bool)):
                self.add_triple(node_uri, prop_uri, Literal(value))
            elif isinstance(value, list):
                for item in value:
                    self.add_triple(node_uri, prop_uri, Literal(item))
            else:
                self.add_triple(node_uri, prop_uri, Literal(str(value)))
    
    def _add_edge_to_rdf(self, source: Any, target: Any, edge_data: Dict[str, Any]):
        """添加边到RDF图"""
        source_uri = self._get_or_create_node_uri(source)
        target_uri = self._get_or_create_node_uri(target)
        
        # 获取关系类型
        relation_type = edge_data.get('type', edge_data.get('relation', edge_data.get('label', 'relatedTo')))
        relation_uri = self.create_uri(self._sanitize_name(relation_type))
        
        # 如果边有其他属性，创建一个边实例
        edge_properties = {k: v for k, v in edge_data.items() 
                          if k not in ['type', 'relation', 'label', 'source', 'target', 'from', 'to']}
        
        if edge_properties:
            # 创建边实例
            edge_uri = self.create_uri(f"edge_{self.edge_counter}")
            self.edge_counter += 1
            
            # 添加边类型
            edge_class_uri = self.create_uri(f"{relation_type}_Edge")
            self.add_triple(edge_uri, RDF.type, edge_class_uri)
            
            # 连接源和目标
            self.add_triple(edge_uri, self.create_uri('hasSource'), source_uri)
            self.add_triple(edge_uri, self.create_uri('hasTarget'), target_uri)
            
            # 添加边属性
            for key, value in edge_properties.items():
                prop_uri = self.create_uri(self._sanitize_name(key))
                if isinstance(value, (str, int, float, bool)):
                    self.add_triple(edge_uri, prop_uri, Literal(value))
                else:
                    self.add_triple(edge_uri, prop_uri, Literal(str(value)))
        else:
            # 简单的直接关系
            self.add_triple(source_uri, relation_uri, target_uri)
    
    def _add_relationship_to_rdf(self, relationship: Dict[str, Any]):
        """添加Neo4j关系到RDF"""
        source_id = relationship.get('startNode')
        target_id = relationship.get('endNode')
        rel_type = relationship.get('type')
        
        if source_id and target_id and rel_type:
            source_uri = self._get_or_create_node_uri(source_id)
            target_uri = self._get_or_create_node_uri(target_id)
            relation_uri = self.create_uri(self._sanitize_name(rel_type))
            
            self.add_triple(source_uri, relation_uri, target_uri)
            
            # 添加关系属性
            properties = relationship.get('properties', {})
            if properties:
                edge_uri = self.create_uri(f"edge_{self.edge_counter}")
                self.edge_counter += 1
                
                self.add_triple(edge_uri, RDF.type, self.create_uri(f"{rel_type}_Edge"))
                self.add_triple(edge_uri, self.create_uri('hasSource'), source_uri)
                self.add_triple(edge_uri, self.create_uri('hasTarget'), target_uri)
                
                for key, value in properties.items():
                    prop_uri = self.create_uri(self._sanitize_name(key))
                    self.add_triple(edge_uri, prop_uri, Literal(value))
    
    def _infer_graph_from_dataframe(self, df: pd.DataFrame):
        """从DataFrame推断图结构"""
        # 尝试识别实体列和关系列
        entity_columns = []
        relation_columns = []
        
        for col in df.columns:
            col_lower = col.lower()
            if any(keyword in col_lower for keyword in ['entity', 'node', 'subject', 'object']):
                entity_columns.append(col)
            elif any(keyword in col_lower for keyword in ['relation', 'predicate', 'edge', 'link']):
                relation_columns.append(col)
        
        # 如果没有明确的列，使用前三列作为主语-谓语-宾语
        if not entity_columns and not relation_columns and len(df.columns) >= 3:
            for _, row in df.iterrows():
                subject = row.iloc[0]
                predicate = row.iloc[1]
                obj = row.iloc[2]
                
                subject_uri = self._get_or_create_node_uri(subject)
                predicate_uri = self.create_uri(self._sanitize_name(str(predicate)))
                
                if isinstance(obj, str) and not obj.isdigit():
                    object_uri = self._get_or_create_node_uri(obj)
                    self.add_triple(subject_uri, predicate_uri, object_uri)
                else:
                    self.add_triple(subject_uri, predicate_uri, Literal(obj))
    
    def _get_or_create_node_uri(self, node_id: Any) -> URIRef:
        """获取或创建节点URI"""
        if node_id not in self.node_uri_map:
            sanitized_id = self._sanitize_name(str(node_id))
            self.node_uri_map[node_id] = self.create_uri(f"entity_{sanitized_id}")
        return self.node_uri_map[node_id]
    
    def _sanitize_name(self, name: str) -> str:
        """清理名称，使其适合作为URI的一部分"""
        # 移除或替换特殊字符
        import re
        sanitized = re.sub(r'[^\w\u4e00-\u9fff]', '_', str(name))
        sanitized = re.sub(r'_+', '_', sanitized)
        sanitized = sanitized.strip('_')
        return quote(sanitized, safe='')
    
    def convert_from_rdf(self, target_format: str = "networkx") -> Any:
        """从RDF转换为图格式"""
        if target_format == "networkx":
            return self._convert_rdf_to_networkx()
        elif target_format == "json":
            return self._convert_rdf_to_json()
        elif target_format == "cypher":
            return self._convert_rdf_to_cypher()
        else:
            logger.error(f"不支持的目标格式: {target_format}")
            return None
    
    def _convert_rdf_to_networkx(self) -> nx.Graph:
        """转换RDF到NetworkX图"""
        graph = nx.Graph()
        
        # 查询所有实体
        entity_query = """
        SELECT DISTINCT ?entity ?type ?label
        WHERE {
            ?entity a ?type .
            OPTIONAL { ?entity rdfs:label ?label }
        }
        """
        
        entities = self.query_sparql(entity_query)
        for entity in entities:
            node_id = str(entity['entity'])
            node_data = {
                'type': str(entity['type']),
                'label': str(entity.get('label', node_id))
            }
            graph.add_node(node_id, **node_data)
        
        # 查询所有关系
        relation_query = """
        SELECT ?subject ?predicate ?object
        WHERE {
            ?subject ?predicate ?object .
            FILTER(isURI(?object))
        }
        """
        
        relations = self.query_sparql(relation_query)
        for relation in relations:
            subject = str(relation['subject'])
            predicate = str(relation['predicate'])
            obj = str(relation['object'])
            
            if subject in graph.nodes and obj in graph.nodes:
                graph.add_edge(subject, obj, relation=predicate)
        
        return graph
    
    def _convert_rdf_to_json(self) -> Dict[str, Any]:
        """转换RDF到JSON图格式"""
        nodes = []
        edges = []
        
        # 获取所有节点
        entity_query = """
        SELECT DISTINCT ?entity ?type ?label
        WHERE {
            ?entity a ?type .
            OPTIONAL { ?entity rdfs:label ?label }
        }
        """
        
        entities = self.query_sparql(entity_query)
        for entity in entities:
            node = {
                'id': str(entity['entity']),
                'type': str(entity['type']),
                'label': str(entity.get('label', entity['entity']))
            }
            nodes.append(node)
        
        # 获取所有边
        relation_query = """
        SELECT ?subject ?predicate ?object
        WHERE {
            ?subject ?predicate ?object .
            FILTER(isURI(?object))
        }
        """
        
        relations = self.query_sparql(relation_query)
        for relation in relations:
            edge = {
                'source': str(relation['subject']),
                'target': str(relation['object']),
                'type': str(relation['predicate'])
            }
            edges.append(edge)
        
        return {
            'nodes': nodes,
            'edges': edges
        }
    
    def _convert_rdf_to_cypher(self) -> List[str]:
        """转换RDF到Cypher语句"""
        cypher_statements = []
        
        # 创建节点的Cypher语句
        entity_query = """
        SELECT DISTINCT ?entity ?type ?label
        WHERE {
            ?entity a ?type .
            OPTIONAL { ?entity rdfs:label ?label }
        }
        """
        
        entities = self.query_sparql(entity_query)
        for entity in entities:
            entity_id = str(entity['entity']).split('/')[-1]
            entity_type = str(entity['type']).split('/')[-1]
            label = str(entity.get('label', entity_id))
            
            cypher = f"CREATE (:{entity_type} {{id: '{entity_id}', label: '{label}'}})"
            cypher_statements.append(cypher)
        
        # 创建关系的Cypher语句
        relation_query = """
        SELECT ?subject ?predicate ?object
        WHERE {
            ?subject ?predicate ?object .
            FILTER(isURI(?object))
        }
        """
        
        relations = self.query_sparql(relation_query)
        for relation in relations:
            subject_id = str(relation['subject']).split('/')[-1]
            predicate = str(relation['predicate']).split('/')[-1]
            object_id = str(relation['object']).split('/')[-1]
            
            cypher = f"MATCH (a {{id: '{subject_id}'}}), (b {{id: '{object_id}'}}) CREATE (a)-[:{predicate}]->(b)"
            cypher_statements.append(cypher)
        
        return cypher_statements