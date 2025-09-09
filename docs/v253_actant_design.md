# Greeum v2.5.3: Actant-Based Memory Recording Design

## 🎯 Core Vision

Transform Greeum MCP tools to **force** actant-based recording through tool descriptions, enabling relationship and causality inference foundation for v3.0.0 schema management.

## 📋 Actant-Based Tool Description Strategy

### Current MCP Tool Pattern (v2.5.2)
```python
{
    "name": "add_memory", 
    "description": "Add important permanent memories to long-term storage.",
    "parameters": {
        "content": {"description": "Content to store in memory"},
        "importance": {"description": "Importance score (0.0-1.0)"}
    }
}
```

### v2.5.3 Actant-Enforced Pattern
```python
{
    "name": "add_memory",
    "description": "Record [SUBJECT-ACTION-OBJECT] structured memory. MANDATORY format: '[주체-행동-객체] 구체적 내용'. Examples: '[사용자-요청-기능개선]', '[Claude-발견-버그]', '[팀-결정-아키텍처]'",
    "parameters": {
        "content": {
            "description": "MUST start with '[Subject-Action-Object]' pattern. Subject: who performed action (사용자/Claude/팀/시스템). Action: specific verb (요청/발견/결정/구현/테스트). Object: target of action. Required format: '[주체-행동-객체] detailed description 1-2 sentences'",
            "pattern": "^\\[\\w+-\\w+-\\w+\\].*"
        },
        "importance": {"description": "Importance score (0.0-1.0)"}
    }
}
```

## 🔧 Implementation Strategy

### Phase 1: Tool Description Enhancement
Update all MCP tool descriptions to **require** actant format:

1. **add_memory**: Force `[Subject-Action-Object]` format
2. **search_memory**: Include relationship context in descriptions  
3. **get_memory_stats**: Return actant pattern analytics
4. **usage_analytics**: Track actant compliance and relationship patterns

### Phase 2: Validation Layer
```python
def validate_actant_format(content: str) -> ActantValidation:
    """Validate and extract actant components"""
    pattern = r'^\[(\w+)-(\w+)-(\w+)\]\s*(.+)$'
    match = re.match(pattern, content)
    
    if not match:
        raise ValueError("Content must start with [Subject-Action-Object] format")
    
    subject, action, object_target, description = match.groups()
    
    return ActantValidation(
        subject=subject,
        action=action, 
        object_target=object_target,
        description=description,
        is_valid=True
    )
```

### Phase 3: Relationship Inference Foundation
```python
class RelationshipExtractor:
    """Extract relationships and causality from actant-structured memories"""
    
    def extract_relationships(self, memories: List[ActantMemory]) -> RelationshipGraph:
        """Build relationship graph from actant patterns"""
        graph = RelationshipGraph()
        
        for memory in memories:
            # Subject-Subject relationships (who works with whom)
            subject_relations = self._find_subject_relationships(memory, memories)
            
            # Action-Action causality (what actions lead to other actions)  
            action_causality = self._find_action_causality(memory, memories)
            
            # Object-Object dependencies (what objects are related)
            object_dependencies = self._find_object_dependencies(memory, memories)
            
            graph.add_relationships(subject_relations, action_causality, object_dependencies)
            
        return graph
```

## 📊 Expected Benefits for v3.0.0

### 1. Rich Relationship Data
- **Subject networks**: Who collaborates with whom
- **Action chains**: What actions trigger other actions
- **Object dependencies**: Which components/features are related

### 2. Causality Inference
- **Temporal patterns**: Action sequences over time
- **Trigger analysis**: What events cause what outcomes
- **Impact mapping**: How decisions affect implementation

### 3. Schema Foundation
- **Structured data**: Clean actant-based records for schema migration
- **Relationship schema**: Pre-built relationship types for v3.0.0
- **Validation rules**: Established patterns for schema enforcement

## 🎯 v2.5.3 Deliverables

1. **Enhanced MCP Tools** with actant-enforcing descriptions
2. **Actant Validation Layer** with regex pattern matching
3. **Relationship Extraction Engine** for basic inference
4. **Analytics Dashboard** showing actant compliance and relationship patterns
5. **Migration Path** documentation for v3.0.0 schema transition

## 📈 Success Metrics

- **Actant Compliance**: 90%+ of new memories follow [Subject-Action-Object] format
- **Relationship Discovery**: Identify 50+ subject-action-object relationships
- **Causality Patterns**: Document 20+ action-action causal chains
- **Schema Readiness**: 100% of data ready for v3.0.0 schema migration

This foundation will enable v3.0.0 to implement full schema-based management with rich relationship inference capabilities.