#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RDF转图谱数据转换器

将RDF知识图谱转换为各种图数据格式
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from collections import defaultdict

from rdflib import URIRef, Literal, BNode
from rdflib.namespace import RDF, RDFS, OWL, XSD

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False
    nx = None

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None

from base_converter import BaseRDFConverter

logger = logging.getLogger(__name__)

class RDFToGraphConverter(BaseRDFConverter):
    """RDF转图谱数据转换器"""
    
    def __init__(self, base_uri: str = "http://example.org/kg/"):
        super().__init__(base_uri)
    
    def convert_from_rdf(self, target_format: str = "networkx") -> Any:
        """从RDF转换为图数据格式
        
        Args:
            target_format: 目标格式 ('networkx', 'cypher', 'json', 'gexf', 'graphml', 'edgelist', 'adjacency')
        """
        try:
            if target_format == "networkx":
                return self._convert_to_networkx()
            elif target_format == "cypher":
                return self._convert_to_cypher()
            elif target_format == "json":
                return self._convert_to_json()
            elif target_format == "gexf":
                return self._convert_to_gexf()
            elif target_format == "graphml":
                return self._convert_to_graphml()
            elif target_format == "edgelist":
                return self._convert_to_edgelist()
            elif target_format == "adjacency":
                return self._convert_to_adjacency_matrix()
            else:
                logger.error(f"不支持的目标格式: {target_format}")
                return None
        except Exception as e:
            logger.error(f"RDF转图数据失败: {e}")
            return None
    
    def convert_to_rdf(self, data: Any) -> bool:
        """此转换器主要用于RDF到图数据的转换"""
        logger.warning("RDFToGraphConverter主要用于RDF到图数据的转换")
        return False
    
    def _convert_to_networkx(self) -> Optional[Any]:
        """转换为NetworkX图"""
        if not NETWORKX_AVAILABLE:
            logger.error("NetworkX未安装，无法转换")
            return None
        
        # 创建有向图
        G = nx.DiGraph()
        
        # 获取所有实体
        entities = self._get_all_entities()
        
        # 添加节点
        for entity in entities:
            node_id = self._get_node_id(entity['uri'])
            G.add_node(node_id, **entity['attributes'])
        
        # 获取所有关系
        relations = self._get_all_relations_detailed()
        
        # 添加边
        for relation in relations:
            source_id = self._get_node_id(relation['subject'])
            target_id = self._get_node_id(relation['object'])
            edge_attrs = {
                'relation': relation['predicate'],
                'relation_uri': relation['predicate_uri']
            }
            
            # 如果对象是字面量，创建一个属性节点
            if relation.get('is_literal', False):
                literal_id = f"literal_{hash(relation['object'])}"
                G.add_node(literal_id, 
                          label=relation['object'], 
                          type='Literal',
                          datatype=relation.get('datatype', 'string'))
                G.add_edge(source_id, literal_id, **edge_attrs)
            else:
                G.add_edge(source_id, target_id, **edge_attrs)
        
        return G
    
    def _convert_to_cypher(self) -> str:
        """转换为Cypher语句"""
        cypher_statements = []
        
        # 创建节点的Cypher语句
        entities = self._get_all_entities()
        
        for entity in entities:
            node_id = self._get_node_id(entity['uri'])
            labels = entity['attributes'].get('types', ['Entity'])
            
            # 构建属性字符串
            props = []
            for key, value in entity['attributes'].items():
                if key != 'types':
                    if isinstance(value, str):
                        props.append(f"{key}: '{value}'")
                    else:
                        props.append(f"{key}: {value}")
            
            props_str = ", ".join(props)
            labels_str = ":".join(labels)
            
            cypher = f"CREATE (n_{node_id}:{labels_str} {{{props_str}}})"
            cypher_statements.append(cypher)
        
        # 创建关系的Cypher语句
        relations = self._get_all_relations_detailed()
        
        for relation in relations:
            if relation.get('is_literal', False):
                continue  # 跳过字面量关系
            
            source_id = self._get_node_id(relation['subject'])
            target_id = self._get_node_id(relation['object'])
            relation_type = relation['predicate'].upper()
            
            cypher = f"MATCH (a), (b) WHERE id(a) = {source_id} AND id(b) = {target_id} CREATE (a)-[:{relation_type}]->(b)"
            cypher_statements.append(cypher)
        
        return "\n".join(cypher_statements)
    
    def _convert_to_json(self) -> Dict[str, Any]:
        """转换为JSON格式"""
        # 获取节点数据
        entities = self._get_all_entities()
        nodes = []
        
        for entity in entities:
            node = {
                'id': self._get_node_id(entity['uri']),
                'uri': entity['uri'],
                'label': entity['attributes'].get('label', entity['uri'].split('/')[-1]),
                'type': entity['attributes'].get('types', ['Entity'])[0],
                'properties': {k: v for k, v in entity['attributes'].items() if k not in ['label', 'types']}
            }
            nodes.append(node)
        
        # 获取边数据
        relations = self._get_all_relations_detailed()
        edges = []
        
        for relation in relations:
            if relation.get('is_literal', False):
                # 处理字面量作为节点属性
                continue
            
            edge = {
                'source': self._get_node_id(relation['subject']),
                'target': self._get_node_id(relation['object']),
                'relation': relation['predicate'],
                'relation_uri': relation['predicate_uri']
            }
            edges.append(edge)
        
        return {
            'nodes': nodes,
            'edges': edges,
            'metadata': {
                'total_nodes': len(nodes),
                'total_edges': len(edges),
                'graph_type': 'directed'
            }
        }
    
    def _convert_to_gexf(self) -> str:
        """转换为GEXF格式"""
        if not NETWORKX_AVAILABLE:
            logger.error("NetworkX未安装，无法生成GEXF格式")
            return ""
        
        G = self._convert_to_networkx()
        if G is None:
            return ""
        
        try:
            from io import StringIO
            import xml.etree.ElementTree as ET
            
            # 使用NetworkX的write_gexf功能
            output = StringIO()
            nx.write_gexf(G, output)
            return output.getvalue()
        except Exception as e:
            logger.error(f"生成GEXF格式失败: {e}")
            return ""
    
    def _convert_to_graphml(self) -> str:
        """转换为GraphML格式"""
        if not NETWORKX_AVAILABLE:
            logger.error("NetworkX未安装，无法生成GraphML格式")
            return ""
        
        G = self._convert_to_networkx()
        if G is None:
            return ""
        
        try:
            from io import StringIO
            
            # 使用NetworkX的write_graphml功能
            output = StringIO()
            nx.write_graphml(G, output)
            return output.getvalue()
        except Exception as e:
            logger.error(f"生成GraphML格式失败: {e}")
            return ""
    
    def _convert_to_edgelist(self) -> List[Tuple[str, str, Dict[str, Any]]]:
        """转换为边列表格式"""
        relations = self._get_all_relations_detailed()
        edgelist = []
        
        for relation in relations:
            if relation.get('is_literal', False):
                continue
            
            source = self._get_node_id(relation['subject'])
            target = self._get_node_id(relation['object'])
            attrs = {
                'relation': relation['predicate'],
                'relation_uri': relation['predicate_uri']
            }
            
            edgelist.append((source, target, attrs))
        
        return edgelist
    
    def _convert_to_adjacency_matrix(self) -> Optional[Any]:
        """转换为邻接矩阵"""
        if not NETWORKX_AVAILABLE or not PANDAS_AVAILABLE:
            logger.error("NetworkX或Pandas未安装，无法生成邻接矩阵")
            return None
        
        G = self._convert_to_networkx()
        if G is None:
            return None
        
        try:
            # 生成邻接矩阵
            adj_matrix = nx.adjacency_matrix(G)
            
            # 转换为DataFrame以便查看
            nodes = list(G.nodes())
            df = pd.DataFrame(adj_matrix.toarray(), index=nodes, columns=nodes)
            
            return df
        except Exception as e:
            logger.error(f"生成邻接矩阵失败: {e}")
            return None
    
    def _get_all_entities(self) -> List[Dict[str, Any]]:
        """获取所有实体及其属性"""
        query = """
        SELECT DISTINCT ?entity
        WHERE {
            { ?entity a ?type . ?type a owl:Class . }
            UNION
            { ?entity ?p ?o . FILTER(isURI(?entity)) }
            UNION
            { ?s ?p ?entity . FILTER(isURI(?entity)) }
        }
        """
        
        results = self.query_sparql(query)
        entities = []
        
        for result in results:
            entity_uri = str(result['entity'])
            attributes = self._get_entity_attributes(entity_uri)
            
            entities.append({
                'uri': entity_uri,
                'attributes': attributes
            })
        
        return entities
    
    def _get_entity_attributes(self, entity_uri: str) -> Dict[str, Any]:
        """获取实体的所有属性"""
        attributes = {}
        
        # 获取类型
        type_query = f"""
        SELECT ?type
        WHERE {{
            <{entity_uri}> a ?type .
            ?type a owl:Class .
        }}
        """
        
        type_results = self.query_sparql(type_query)
        types = [str(r['type']).split('/')[-1] for r in type_results]
        if types:
            attributes['types'] = types
        
        # 获取标签
        label_query = f"""
        SELECT ?label
        WHERE {{
            <{entity_uri}> rdfs:label ?label .
        }}
        """
        
        label_results = self.query_sparql(label_query)
        if label_results:
            attributes['label'] = str(label_results[0]['label'])
        else:
            attributes['label'] = entity_uri.split('/')[-1]
        
        # 获取其他属性
        prop_query = f"""
        SELECT ?property ?value
        WHERE {{
            <{entity_uri}> ?property ?value .
            FILTER(?property != rdf:type && ?property != rdfs:label)
            FILTER(isLiteral(?value))
        }}
        """
        
        prop_results = self.query_sparql(prop_query)
        for result in prop_results:
            prop_name = str(result['property']).split('/')[-1]
            prop_value = str(result['value'])
            attributes[prop_name] = prop_value
        
        return attributes
    
    def _get_all_relations_detailed(self) -> List[Dict[str, Any]]:
        """获取所有关系的详细信息"""
        query = """
        SELECT ?subject ?predicate ?object
        WHERE {
            ?subject ?predicate ?object .
            FILTER(?predicate != rdf:type && ?predicate != rdfs:label && ?predicate != rdfs:comment)
        }
        """
        
        results = self.query_sparql(query)
        relations = []
        
        for result in results:
            subject_uri = str(result['subject'])
            predicate_uri = str(result['predicate'])
            object_value = result['object']
            
            relation = {
                'subject': subject_uri,
                'predicate': predicate_uri.split('/')[-1],
                'predicate_uri': predicate_uri,
                'object': str(object_value),
                'is_literal': isinstance(object_value, Literal)
            }
            
            if isinstance(object_value, Literal):
                relation['datatype'] = str(object_value.datatype) if object_value.datatype else 'string'
            
            relations.append(relation)
        
        return relations
    
    def _get_node_id(self, uri: str) -> str:
        """从URI生成节点ID"""
        return uri.split('/')[-1].replace('#', '_')
    
    def export_to_file(self, target_format: str, file_path: str) -> bool:
        """导出图数据到文件"""
        try:
            if target_format == "networkx_pickle":
                if not NETWORKX_AVAILABLE:
                    logger.error("NetworkX未安装")
                    return False
                
                G = self._convert_to_networkx()
                if G is None:
                    return False
                
                import pickle
                with open(file_path, 'wb') as f:
                    pickle.dump(G, f)
                
            elif target_format == "json":
                data = self._convert_to_json()
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            
            elif target_format == "cypher":
                cypher_statements = self._convert_to_cypher()
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(cypher_statements)
            
            elif target_format == "gexf":
                gexf_content = self._convert_to_gexf()
                if not gexf_content:
                    return False
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(gexf_content)
            
            elif target_format == "graphml":
                graphml_content = self._convert_to_graphml()
                if not graphml_content:
                    return False
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(graphml_content)
            
            elif target_format == "edgelist":
                edgelist = self._convert_to_edgelist()
                with open(file_path, 'w', encoding='utf-8') as f:
                    for source, target, attrs in edgelist:
                        f.write(f"{source}\t{target}\t{attrs['relation']}\n")
            
            elif target_format == "adjacency_csv":
                if not PANDAS_AVAILABLE:
                    logger.error("Pandas未安装")
                    return False
                
                adj_matrix = self._convert_to_adjacency_matrix()
                if adj_matrix is None:
                    return False
                
                adj_matrix.to_csv(file_path)
            
            else:
                logger.error(f"不支持的导出格式: {target_format}")
                return False
            
            logger.info(f"成功导出到文件: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"导出文件失败: {e}")
            return False
    
    def get_graph_statistics(self) -> Dict[str, Any]:
        """获取图统计信息"""
        stats = self.get_statistics()
        
        # 获取节点和边的详细统计
        entities = self._get_all_entities()
        relations = self._get_all_relations_detailed()
        
        # 统计节点类型
        node_types = defaultdict(int)
        for entity in entities:
            types = entity['attributes'].get('types', ['Unknown'])
            for t in types:
                node_types[t] += 1
        
        # 统计边类型
        edge_types = defaultdict(int)
        for relation in relations:
            if not relation.get('is_literal', False):
                edge_types[relation['predicate']] += 1
        
        # 计算度分布（如果NetworkX可用）
        degree_stats = {}
        if NETWORKX_AVAILABLE:
            G = self._convert_to_networkx()
            if G is not None:
                degrees = dict(G.degree())
                degree_stats = {
                    'average_degree': sum(degrees.values()) / len(degrees) if degrees else 0,
                    'max_degree': max(degrees.values()) if degrees else 0,
                    'min_degree': min(degrees.values()) if degrees else 0
                }
        
        return {
            'basic_stats': stats,
            'node_count': len(entities),
            'edge_count': len([r for r in relations if not r.get('is_literal', False)]),
            'literal_count': len([r for r in relations if r.get('is_literal', False)]),
            'node_types': dict(node_types),
            'edge_types': dict(edge_types),
            'degree_statistics': degree_stats
        }
    
    def visualize_graph(self, output_file: str = None, layout: str = "spring", 
                       node_size: int = 300, font_size: int = 8) -> bool:
        """可视化图谱"""
        if not NETWORKX_AVAILABLE:
            logger.error("NetworkX未安装，无法可视化")
            return False
        
        try:
            import matplotlib.pyplot as plt
            
            G = self._convert_to_networkx()
            if G is None:
                return False
            
            # 选择布局算法
            if layout == "spring":
                pos = nx.spring_layout(G, k=1, iterations=50)
            elif layout == "circular":
                pos = nx.circular_layout(G)
            elif layout == "random":
                pos = nx.random_layout(G)
            elif layout == "shell":
                pos = nx.shell_layout(G)
            else:
                pos = nx.spring_layout(G)
            
            # 绘制图
            plt.figure(figsize=(12, 8))
            
            # 绘制节点
            nx.draw_networkx_nodes(G, pos, node_size=node_size, 
                                 node_color='lightblue', alpha=0.7)
            
            # 绘制边
            nx.draw_networkx_edges(G, pos, alpha=0.5, arrows=True, 
                                 arrowsize=20, edge_color='gray')
            
            # 绘制标签
            labels = {node: G.nodes[node].get('label', node) for node in G.nodes()}
            nx.draw_networkx_labels(G, pos, labels, font_size=font_size)
            
            plt.title("RDF Knowledge Graph Visualization")
            plt.axis('off')
            
            if output_file:
                plt.savefig(output_file, dpi=300, bbox_inches='tight')
                logger.info(f"图谱可视化已保存到: {output_file}")
            else:
                plt.show()
            
            plt.close()
            return True
            
        except ImportError:
            logger.error("matplotlib未安装，无法可视化")
            return False
        except Exception as e:
            logger.error(f"可视化失败: {e}")
            return False