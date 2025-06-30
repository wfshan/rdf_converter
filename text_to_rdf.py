#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自然语言转RDF转换器

使用大模型将自然语言文本转换为RDF知识图谱
"""

import json
import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

import jieba
import jieba.posseg as pseg
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

@dataclass
class ExtractedTriple:
    """提取的三元组"""
    subject: str
    predicate: str
    object: str
    confidence: float = 0.0
    subject_type: str = "Entity"
    object_type: str = "Entity"
    relation_type: str = "Relation"

class TextToRDFConverter(BaseRDFConverter):
    """自然语言转RDF转换器"""
    
    def __init__(self, base_uri: str = "http://example.org/kg/", use_llm: bool = True):
        super().__init__(base_uri)
        self.use_llm = use_llm and LLM_AVAILABLE
        self.llm = None
        
        if self.use_llm:
            try:
                self.llm = VolcengineLLM()
                logger.info("成功初始化火山方舟大模型")
            except Exception as e:
                logger.warning(f"初始化大模型失败，将使用规则方法: {e}")
                self.use_llm = False
        
        # 初始化中文分词
        jieba.initialize()
        
        # 预定义的实体类型和关系类型
        self.entity_types = {
            '人物': 'Person',
            '公司': 'Company', 
            '组织': 'Organization',
            '地点': 'Location',
            '时间': 'Time',
            '金额': 'Amount',
            '账户': 'Account',
            '交易': 'Transaction',
            '产品': 'Product',
            '事件': 'Event'
        }
        
        self.relation_types = {
            '拥有': 'owns',
            '工作于': 'worksAt',
            '位于': 'locatedAt',
            '发生于': 'occurredAt',
            '参与': 'participatesIn',
            '转账': 'transfersTo',
            '关联': 'relatedTo',
            '控制': 'controls',
            '投资': 'invests',
            '合作': 'cooperatesWith'
        }
    
    def convert_to_rdf(self, text: str, extraction_method: str = "llm") -> bool:
        """转换自然语言文本到RDF
        
        Args:
            text: 输入文本
            extraction_method: 提取方法 ('llm', 'rule', 'hybrid')
        """
        try:
            logger.info(f"开始转换文本到RDF，方法: {extraction_method}")
            
            if extraction_method == "llm" and self.use_llm:
                triples = self._extract_triples_with_llm(text)
            elif extraction_method == "rule":
                triples = self._extract_triples_with_rules(text)
            elif extraction_method == "hybrid":
                # 混合方法：先用规则提取，再用LLM补充
                rule_triples = self._extract_triples_with_rules(text)
                if self.use_llm:
                    llm_triples = self._extract_triples_with_llm(text)
                    triples = self._merge_triples(rule_triples, llm_triples)
                else:
                    triples = rule_triples
            else:
                triples = self._extract_triples_with_rules(text)
            
            # 将提取的三元组添加到RDF图
            for triple in triples:
                self._add_triple_to_rdf(triple)
            
            logger.info(f"文本转换完成，提取了 {len(triples)} 个三元组，生成 {len(self.graph)} 个RDF三元组")
            return True
            
        except Exception as e:
            logger.error(f"转换文本到RDF失败: {e}")
            return False
    
    def _extract_triples_with_llm(self, text: str) -> List[ExtractedTriple]:
        """使用大模型提取三元组"""
        if not self.llm:
            return []
        
        prompt = f"""
请从以下文本中提取知识三元组，以JSON格式返回。每个三元组包含主语(subject)、谓语(predicate)、宾语(object)，以及它们的类型。

文本：{text}

请返回JSON格式，例如：
{{
  "triples": [
    {{
      "subject": "张三",
      "predicate": "工作于",
      "object": "ABC公司",
      "subject_type": "Person",
      "object_type": "Company",
      "relation_type": "Employment",
      "confidence": 0.9
    }}
  ]
}}

