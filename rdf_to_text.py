#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RDF转自然语言转换器

将RDF知识图谱转换为自然语言描述
"""

import json
import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, Counter

from rdflib import URIRef, Literal, BNode
from rdflib.namespace import RDF, RDFS, OWL, XSD

from base_converter import BaseRDFConverter

# 尝试导入火山方舟LLM
try:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'text2code'))
    from volcengine_llm import VolcengineLLM
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    VolcengineLLM = None

logger = logging.getLogger(__name__)

class RDFToTextConverter(BaseRDFConverter):
    """RDF转自然语言转换器"""
    
    def __init__(self, base_uri: str = "http://example.org/kg/", use_llm: bool = True):
        super().__init__(base_uri)
        self.use_llm = use_llm and LLM_AVAILABLE
        self.llm = None
        
        if self.use_llm:
            try:
                self.llm = VolcengineLLM()
                logger.info("成功初始化火山方舟大模型")
            except Exception as e:
                logger.warning(f"初始化大模型失败，将使用模板方法: {e}")
                self.use_llm = False
        
        # 中文谓语映射
        self.predicate_translations = {
            'owns': '拥有',
            'worksAt': '工作于',
            'locatedAt': '位于',
            'occurredAt': '发生于',
            'participatesIn': '参与',
            'transfersTo': '转账给',
            'relatedTo': '关联',
            'controls': '控制',
            'invests': '投资',
            'cooperatesWith': '合作',
            'hasSource': '来源于',
            'hasTarget': '指向',
            'hasProperty': '具有属性',
            'hasValue': '的值为',
            'memberOf': '是...的成员',
            'partOf': '是...的一部分',
            'dependsOn': '依赖于',
            'causes': '导致',
            'follows': '跟随',
            'precedes': '先于'
        }
        
        # 实体类型的中文名称
        self.entity_type_translations = {
            'Person': '人员',
            'Company': '公司',
            'Organization': '组织',
            'Location': '地点',
            'Time': '时间',
            'Amount': '金额',
            'Account': '账户',
            'Transaction': '交易',
            'Product': '产品',
            'Event': '事件',
            'Entity': '实体'
        }
    
    def convert_from_rdf(self, target_format: str = "narrative") -> str:
        """从RDF转换为自然语言
        
        Args:
            target_format: 目标格式 ('narrative', 'summary', 'report', 'qa', 'structured')
        """
        try:
            if target_format == "narrative":
                return self._generate_narrative_text()
            elif target_format == "summary":
                return self._generate_summary_text()
            elif target_format == "report":
                return self._generate_report_text()
            elif target_format == "qa":
                return self._generate_qa_text()
            elif target_format == "structured":
                return self._generate_structured_text()
            else:
                logger.error(f"不支持的目标格式: {target_format}")
                return ""
        except Exception as e:
            logger.error(f"RDF转自然语言失败: {e}")
            return ""
    
    def convert_to_rdf(self, data: Any) -> bool:
        """此转换器主要用于RDF到文本的转换"""
        logger.warning("RDFToTextConverter主要用于RDF到文本的转换")
        return False
    
    def _generate_narrative_text(self) -> str:
        """生成叙述性文本"""
        if self.use_llm:
            return self._generate_narrative_with_llm()
        else:
            return self._generate_narrative_with_template()
    
    def _generate_narrative_with_llm(self) -> str:
        """使用大模型生成叙述性文本"""
        # 获取RDF数据的结构化表示
        structured_data = self._extract_structured_data()
        
        prompt = f"""
请根据以下知识图谱数据生成一段流畅的中文叙述文本。要求：
1. 语言自然流畅，符合中文表达习惯
2. 逻辑清晰，层次分明
3. 包含主要实体和关系信息
4. 避免重复和冗余

知识图谱数据：
{json.dumps(structured_data, ensure_ascii=False, indent=2)}

