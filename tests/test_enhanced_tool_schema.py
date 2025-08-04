#!/usr/bin/env python3
"""
Comprehensive Unit Tests for EnhancedToolSchema (Greeum v2.1.0)
Tests schema generation for all 10 MCP tools, parameter validation,
usage hints, best practices content, and integration scenarios.
"""

import json
from typing import Dict, Any

from tests.base_test_case import BaseGreeumTestCase
from greeum.mcp.enhanced_tool_schema import EnhancedToolSchema


class TestEnhancedToolSchema(BaseGreeumTestCase):
    """Comprehensive test suite for EnhancedToolSchema class"""
    
    def setUp(self):
        """Set up test fixtures before each test method"""
        super().setUp()
        
        self.schema = EnhancedToolSchema()
        
        # Expected tool names
        self.expected_tools = [
            "add_memory", "search_memory", "get_memory_stats", "usage_analytics",
            "ltm_analyze", "ltm_verify", "ltm_export", "stm_add", "stm_promote", "stm_cleanup"
        ]
        
        # Common schema structure elements
        self.required_schema_fields = ["name", "description", "inputSchema"]
        self.required_input_schema_fields = ["type", "properties"]
    
    def test_schema_class_methods(self):
        """Test that all expected schema methods exist"""
        expected_methods = [
            "get_add_memory_schema", "get_search_memory_schema", "get_get_memory_stats_schema",
            "get_usage_analytics_schema", "get_ltm_analyze_schema", "get_ltm_verify_schema",
            "get_ltm_export_schema", "get_stm_add_schema", "get_stm_promote_schema", 
            "get_stm_cleanup_schema", "get_all_enhanced_schemas", "get_tool_schema_by_name"
        ]
        
        for method_name in expected_methods:
            self.assertTrue(hasattr(EnhancedToolSchema, method_name),
                          f"Missing method: {method_name}")
            self.assertTrue(callable(getattr(EnhancedToolSchema, method_name)),
                          f"Method {method_name} is not callable")
    
    def test_add_memory_schema(self):
        """Test add_memory tool schema generation"""
        schema = EnhancedToolSchema.get_add_memory_schema()
        
        # Test basic structure
        self.assertEqual(schema["name"], "add_memory")
        self.assertIn("🧠 Add important permanent memories", schema["description"])
        self.assertIn("USAGE GUIDELINES", schema["description"])
        self.assertIn("ALWAYS search_memory first", schema["description"])
        
        # Test input schema
        input_schema = schema["inputSchema"]
        self.assertEqual(input_schema["type"], "object")
        
        properties = input_schema["properties"]
        self.assertIn("content", properties)
        self.assertIn("importance", properties)
        
        # Test content property
        content_prop = properties["content"]
        self.assertEqual(content_prop["type"], "string")
        self.assertEqual(content_prop["minLength"], 10)
        self.assertIn("meaningful", content_prop["description"])
        
        # Test importance property
        importance_prop = properties["importance"]
        self.assertEqual(importance_prop["type"], "number")
        self.assertEqual(importance_prop["default"], 0.5)
        self.assertEqual(importance_prop["minimum"], 0.0)
        self.assertEqual(importance_prop["maximum"], 1.0)
        self.assertIn("Critical", importance_prop["description"])
        
        # Test required fields
        self.assertEqual(input_schema["required"], ["content"])
        
        # Test usage hints
        self.assertIn("usage_hints", schema)
        usage_hints = schema["usage_hints"]
        self.assertIn("when_to_use", usage_hints)
        self.assertIn("when_not_to_use", usage_hints) 
        self.assertIn("best_practices", usage_hints)
        
        # Verify usage hints content
        self.assertIsInstance(usage_hints["when_to_use"], list)
        self.assertGreater(len(usage_hints["when_to_use"]), 0)
        self.assertTrue(any("preferences" in hint for hint in usage_hints["when_to_use"]))
    
    def test_search_memory_schema(self):
        """Test search_memory tool schema generation"""
        schema = EnhancedToolSchema.get_search_memory_schema()
        
        # Test basic structure
        self.assertEqual(schema["name"], "search_memory")
        self.assertIn("🔍 Search existing memories", schema["description"])
        self.assertIn("ALWAYS USE THIS FIRST", schema["description"])
        
        # Test input schema
        properties = schema["inputSchema"]["properties"]
        self.assertIn("query", properties)
        self.assertIn("limit", properties)
        
        # Test query property
        query_prop = properties["query"]
        self.assertEqual(query_prop["type"], "string")
        self.assertEqual(query_prop["minLength"], 2)
        
        # Test limit property
        limit_prop = properties["limit"]
        self.assertEqual(limit_prop["type"], "integer")
        self.assertEqual(limit_prop["default"], 5)
        self.assertEqual(limit_prop["minimum"], 1)
        self.assertEqual(limit_prop["maximum"], 50)
        
        # Test usage hints
        usage_hints = schema["usage_hints"]
        self.assertIn("search_strategies", usage_hints)
        self.assertIn("result_handling", usage_hints)
        
        self.assertIsInstance(usage_hints["search_strategies"], list)
        self.assertTrue(any("specific keywords" in hint for hint in usage_hints["search_strategies"]))
    
    def test_stm_add_schema(self):
        """Test stm_add tool schema generation"""
        schema = EnhancedToolSchema.get_stm_add_schema()
        
        # Test basic structure
        self.assertEqual(schema["name"], "stm_add")
        self.assertIn("🕒 Add content to short-term memory", schema["description"])
        self.assertIn("STM vs LTM Decision", schema["description"])
        
        # Test input schema properties
        properties = schema["inputSchema"]["properties"]
        self.assertIn("content", properties)
        self.assertIn("ttl", properties)
        self.assertIn("importance", properties)
        
        # Test TTL property
        ttl_prop = properties["ttl"]
        self.assertEqual(ttl_prop["type"], "string")
        self.assertEqual(ttl_prop["default"], "1h")
        self.assertIn("30m, 1h, 2h, 1d", ttl_prop["description"])
        
        # Test importance property for STM
        importance_prop = properties["importance"]
        self.assertEqual(importance_prop["default"], 0.3)  # Lower default for STM
        self.assertIn("typically 0.3-0.5", importance_prop["description"])
    
    def test_ltm_analyze_schema(self):
        """Test ltm_analyze tool schema generation"""
        schema = EnhancedToolSchema.get_ltm_analyze_schema()
        
        # Test basic structure
        self.assertEqual(schema["name"], "ltm_analyze")
        self.assertIn("📊 Analyze long-term memory patterns", schema["description"])
        
        # Test input schema properties
        properties = schema["inputSchema"]["properties"]
        self.assertIn("trends", properties)
        self.assertIn("period", properties)
        self.assertIn("output", properties)
        
        # Test trends property
        trends_prop = properties["trends"]
        self.assertEqual(trends_prop["type"], "boolean")
        self.assertEqual(trends_prop["default"], True)
        
        # Test period property
        period_prop = properties["period"]
        self.assertEqual(period_prop["type"], "string")
        self.assertEqual(period_prop["default"], "6m")
        self.assertIn("1w, 1m, 3m, 6m, 1y", period_prop["description"])
        
        # Test output property
        output_prop = properties["output"]
        self.assertEqual(output_prop["type"], "string")
        self.assertEqual(output_prop["enum"], ["text", "json"])
        self.assertEqual(output_prop["default"], "text")
    
    def test_get_memory_stats_schema(self):
        """Test get_memory_stats tool schema generation"""
        schema = EnhancedToolSchema.get_get_memory_stats_schema()
        
        # Test basic structure
        self.assertEqual(schema["name"], "get_memory_stats")
        self.assertIn("📊 Get current memory system statistics", schema["description"])
        self.assertIn("Starting new conversations", schema["description"])
        
        # Test input schema (should be empty)
        properties = schema["inputSchema"]["properties"]
        self.assertEqual(len(properties), 0)
    
    def test_stm_promote_schema(self):
        """Test stm_promote tool schema generation"""
        schema = EnhancedToolSchema.get_stm_promote_schema()
        
        # Test basic structure
        self.assertEqual(schema["name"], "stm_promote")
        self.assertIn("🔝 Promote important short-term memories", schema["description"])
        self.assertIn("USE AT SESSION END", schema["description"])
        self.assertIn("dry_run=true first", schema["description"])
        
        # Test input schema properties
        properties = schema["inputSchema"]["properties"]
        self.assertIn("threshold", properties)
        self.assertIn("dry_run", properties)
        
        # Test threshold property
        threshold_prop = properties["threshold"]
        self.assertEqual(threshold_prop["type"], "number")
        self.assertEqual(threshold_prop["default"], 0.8)
        self.assertIn("0.8 recommended", threshold_prop["description"])
        
        # Test dry_run property
        dry_run_prop = properties["dry_run"]
        self.assertEqual(dry_run_prop["type"], "boolean")
        self.assertEqual(dry_run_prop["default"], False)
        self.assertIn("recommended first", dry_run_prop["description"])
    
    def test_stm_cleanup_schema(self):
        """Test stm_cleanup tool schema generation"""
        schema = EnhancedToolSchema.get_stm_cleanup_schema()
        
        # Test basic structure
        self.assertEqual(schema["name"], "stm_cleanup")
        self.assertIn("🧹 Clean up short-term memory entries", schema["description"])
        
        # Test input schema properties
        properties = schema["inputSchema"]["properties"]
        self.assertIn("smart", properties)
        self.assertIn("expired", properties)
        self.assertIn("threshold", properties)
        
        # Test smart property
        smart_prop = properties["smart"]
        self.assertEqual(smart_prop["type"], "boolean")
        self.assertEqual(smart_prop["default"], False)
        self.assertIn("intelligent cleanup", smart_prop["description"])
        
        # Test expired property
        expired_prop = properties["expired"]
        self.assertEqual(expired_prop["type"], "boolean")
        self.assertEqual(expired_prop["default"], False)
        self.assertIn("safest option", expired_prop["description"])
    
    def test_ltm_verify_schema(self):
        """Test ltm_verify tool schema generation"""
        schema = EnhancedToolSchema.get_ltm_verify_schema()
        
        # Test basic structure
        self.assertEqual(schema["name"], "ltm_verify")
        self.assertIn("🔍 Verify blockchain-like LTM integrity", schema["description"])
        self.assertIn("repair=true only if issues detected", schema["description"])
        
        # Test input schema properties
        properties = schema["inputSchema"]["properties"]
        self.assertIn("repair", properties)
        
        # Test repair property
        repair_prop = properties["repair"]
        self.assertEqual(repair_prop["type"], "boolean")
        self.assertEqual(repair_prop["default"], False)
        self.assertIn("use carefully", repair_prop["description"])
    
    def test_ltm_export_schema(self):
        """Test ltm_export tool schema generation"""
        schema = EnhancedToolSchema.get_ltm_export_schema()
        
        # Test basic structure
        self.assertEqual(schema["name"], "ltm_export")
        self.assertIn("📤 Export long-term memory data", schema["description"])
        
        # Test input schema properties
        properties = schema["inputSchema"]["properties"]
        self.assertIn("format", properties)
        self.assertIn("limit", properties)
        
        # Test format property
        format_prop = properties["format"]
        self.assertEqual(format_prop["type"], "string")
        self.assertEqual(format_prop["enum"], ["json", "blockchain", "csv"])
        self.assertEqual(format_prop["default"], "json")
        
        # Test limit property
        limit_prop = properties["limit"]
        self.assertEqual(limit_prop["type"], "integer")
        self.assertEqual(limit_prop["minimum"], 1)
        self.assertEqual(limit_prop["maximum"], 1000)
    
    def test_usage_analytics_schema(self):
        """Test usage_analytics tool schema generation"""
        schema = EnhancedToolSchema.get_usage_analytics_schema()
        
        # Test basic structure
        self.assertEqual(schema["name"], "usage_analytics")
        self.assertIn("📊 Get comprehensive usage analytics", schema["description"])
        
        # Test input schema properties
        properties = schema["inputSchema"]["properties"]
        self.assertIn("days", properties)
        self.assertIn("report_type", properties)
        
        # Test days property
        days_prop = properties["days"]
        self.assertEqual(days_prop["type"], "integer")
        self.assertEqual(days_prop["default"], 7)
        self.assertEqual(days_prop["minimum"], 1)
        self.assertEqual(days_prop["maximum"], 90)
        
        # Test report_type property
        report_type_prop = properties["report_type"]
        self.assertEqual(report_type_prop["type"], "string")
        self.assertEqual(report_type_prop["enum"], ["usage", "quality", "performance", "all"])
        self.assertEqual(report_type_prop["default"], "usage")
    
    def test_get_all_enhanced_schemas(self):
        """Test getting all enhanced schemas"""
        all_schemas = EnhancedToolSchema.get_all_enhanced_schemas()
        
        # Test that all expected tools are present
        self.assertEqual(len(all_schemas), len(self.expected_tools))
        
        schema_names = [schema["name"] for schema in all_schemas]
        for expected_tool in self.expected_tools:
            self.assertIn(expected_tool, schema_names)
        
        # Test that each schema has required structure
        for schema in all_schemas:
            for field in self.required_schema_fields:
                self.assertIn(field, schema, f"Missing {field} in {schema['name']} schema")
            
            # Test input schema structure
            input_schema = schema["inputSchema"]
            for field in self.required_input_schema_fields:
                self.assertIn(field, input_schema, 
                            f"Missing {field} in {schema['name']} input schema")
    
    def test_get_tool_schema_by_name(self):
        """Test getting specific tool schema by name"""
        # Test valid tool names
        for tool_name in self.expected_tools:
            schema = EnhancedToolSchema.get_tool_schema_by_name(tool_name)
            
            self.assertEqual(schema["name"], tool_name)
            self.assertIn("description", schema)
            self.assertIn("inputSchema", schema)
        
        # Test invalid tool name
        with self.assertRaises(ValueError) as context:
            EnhancedToolSchema.get_tool_schema_by_name("invalid_tool")
        
        self.assertIn("Unknown tool name", str(context.exception))
    
    def test_schema_descriptions_quality(self):
        """Test quality and completeness of schema descriptions"""
        all_schemas = EnhancedToolSchema.get_all_enhanced_schemas()
        
        for schema in all_schemas:
            description = schema["description"]
            
            # Check for emoji usage (visual indicators)
            emoji_indicators = ["🧠", "🔍", "📊", "🕒", "🔝", "🧹", "⚠️", "✅", "💡"]
            has_emoji = any(emoji in description for emoji in emoji_indicators)
            self.assertTrue(has_emoji, f"{schema['name']} description should have visual indicators")
            
            # Check for usage guidelines
            guideline_keywords = ["USE", "USAGE", "WHEN", "WORKFLOW", "GUIDELINES"]
            has_guidelines = any(keyword in description for keyword in guideline_keywords)
            self.assertTrue(has_guidelines, f"{schema['name']} should have usage guidelines")
            
            # Check minimum description length (should be informative)
            self.assertGreater(len(description), 100, 
                             f"{schema['name']} description should be comprehensive")
    
    def test_parameter_validation_rules(self):
        """Test parameter validation rules in schemas"""
        # Test add_memory content validation
        add_memory_schema = EnhancedToolSchema.get_add_memory_schema()
        content_prop = add_memory_schema["inputSchema"]["properties"]["content"]
        self.assertEqual(content_prop["minLength"], 10)
        
        # Test search_memory query validation
        search_schema = EnhancedToolSchema.get_search_memory_schema()
        query_prop = search_schema["inputSchema"]["properties"]["query"]
        self.assertEqual(query_prop["minLength"], 2)
        
        # Test limit validations
        limit_prop = search_schema["inputSchema"]["properties"]["limit"]
        self.assertEqual(limit_prop["minimum"], 1)
        self.assertEqual(limit_prop["maximum"], 50)
        
        # Test importance score validations
        importance_prop = add_memory_schema["inputSchema"]["properties"]["importance"]
        self.assertEqual(importance_prop["minimum"], 0.0)
        self.assertEqual(importance_prop["maximum"], 1.0)
    
    def test_usage_hints_completeness(self):
        """Test completeness of usage hints"""
        tools_with_hints = ["add_memory", "search_memory"]
        
        for tool_name in tools_with_hints:
            schema = EnhancedToolSchema.get_tool_schema_by_name(tool_name)
            
            self.assertIn("usage_hints", schema)
            usage_hints = schema["usage_hints"]
            
            # Check for required hint categories
            if tool_name == "add_memory":
                self.assertIn("when_to_use", usage_hints)
                self.assertIn("when_not_to_use", usage_hints)
                self.assertIn("best_practices", usage_hints)
                
                # Check content quality
                self.assertGreater(len(usage_hints["when_to_use"]), 3)
                self.assertGreater(len(usage_hints["when_not_to_use"]), 2)
                self.assertGreater(len(usage_hints["best_practices"]), 2)
            
            elif tool_name == "search_memory":
                self.assertIn("search_strategies", usage_hints)
                self.assertIn("result_handling", usage_hints)
                
                self.assertGreater(len(usage_hints["search_strategies"]), 2)
                self.assertGreater(len(usage_hints["result_handling"]), 2)
    
    def test_schema_json_serialization(self):
        """Test that schemas can be properly JSON serialized"""
        all_schemas = EnhancedToolSchema.get_all_enhanced_schemas()
        
        for schema in all_schemas:
            try:
                json_str = json.dumps(schema, indent=2)
                self.assertIsInstance(json_str, str)
                
                # Test deserialization
                parsed_schema = json.loads(json_str)
                self.assertEqual(parsed_schema["name"], schema["name"])
                
            except (TypeError, ValueError) as e:
                self.fail(f"Schema {schema['name']} is not JSON serializable: {e}")
    
    def test_enum_values_validity(self):
        """Test that enum values in schemas are valid"""
        # Test ltm_analyze output enum
        ltm_analyze_schema = EnhancedToolSchema.get_ltm_analyze_schema()
        output_enum = ltm_analyze_schema["inputSchema"]["properties"]["output"]["enum"]
        self.assertEqual(set(output_enum), {"text", "json"})
        
        # Test ltm_export format enum
        ltm_export_schema = EnhancedToolSchema.get_ltm_export_schema()
        format_enum = ltm_export_schema["inputSchema"]["properties"]["format"]["enum"]
        self.assertEqual(set(format_enum), {"json", "blockchain", "csv"})
        
        # Test usage_analytics report_type enum
        analytics_schema = EnhancedToolSchema.get_usage_analytics_schema()
        report_enum = analytics_schema["inputSchema"]["properties"]["report_type"]["enum"]
        expected_reports = {"usage", "quality", "performance", "all"}
        self.assertEqual(set(report_enum), expected_reports)
    
    def test_default_values_consistency(self):
        """Test consistency of default values across schemas"""
        # Test importance defaults
        add_memory_schema = EnhancedToolSchema.get_add_memory_schema()
        add_memory_importance = add_memory_schema["inputSchema"]["properties"]["importance"]["default"]
        self.assertEqual(add_memory_importance, 0.5)  # Medium importance for LTM
        
        stm_add_schema = EnhancedToolSchema.get_stm_add_schema()
        stm_importance = stm_add_schema["inputSchema"]["properties"]["importance"]["default"]
        self.assertEqual(stm_importance, 0.3)  # Lower importance for STM
        
        # Test limit defaults
        search_schema = EnhancedToolSchema.get_search_memory_schema()
        search_limit = search_schema["inputSchema"]["properties"]["limit"]["default"]
        self.assertEqual(search_limit, 5)  # Reasonable default for search results
        
        # Test threshold defaults
        promote_schema = EnhancedToolSchema.get_stm_promote_schema()
        promote_threshold = promote_schema["inputSchema"]["properties"]["threshold"]["default"]
        self.assertEqual(promote_threshold, 0.8)  # High threshold for promotion
    
    def test_required_fields_logic(self):
        """Test logic of required fields in schemas"""
        # Test add_memory required fields
        add_memory_schema = EnhancedToolSchema.get_add_memory_schema()
        required = add_memory_schema["inputSchema"]["required"]
        self.assertEqual(required, ["content"])  # Only content is required
        
        # Test search_memory required fields
        search_schema = EnhancedToolSchema.get_search_memory_schema()
        required = search_schema["inputSchema"]["required"]
        self.assertEqual(required, ["query"])  # Only query is required
        
        # Test stm_add required fields
        stm_schema = EnhancedToolSchema.get_stm_add_schema()
        required = stm_schema["inputSchema"]["required"]
        self.assertEqual(required, ["content"])  # Only content is required
    
    def test_description_formatting_consistency(self):
        """Test consistent formatting in descriptions"""
        all_schemas = EnhancedToolSchema.get_all_enhanced_schemas()
        
        for schema in all_schemas:
            description = schema["description"]
            
            # Check for consistent emoji usage at start
            self.assertTrue(description.strip().startswith(('🧠', '🔍', '📊', '🕒', '🔝', '🧹', '📤')),
                          f"{schema['name']} should start with appropriate emoji")
            
            # Check for proper line breaks and formatting
            self.assertIn('\n', description, f"{schema['name']} should have multi-line description")
            
            # Check for uppercase section headers
            uppercase_sections = ['USE', 'USAGE', 'WORKFLOW', 'GUIDELINES']
            has_sections = any(section in description for section in uppercase_sections)
            if schema['name'] in ['add_memory', 'search_memory', 'stm_add']:
                self.assertTrue(has_sections, f"{schema['name']} should have formatted sections")
    
    def test_parameter_descriptions_informativeness(self):
        """Test that parameter descriptions are informative"""
        all_schemas = EnhancedToolSchema.get_all_enhanced_schemas()
        
        for schema in all_schemas:
            properties = schema["inputSchema"]["properties"]
            
            for param_name, param_def in properties.items():
                if "description" in param_def:
                    description = param_def["description"]
                    
                    # Should be reasonably informative (more than just type info)
                    self.assertGreater(len(description), 10,
                                     f"{schema['name']}.{param_name} description too brief")
                    
                    # Should not just repeat the parameter name
                    self.assertNotEqual(description.lower(), param_name.lower(),
                                      f"{schema['name']}.{param_name} description is just parameter name")