注意：
1. 主语和宾语应该是具体的实体
2. 谓语应该表达它们之间的关系
3. 类型使用英文，如Person、Company、Location等
4. confidence表示置信度(0-1)
"""
        
        try:
            response = self.llm.chat_completion([
                {"role": "user", "content": prompt}
            ], temperature=0.3)
            
            if response.success:
                # 尝试解析JSON响应
                content = response.content
                
                # 提取JSON部分
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    result = json.loads(json_str)
                    
                    triples = []
                    for triple_data in result.get('triples', []):
                        triple = ExtractedTriple(
                            subject=triple_data['subject'],
                            predicate=triple_data['predicate'],
                            object=triple_data['object'],
                            subject_type=triple_data.get('subject_type', 'Entity'),
                            object_type=triple_data.get('object_type', 'Entity'),
                            relation_type=triple_data.get('relation_type', 'Relation'),
                            confidence=triple_data.get('confidence', 0.8)
                        )
                        triples.append(triple)
                    
                    return triples
            
        except Exception as e:
            logger.error(f"LLM提取三元组失败: {e}")
        
        return []
    
    def _extract_triples_with_rules(self, text: str) -> List[ExtractedTriple]:
        """使用规则方法提取三元组"""
        triples = []
        
        # 分句处理
        sentences = re.split(r'[。！？；]', text)
        
        for sentence in sentences:
            if not sentence.strip():
                continue
            
            # 词性标注
            words = list(pseg.cut(sentence))
            
            # 提取实体
            entities = self._extract_entities(words)
            
            # 提取关系
            relations = self._extract_relations(words)
            
            # 构建三元组
            sentence_triples = self._build_triples_from_entities_relations(entities, relations, sentence)
            triples.extend(sentence_triples)
        
        return triples
    
    def _extract_entities(self, words: List[Tuple[str, str]]) -> List[Dict[str, Any]]:
        """从词性标注结果中提取实体"""
        entities = []
        
        for word, pos in words:
            entity_type = None
            
            # 人名
            if pos in ['nr', 'nrf']:
                entity_type = 'Person'
            # 地名
            elif pos in ['ns', 'nsf']:
                entity_type = 'Location'
            # 机构名
            elif pos in ['nt', 'nz']:
                entity_type = 'Organization'
            # 时间
            elif pos in ['t']:
                entity_type = 'Time'
            # 数量
            elif pos in ['m', 'mq']:
                entity_type = 'Amount'
            # 普通名词（可能是实体）
            elif pos in ['n', 'ng', 'nl'] and len(word) > 1:
                entity_type = 'Entity'
            
            if entity_type:
                entities.append({
                    'text': word,
                    'type': entity_type,
                    'pos': pos
                })
        
        return entities
    
    def _extract_relations(self, words: List[Tuple[str, str]]) -> List[Dict[str, Any]]:
        """从词性标注结果中提取关系"""
        relations = []
        
        for word, pos in words:
            relation_type = None
            
            # 动词
            if pos.startswith('v'):
                relation_type = 'Action'
            # 介词
            elif pos in ['p']:
                relation_type = 'Preposition'
            # 连词
            elif pos in ['c']:
                relation_type = 'Conjunction'
            
            # 检查预定义关系
            if word in self.relation_types:
                relation_type = 'PredefinedRelation'
            
            if relation_type:
                relations.append({
                    'text': word,
                    'type': relation_type,
                    'pos': pos
                })
        
        return relations
    
    def _build_triples_from_entities_relations(self, entities: List[Dict], 
                                             relations: List[Dict], 
                                             sentence: str) -> List[ExtractedTriple]:
        """从实体和关系构建三元组"""
        triples = []
        
        if len(entities) >= 2 and len(relations) >= 1:
            # 简单的启发式规则：第一个实体作为主语，最后一个实体作为宾语，中间的关系作为谓语
            for i in range(len(entities) - 1):
                for j in range(i + 1, len(entities)):
                    subject_entity = entities[i]
                    object_entity = entities[j]
                    
                    # 寻找最合适的关系
                    best_relation = None
                    if relations:
                        # 选择位置在两个实体之间的关系
                        subject_pos = sentence.find(subject_entity['text'])
                        object_pos = sentence.find(object_entity['text'])
                        
                        for relation in relations:
                            relation_pos = sentence.find(relation['text'])
                            if subject_pos < relation_pos < object_pos:
                                best_relation = relation
                                break
                        
                        if not best_relation:
                            best_relation = relations[0]  # 使用第一个关系
                    
                    if best_relation:
                        predicate = best_relation['text']
                        if predicate in self.relation_types:
                            predicate = self.relation_types[predicate]
                        
                        triple = ExtractedTriple(
                            subject=subject_entity['text'],
                            predicate=predicate,
                            object=object_entity['text'],
                            subject_type=subject_entity['type'],
                            object_type=object_entity['type'],
                            relation_type=best_relation['type'],
                            confidence=0.6
                        )
                        triples.append(triple)
        
        return triples
    
    def _merge_triples(self, rule_triples: List[ExtractedTriple], 
                      llm_triples: List[ExtractedTriple]) -> List[ExtractedTriple]:
        """合并规则提取和LLM提取的三元组"""
        merged = []
        
        # 添加LLM提取的三元组（置信度较高）
        for triple in llm_triples:
            merged.append(triple)
        
        # 添加规则提取的三元组，但避免重复
        for rule_triple in rule_triples:
            is_duplicate = False
            for existing_triple in merged:
                if (rule_triple.subject == existing_triple.subject and
                    rule_triple.predicate == existing_triple.predicate and
                    rule_triple.object == existing_triple.object):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                merged.append(rule_triple)
        
        return merged
    
    def _add_triple_to_rdf(self, triple: ExtractedTriple):
        """将提取的三元组添加到RDF图"""
        # 创建主语URI
        subject_uri = self.create_uri(self._sanitize_name(triple.subject))
        
        # 创建谓语URI
        predicate_uri = self.create_uri(self._sanitize_name(triple.predicate))
        
        # 创建宾语URI或字面量
        if self._is_literal(triple.object):
            object_node = Literal(triple.object)
        else:
            object_node = self.create_uri(self._sanitize_name(triple.object))
        
        # 添加三元组
        self.add_triple(subject_uri, predicate_uri, object_node)
        
        # 添加类型信息
        subject_class_uri = self.create_uri(triple.subject_type)
        self.add_triple(subject_uri, RDF.type, subject_class_uri)
        self.add_class(subject_class_uri, triple.subject_type)
        
        if not self._is_literal(triple.object):
            object_class_uri = self.create_uri(triple.object_type)
            self.add_triple(object_node, RDF.type, object_class_uri)
            self.add_class(object_class_uri, triple.object_type)
        
        # 添加标签
        self.add_triple(subject_uri, RDFS.label, Literal(triple.subject, lang='zh'))
        if not self._is_literal(triple.object):
            self.add_triple(object_node, RDFS.label, Literal(triple.object, lang='zh'))
        
        # 添加置信度信息
        if triple.confidence > 0:
            confidence_prop = self.create_uri('confidence')
            # 为三元组创建一个陈述节点
            statement_uri = self.create_uri(f"statement_{len(self.graph)}")
            self.add_triple(statement_uri, RDF.type, self.create_uri('Statement'))
            self.add_triple(statement_uri, self.create_uri('hasSubject'), subject_uri)
            self.add_triple(statement_uri, self.create_uri('hasPredicate'), predicate_uri)
            self.add_triple(statement_uri, self.create_uri('hasObject'), object_node)
            self.add_triple(statement_uri, confidence_prop, Literal(triple.confidence))
    
    def _is_literal(self, value: str) -> bool:
        """判断值是否应该作为字面量"""
        # 数字
        if value.replace('.', '').replace('-', '').isdigit():
            return True
        
        # 日期格式
        if re.match(r'\d{4}[-/]\d{1,2}[-/]\d{1,2}', value):
            return True
        
        # 时间格式
        if re.match(r'\d{1,2}:\d{2}', value):
            return True
        
        # 短文本（可能是属性值）
        if len(value) < 10 and not any(char in value for char in '公司组织机构'):
            return True
        
        return False
    
    def _sanitize_name(self, name: str) -> str:
        """清理名称，使其适合作为URI的一部分"""
        import re
        from urllib.parse import quote
        
        # 移除或替换特殊字符
        sanitized = re.sub(r'[^\w\u4e00-\u9fff]', '_', str(name))
        sanitized = re.sub(r'_+', '_', sanitized)
        sanitized = sanitized.strip('_')
        return quote(sanitized, safe='')
    
    def convert_from_rdf(self, target_format: str = "text") -> Any:
        """从RDF转换为自然语言"""
        if target_format == "text":
            return self._convert_rdf_to_text()
        elif target_format == "summary":
            return self._convert_rdf_to_summary()
        elif target_format == "triples":
            return self._convert_rdf_to_triple_list()
        else:
            logger.error(f"不支持的目标格式: {target_format}")
            return None
    
    def _convert_rdf_to_text(self) -> str:
        """转换RDF为自然语言文本"""
        sentences = []
        
        # 查询所有三元组
        query = """
        SELECT ?subject ?predicate ?object ?subjectLabel ?objectLabel
        WHERE {
            ?subject ?predicate ?object .
            OPTIONAL { ?subject rdfs:label ?subjectLabel }
            OPTIONAL { ?object rdfs:label ?objectLabel }
            FILTER(?predicate != rdf:type && ?predicate != rdfs:label && ?predicate != rdfs:comment)
        }
        """
        
        results = self.query_sparql(query)
        
        for result in results:
            subject_label = result.get('subjectLabel', str(result['subject']).split('/')[-1])
            predicate_label = str(result['predicate']).split('/')[-1]
            
            if 'objectLabel' in result:
                object_label = result['objectLabel']
            else:
                obj = result['object']
                if hasattr(obj, 'value'):
                    object_label = str(obj.value)
                else:
                    object_label = str(obj).split('/')[-1]
            
            # 将英文谓语转换为中文
            predicate_zh = self._translate_predicate_to_chinese(predicate_label)
            
            sentence = f"{subject_label}{predicate_zh}{object_label}"
            sentences.append(sentence)
        
        return '。'.join(sentences) + '。'
    
    def _convert_rdf_to_summary(self) -> str:
        """转换RDF为摘要文本"""
        stats = self.get_statistics()
        
        summary = f"知识图谱包含{stats['individuals']}个实体，{stats['classes']}种类型，{stats['total_triples']}个关系。"
        
        # 获取主要实体类型
        type_query = """
        SELECT ?type (COUNT(?entity) as ?count)
        WHERE {
            ?entity a ?type .
            ?type a owl:Class .
        }
        GROUP BY ?type
        ORDER BY DESC(?count)
        LIMIT 5
        """
        
        type_results = self.query_sparql(type_query)
        if type_results:
            summary += "主要实体类型包括："
            for result in type_results:
                type_name = str(result['type']).split('/')[-1]
                count = int(result['count'])
                summary += f"{type_name}({count}个)、"
            summary = summary.rstrip('、') + "。"
        
        return summary
    
    def _convert_rdf_to_triple_list(self) -> List[Dict[str, str]]:
        """转换RDF为三元组列表"""
        triples = []
        
        query = """
        SELECT ?subject ?predicate ?object ?subjectLabel ?objectLabel
        WHERE {
            ?subject ?predicate ?object .
            OPTIONAL { ?subject rdfs:label ?subjectLabel }
            OPTIONAL { ?object rdfs:label ?objectLabel }
            FILTER(?predicate != rdf:type && ?predicate != rdfs:label && ?predicate != rdfs:comment)
        }
        """
        
        results = self.query_sparql(query)
        
        for result in results:
            subject_label = result.get('subjectLabel', str(result['subject']).split('/')[-1])
            predicate_label = str(result['predicate']).split('/')[-1]
            
            if 'objectLabel' in result:
                object_label = result['objectLabel']
            else:
                obj = result['object']
                if hasattr(obj, 'value'):
                    object_label = str(obj.value)
                else:
                    object_label = str(obj).split('/')[-1]
            
            triple = {
                'subject': subject_label,
                'predicate': predicate_label,
                'object': object_label
            }
            triples.append(triple)
        
        return triples
    
    def _translate_predicate_to_chinese(self, predicate: str) -> str:
        """将英文谓语转换为中文"""
        translation_map = {
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
            'confidence': '置信度'
        }
        
        return translation_map.get(predicate, predicate)
    
    def extract_entities_and_relations(self, text: str) -> Dict[str, List[str]]:
        """提取文本中的实体和关系（用于分析）"""
        words = list(pseg.cut(text))
        entities = self._extract_entities(words)
        relations = self._extract_relations(words)
        
        return {
            'entities': [e['text'] for e in entities],
            'relations': [r['text'] for r in relations]
        }