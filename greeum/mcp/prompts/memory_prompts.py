"""
Memory-related prompts for GreeumMCP.

This module implements MCP prompts for generating memory-enhanced contexts.
"""
from typing import Dict, List, Any, Optional
import json

class MemoryPrompts:
    """Memory prompt implementation for GreeumMCP."""
    
    def __init__(self, greeum_adapter):
        """
        Initialize memory prompts.
        
        Args:
            greeum_adapter: GreeumAdapter instance
        """
        self.adapter = greeum_adapter
    
    def memory_context(self, user_input: str, include_stm: bool = True) -> str:
        """
        Generate a prompt with memory context.
        
        Args:
            user_input: User input to provide context for
            include_stm: Whether to include short-term memories
        
        Returns:
            Prompt with memory context
        """
        return self.adapter.prompt_wrapper.compose_prompt(
            user_input=user_input,
            include_stm=include_stm,
            max_blocks=3,
            max_stm=5
        )
    
    def time_based_recall(self, time_reference: str, contextual_prompt: str) -> str:
        """
        Generate a prompt with time-based recall.
        
        Args:
            time_reference: Time reference to search for
            contextual_prompt: Additional contextual prompt
        
        Returns:
            Prompt with time-based recall
        """
        # Get memories based on time reference
        memories = self.adapter.temporal_reasoner.search_by_time_reference(
            time_reference,
            margin_hours=12
        )
        
        # Format memories as text
        memory_text = ""
        if memories:
            for i, memory in enumerate(memories):
                memory_text += f"\nMemory {i+1}: {memory.get('context', '')}\n"
        else:
            memory_text = "No memories found for this time reference."
        
        # Generate prompt template
        prompt = f"""
Time Reference: {time_reference}

Relevant Memories:
{memory_text}

Context: {contextual_prompt}

Please respond based on the provided memories and context.
"""
        
        return prompt
    
    def memory_organization(self, memory_subset: List[Dict[str, Any]], organization_goal: str) -> str:
        """
        Generate a prompt for memory organization.
        
        Args:
            memory_subset: List of memories to organize
            organization_goal: Goal of the organization
        
        Returns:
            Prompt for memory organization
        """
        # Format memories as text
        memory_text = ""
        if memory_subset:
            for i, memory in enumerate(memory_subset):
                memory_text += f"\nMemory {i+1}: {memory.get('context', memory.get('content', ''))}\n"
                if memory.get('timestamp'):
                    memory_text += f"Timestamp: {memory.get('timestamp')}\n"
                if memory.get('keywords'):
                    memory_text += f"Keywords: {', '.join(memory.get('keywords', []))}\n"
        else:
            memory_text = "No memories provided for organization."
        
        # Generate prompt template
        prompt = f"""
Memory Organization Goal: {organization_goal}

Memories to Organize:
{memory_text}

Please organize these memories according to the specified goal.
"""
        
        return prompt 