class TestEnhancedToolSchemaIntegration(BaseGreeumTestCase):
    """Integration tests for EnhancedToolSchema with MCP scenarios"""
    
    def test_mcp_server_integration_scenario(self):
        """Test schema usage in MCP server integration scenario"""
        # Simulate MCP server loading all schemas
        all_schemas = EnhancedToolSchema.get_all_enhanced_schemas()
        
        # Test that schemas can be used to build MCP tool definitions
        mcp_tools = {}
        for schema in all_schemas:
            tool_name = schema["name"]
            mcp_tools[tool_name] = {
                "description": schema["description"],
                "inputSchema": schema["inputSchema"]
            }
        
        # Verify all expected tools are available
        expected_tools = [
            "add_memory", "search_memory", "get_memory_stats", "usage_analytics",
            "ltm_analyze", "ltm_verify", "ltm_export", "stm_add", "stm_promote", "stm_cleanup"
        ]
        
        for tool in expected_tools:
            self.assertIn(tool, mcp_tools)
            self.assertIn("description", mcp_tools[tool])
            self.assertIn("inputSchema", mcp_tools[tool])
    
    def test_llm_autonomous_usage_scenario(self):
        """Test schemas for LLM autonomous usage scenarios"""
        # Test key tools that LLMs would use autonomously
        autonomous_tools = ["add_memory", "search_memory", "get_memory_stats"]
        
        for tool_name in autonomous_tools:
            schema = EnhancedToolSchema.get_tool_schema_by_name(tool_name)
            
            # Should have clear usage guidelines
            description = schema["description"]
            self.assertIn("USE", description.upper())
            
            # Should have parameter validation to prevent misuse
            input_schema = schema["inputSchema"]
            properties = input_schema["properties"]
            
            for param_name, param_def in properties.items():
                if param_def["type"] in ["string", "integer", "number"]:
                    # Should have bounds or validation
                    has_validation = any(key in param_def for key in 
                                       ["minLength", "maxLength", "minimum", "maximum", "enum"])
                    if tool_name == "add_memory" and param_name == "content":
                        self.assertTrue(has_validation, 
                                      f"{tool_name}.{param_name} should have validation")
    
    def test_claude_code_mcp_compatibility(self):
        """Test compatibility with Claude Code MCP expectations"""
        all_schemas = EnhancedToolSchema.get_all_enhanced_schemas()
        
        for schema in all_schemas:
            # Test that schema matches MCP tool schema format
            self.assertIn("name", schema)
            self.assertIn("description", schema)
            self.assertIn("inputSchema", schema)
            
            # Test input schema format
            input_schema = schema["inputSchema"]
            self.assertEqual(input_schema["type"], "object")
            self.assertIn("properties", input_schema)
            
            # Test that descriptions are helpful for LLM understanding
            description = schema["description"]
            self.assertGreater(len(description), 50)  # Substantive description
            
            # Should contain contextual hints
            contextual_indicators = ["when", "use", "how", "what", "why"]
            has_context = any(indicator in description.lower() for indicator in contextual_indicators)
            self.assertTrue(has_context, f"{schema['name']} should have contextual guidance")
    
    def test_workflow_guidance_completeness(self):
        """Test that workflow guidance is complete and actionable"""
        # Test memory management workflow
        add_schema = EnhancedToolSchema.get_add_memory_schema()
        search_schema = EnhancedToolSchema.get_search_memory_schema()
        
        # Add memory should reference search first
        self.assertIn("search_memory first", add_schema["description"])
        
        # Search should be emphasized as primary tool
        self.assertIn("ALWAYS USE THIS FIRST", search_schema["description"])
        
        # Test STM workflow
        stm_add_schema = EnhancedToolSchema.get_stm_add_schema()
        stm_promote_schema = EnhancedToolSchema.get_stm_promote_schema()
        stm_cleanup_schema = EnhancedToolSchema.get_stm_cleanup_schema()
        
        # STM workflow should be connected
        self.assertIn("stm_promote", stm_add_schema["description"])
        self.assertIn("SESSION END", stm_promote_schema["description"])
        self.assertIn("after stm_promote", stm_cleanup_schema["description"])
    
    def test_best_practices_coverage(self):
        """Test that best practices are comprehensively covered"""
        add_memory_schema = EnhancedToolSchema.get_add_memory_schema()
        
        if "usage_hints" in add_memory_schema:
            best_practices = add_memory_schema["usage_hints"]["best_practices"]
            
            # Should cover key areas
            practice_areas = {
                "duplicate_prevention": False,
                "content_quality": False,  
                "importance_setting": False,
                "context_inclusion": False
            }
            
            for practice in best_practices:
                practice_lower = practice.lower()
                if "search" in practice_lower and "duplicate" in practice_lower:
                    practice_areas["duplicate_prevention"] = True
                if "descriptive" in practice_lower or "searchable" in practice_lower:
                    practice_areas["content_quality"] = True
                if "importance" in practice_lower:
                    practice_areas["importance_setting"] = True
                if "context" in practice_lower:
                    practice_areas["context_inclusion"] = True
            
            # Most areas should be covered
            covered_areas = sum(practice_areas.values())
            self.assertGreaterEqual(covered_areas, 3, "Should cover most best practice areas")


if __name__ == '__main__':
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add all test cases
    suite.addTest(unittest.makeSuite(TestEnhancedToolSchema))
    suite.addTest(unittest.makeSuite(TestEnhancedToolSchemaIntegration))
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"EnhancedToolSchema Test Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print(f"{'='*50}")
    
    # Print schema overview
    print(f"\nSchema Generation Test:")
    try:
        all_schemas = EnhancedToolSchema.get_all_enhanced_schemas()
        print(f"✅ Successfully generated {len(all_schemas)} enhanced tool schemas")
        for schema in all_schemas:
            print(f"  - {schema['name']}: {len(schema['description'])} chars description")
    except Exception as e:
        print(f"❌ Schema generation failed: {e}")