请生成叙述文本：
"""
        
        try:
            response = self.llm.chat_completion([
                {"role": "user", "content": prompt}
            ], temperature=0.7)
            
            if response.success:
                return response.content.strip()
            else:
                logger.error(f"LLM生成叙述文本失败: {response.error_message}")
                return self._generate_narrative_with_template()
        
        except Exception as e:
            logger.error(f"LLM生成叙述文本异常: {e}")
            return self._generate_narrative_with_template()
    
    def _generate_narrative_with_template(self) -> str:
        """使用模板生成叙述性文本"""
        sentences = []
        
        # 获取实体信息
        entities = self._get_entities_with_info()
        
        # 按类型分组实体
        entities_by_type = defaultdict(list)
        for entity in entities:
            entity_type = entity.get('type', 'Entity')
            entities_by_type[entity_type].append(entity)
        
        # 生成实体介绍
        for entity_type, entity_list in entities_by_type.items():
            type_name_zh = self.entity_type_translations.get(entity_type, entity_type)
            
            if len(entity_list) == 1:
                entity = entity_list[0]
                sentence = f"在这个知识图谱中，有一个{type_name_zh}叫做{entity['label']}。"
                sentences.append(sentence)
            else:
                entity_names = [e['label'] for e in entity_list[:5]]  # 最多列举5个
                if len(entity_list) > 5:
                    sentence = f"知识图谱中包含{len(entity_list)}个{type_name_zh}，主要有{' '.join(entity_names)}等。"
                else:
                    sentence = f"知识图谱中包含{len(entity_list)}个{type_name_zh}：{' '.join(entity_names)}。"
                sentences.append(sentence)
        
        # 生成关系描述
        relations = self._get_important_relations()
        
        for relation in relations[:10]:  # 最多描述10个重要关系
            subject_label = relation['subject_label']
            predicate = relation['predicate']
            object_label = relation['object_label']
            
            predicate_zh = self.predicate_translations.get(predicate, predicate)
            
            sentence = f"{subject_label}{predicate_zh}{object_label}。"
            sentences.append(sentence)
        
        return ''.join(sentences)
    
    def _generate_summary_text(self) -> str:
        """生成摘要文本"""
        stats = self.get_statistics()
        
        summary_parts = []
        
        # 基本统计信息
        summary_parts.append(f"该知识图谱共包含{stats['total_triples']}个知识三元组，")
        summary_parts.append(f"涉及{stats['individuals']}个实体实例，")
        summary_parts.append(f"{stats['classes']}种实体类型，")
        summary_parts.append(f"以及{stats['properties']}种关系类型。")
        
        # 主要实体类型统计
        type_stats = self._get_entity_type_statistics()
        if type_stats:
            summary_parts.append("\n\n主要实体类型分布：")
            for entity_type, count in type_stats[:5]:
                type_name_zh = self.entity_type_translations.get(entity_type, entity_type)
                summary_parts.append(f"{type_name_zh}({count}个)、")
            summary_parts[-1] = summary_parts[-1].rstrip('、') + '。'
        
        # 主要关系类型统计
        relation_stats = self._get_relation_type_statistics()
        if relation_stats:
            summary_parts.append("\n\n主要关系类型包括：")
            for relation_type, count in relation_stats[:5]:
                relation_name_zh = self.predicate_translations.get(relation_type, relation_type)
                summary_parts.append(f"{relation_name_zh}({count}次)、")
            summary_parts[-1] = summary_parts[-1].rstrip('、') + '。'
        
        return ''.join(summary_parts)
    
    def _generate_report_text(self) -> str:
        """生成报告格式文本"""
        report_parts = []
        
        # 报告标题
        report_parts.append("# 知识图谱分析报告\n\n")
        
        # 概述
        report_parts.append("## 概述\n\n")
        report_parts.append(self._generate_summary_text())
        report_parts.append("\n\n")
        
        # 实体分析
        report_parts.append("## 实体分析\n\n")
        entities = self._get_entities_with_info()
        entities_by_type = defaultdict(list)
        for entity in entities:
            entity_type = entity.get('type', 'Entity')
            entities_by_type[entity_type].append(entity)
        
        for entity_type, entity_list in entities_by_type.items():
            type_name_zh = self.entity_type_translations.get(entity_type, entity_type)
            report_parts.append(f"### {type_name_zh}\n\n")
            
            for entity in entity_list[:10]:  # 最多列举10个
                report_parts.append(f"- {entity['label']}")
                if entity.get('properties'):
                    for prop, value in list(entity['properties'].items())[:3]:  # 最多显示3个属性
                        report_parts.append(f" ({prop}: {value})")
                report_parts.append("\n")
            
            if len(entity_list) > 10:
                report_parts.append(f"... 还有{len(entity_list) - 10}个{type_name_zh}\n")
            
            report_parts.append("\n")
        
        # 关系分析
        report_parts.append("## 关系分析\n\n")
        relation_stats = self._get_relation_type_statistics()
        
        for relation_type, count in relation_stats[:10]:
            relation_name_zh = self.predicate_translations.get(relation_type, relation_type)
            report_parts.append(f"### {relation_name_zh} ({count}个关系)\n\n")
            
            # 获取该关系类型的示例
            examples = self._get_relation_examples(relation_type, limit=5)
            for example in examples:
                report_parts.append(f"- {example['subject']} → {example['object']}\n")
            
            report_parts.append("\n")
        
        return ''.join(report_parts)
    
    def _generate_qa_text(self) -> str:
        """生成问答格式文本"""
        qa_pairs = []
        
        # 基本信息问答
        stats = self.get_statistics()
        qa_pairs.append({
            'question': '这个知识图谱包含多少信息？',
            'answer': f'该知识图谱包含{stats["total_triples"]}个知识三元组，{stats["individuals"]}个实体，{stats["classes"]}种类型，{stats["properties"]}种关系。'
        })
        
        # 实体类型问答
        type_stats = self._get_entity_type_statistics()
        if type_stats:
            main_types = [self.entity_type_translations.get(t[0], t[0]) for t in type_stats[:3]]
            qa_pairs.append({
                'question': '主要包含哪些类型的实体？',
                'answer': f'主要实体类型包括{"、".join(main_types)}等。'
            })
        
        # 关系类型问答
        relation_stats = self._get_relation_type_statistics()
        if relation_stats:
            main_relations = [self.predicate_translations.get(r[0], r[0]) for r in relation_stats[:3]]
            qa_pairs.append({
                'question': '实体之间主要有哪些关系？',
                'answer': f'主要关系类型包括{"、".join(main_relations)}等。'
            })
        
        # 具体实体问答
        entities = self._get_entities_with_info()
        if entities:
            entity = entities[0]
            qa_pairs.append({
                'question': f'{entity["label"]}是什么？',
                'answer': f'{entity["label"]}是一个{self.entity_type_translations.get(entity.get("type", "Entity"), "实体")}。'
            })
        
        # 格式化输出
        result = []
        for i, qa in enumerate(qa_pairs, 1):
            result.append(f"Q{i}: {qa['question']}\n")
            result.append(f"A{i}: {qa['answer']}\n\n")
        
        return ''.join(result)
    
    def _generate_structured_text(self) -> str:
        """生成结构化文本"""
        structured_data = self._extract_structured_data()
        
        result = []
        
        # 实体部分
        result.append("【实体信息】\n")
        for entity_type, entities in structured_data.get('entities_by_type', {}).items():
            type_name_zh = self.entity_type_translations.get(entity_type, entity_type)
            result.append(f"\n{type_name_zh}：\n")
            
            for entity in entities[:10]:  # 最多显示10个
                result.append(f"  - {entity['label']}")
                if entity.get('properties'):
                    props = [f"{k}={v}" for k, v in list(entity['properties'].items())[:2]]
                    result.append(f" ({', '.join(props)})")
                result.append("\n")
        
        # 关系部分
        result.append("\n【关系信息】\n")
        for relation in structured_data.get('relations', [])[:20]:  # 最多显示20个关系
            predicate_zh = self.predicate_translations.get(relation['predicate'], relation['predicate'])
            result.append(f"  {relation['subject']} {predicate_zh} {relation['object']}\n")
        
        return ''.join(result)
    
    def _extract_structured_data(self) -> Dict[str, Any]:
        """提取结构化数据"""
        # 获取实体信息
        entities = self._get_entities_with_info()
        entities_by_type = defaultdict(list)
        for entity in entities:
            entity_type = entity.get('type', 'Entity')
            entities_by_type[entity_type].append(entity)
        
        # 获取关系信息
        relations = self._get_all_relations()
        
        return {
            'entities_by_type': dict(entities_by_type),
            'relations': relations,
            'statistics': self.get_statistics()
        }
    
    def _get_entities_with_info(self) -> List[Dict[str, Any]]:
        """获取带有详细信息的实体列表"""
        query = """
        SELECT ?entity ?type ?label
        WHERE {
            ?entity a ?type .
            ?type a owl:Class .
            OPTIONAL { ?entity rdfs:label ?label }
        }
        ORDER BY ?type ?entity
        """
        
        results = self.query_sparql(query)
        entities = []
        
        for result in results:
            entity_uri = str(result['entity'])
            entity_type = str(result['type']).split('/')[-1]
            entity_label = str(result.get('label', entity_uri.split('/')[-1]))
            
            # 获取实体的属性
            properties = self._get_entity_properties(result['entity'])
            
            entities.append({
                'uri': entity_uri,
                'type': entity_type,
                'label': entity_label,
                'properties': properties
            })
        
        return entities
    
    def _get_entity_properties(self, entity_uri: URIRef) -> Dict[str, str]:
        """获取实体的属性"""
        query = f"""
        SELECT ?property ?value
        WHERE {{
            <{entity_uri}> ?property ?value .
            FILTER(?property != rdf:type && ?property != rdfs:label)
        }}
        """
        
        results = self.query_sparql(query)
        properties = {}
        
        for result in results:
            prop_name = str(result['property']).split('/')[-1]
            prop_value = str(result['value'])
            properties[prop_name] = prop_value
        
        return properties
    
    def _get_important_relations(self) -> List[Dict[str, str]]:
        """获取重要关系"""
        query = """
        SELECT ?subject ?predicate ?object ?subjectLabel ?objectLabel
        WHERE {
            ?subject ?predicate ?object .
            FILTER(isURI(?object))
            FILTER(?predicate != rdf:type && ?predicate != rdfs:label && ?predicate != rdfs:comment)
            OPTIONAL { ?subject rdfs:label ?subjectLabel }
            OPTIONAL { ?object rdfs:label ?objectLabel }
        }
        LIMIT 50
        """
        
        results = self.query_sparql(query)
        relations = []
        
        for result in results:
            subject_label = str(result.get('subjectLabel', result['subject'])).split('/')[-1]
            predicate = str(result['predicate']).split('/')[-1]
            object_label = str(result.get('objectLabel', result['object'])).split('/')[-1]
            
            relations.append({
                'subject_label': subject_label,
                'predicate': predicate,
                'object_label': object_label
            })
        
        return relations
    
    def _get_all_relations(self) -> List[Dict[str, str]]:
        """获取所有关系"""
        query = """
        SELECT ?subject ?predicate ?object ?subjectLabel ?objectLabel
        WHERE {
            ?subject ?predicate ?object .
            FILTER(?predicate != rdf:type && ?predicate != rdfs:label && ?predicate != rdfs:comment)
            OPTIONAL { ?subject rdfs:label ?subjectLabel }
            OPTIONAL { ?object rdfs:label ?objectLabel }
        }
        """
        
        results = self.query_sparql(query)
        relations = []
        
        for result in results:
            subject_label = str(result.get('subjectLabel', result['subject'])).split('/')[-1]
            predicate = str(result['predicate']).split('/')[-1]
            
            if 'objectLabel' in result:
                object_label = str(result['objectLabel'])
            else:
                obj = result['object']
                if hasattr(obj, 'value'):
                    object_label = str(obj.value)
                else:
                    object_label = str(obj).split('/')[-1]
            
            relations.append({
                'subject': subject_label,
                'predicate': predicate,
                'object': object_label
            })
        
        return relations
    
    def _get_entity_type_statistics(self) -> List[Tuple[str, int]]:
        """获取实体类型统计"""
        query = """
        SELECT ?type (COUNT(?entity) as ?count)
        WHERE {
            ?entity a ?type .
            ?type a owl:Class .
        }
        GROUP BY ?type
        ORDER BY DESC(?count)
        """
        
        results = self.query_sparql(query)
        return [(str(r['type']).split('/')[-1], int(r['count'])) for r in results]
    
    def _get_relation_type_statistics(self) -> List[Tuple[str, int]]:
        """获取关系类型统计"""
        query = """
        SELECT ?predicate (COUNT(*) as ?count)
        WHERE {
            ?subject ?predicate ?object .
            FILTER(?predicate != rdf:type && ?predicate != rdfs:label && ?predicate != rdfs:comment)
        }
        GROUP BY ?predicate
        ORDER BY DESC(?count)
        """
        
        results = self.query_sparql(query)
        return [(str(r['predicate']).split('/')[-1], int(r['count'])) for r in results]
    
    def _get_relation_examples(self, relation_type: str, limit: int = 5) -> List[Dict[str, str]]:
        """获取特定关系类型的示例"""
        # 构建完整的关系URI
        relation_uri = self.create_uri(relation_type)
        
        query = f"""
        SELECT ?subject ?object ?subjectLabel ?objectLabel
        WHERE {{
            ?subject <{relation_uri}> ?object .
            OPTIONAL {{ ?subject rdfs:label ?subjectLabel }}
            OPTIONAL {{ ?object rdfs:label ?objectLabel }}
        }}
        LIMIT {limit}
        """
        
        results = self.query_sparql(query)
        examples = []
        
        for result in results:
            subject_label = str(result.get('subjectLabel', result['subject'])).split('/')[-1]
            object_label = str(result.get('objectLabel', result['object'])).split('/')[-1]
            
            examples.append({
                'subject': subject_label,
                'object': object_label
            })
        
        return examples
    
    def generate_entity_description(self, entity_uri: str) -> str:
        """生成特定实体的描述"""
        # 获取实体信息
        entity_info = self._get_entity_info(entity_uri)
        
        if not entity_info:
            return f"未找到实体 {entity_uri} 的信息。"
        
        description_parts = []
        
        # 基本信息
        entity_type_zh = self.entity_type_translations.get(entity_info['type'], entity_info['type'])
        description_parts.append(f"{entity_info['label']}是一个{entity_type_zh}。")
        
        # 属性信息
        if entity_info['properties']:
            description_parts.append("其属性包括：")
            for prop, value in entity_info['properties'].items():
                description_parts.append(f"{prop}为{value}；")
        
        # 关系信息
        relations = self._get_entity_relations(entity_uri)
        if relations:
            description_parts.append("相关关系有：")
            for relation in relations[:5]:  # 最多显示5个关系
                predicate_zh = self.predicate_translations.get(relation['predicate'], relation['predicate'])
                description_parts.append(f"{predicate_zh}{relation['object']}；")
        
        return ''.join(description_parts)
    
    def _get_entity_info(self, entity_uri: str) -> Optional[Dict[str, Any]]:
        """获取实体信息"""
        query = f"""
        SELECT ?type ?label
        WHERE {{
            <{entity_uri}> a ?type .
            ?type a owl:Class .
            OPTIONAL {{ <{entity_uri}> rdfs:label ?label }}
        }}
        """
        
        results = self.query_sparql(query)
        if not results:
            return None
        
        result = results[0]
        entity_type = str(result['type']).split('/')[-1]
        entity_label = str(result.get('label', entity_uri.split('/')[-1]))
        
        # 获取属性
        properties = self._get_entity_properties(URIRef(entity_uri))
        
        return {
            'type': entity_type,
            'label': entity_label,
            'properties': properties
        }
    
    def _get_entity_relations(self, entity_uri: str) -> List[Dict[str, str]]:
        """获取实体的关系"""
        query = f"""
        SELECT ?predicate ?object ?objectLabel
        WHERE {{
            <{entity_uri}> ?predicate ?object .
            FILTER(?predicate != rdf:type && ?predicate != rdfs:label && ?predicate != rdfs:comment)
            OPTIONAL {{ ?object rdfs:label ?objectLabel }}
        }}
        """
        
        results = self.query_sparql(query)
        relations = []
        
        for result in results:
            predicate = str(result['predicate']).split('/')[-1]
            object_label = str(result.get('objectLabel', result['object'])).split('/')[-1]
            
            relations.append({
                'predicate': predicate,
                'object': object_label
            })
        
        return relations