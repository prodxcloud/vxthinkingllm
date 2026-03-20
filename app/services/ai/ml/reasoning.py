"""
Chain of Thoughts Reasoning Engine
Implements agent-to-agent thinking patterns for cloud operations
"""

import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from .embeddings import VectorStore


@dataclass
class ReasoningStep:
    """Represents a single reasoning step"""
    step_type: str  # 'search', 'analyze', 'synthesize', 'decide'
    content: str
    confidence: float
    metadata: Dict[str, Any]


class ReasoningEngine:
    """Chain of thoughts reasoning for cloud operations"""
    
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        # Provisioning-only: single intent for deployment/provision flows
        self.intent_keywords = {
            'provision': ['provision', 'create', 'deploy', 'setup', 'launch', 'spin up', 'run', 'host', 'install'],
        }
    
    async def initialize(self):
        """Initialize reasoning engine"""
        try:
            print("🧠 Reasoning engine ready")
        except UnicodeEncodeError:
            print("Reasoning engine ready")
    
    async def reason(
        self,
        query: str,
        context: Optional[str] = None,
        max_steps: int = 5
    ) -> Dict[str, Any]:
        """
        Perform chain of thoughts reasoning
        
        Args:
            query: User query
            context: Optional context string
            max_steps: Maximum reasoning steps
        
        Returns:
            Reasoning result with steps and final answer
        """
        steps = []
        current_context = context or ""
        
        # Step 1: Intent Detection
        intent = await self._detect_intent(query)
        steps.append(ReasoningStep(
            step_type='analyze',
            content=f"Detected intent: {intent}",
            confidence=0.9,
            metadata={'intent': intent}
        ))
        
        # Step 2: Context Gathering
        if not current_context:
            context_results = await self.vector_store.search(query, top_k=10)
            current_context = await self._format_context(context_results)
            steps.append(ReasoningStep(
                step_type='search',
                content=f"Gathered {len(context_results)} relevant documents",
                confidence=0.85,
                metadata={'documents_found': len(context_results)}
            ))
        
        # Step 3: Analysis
        analysis = await self._analyze(query, current_context, intent)
        steps.append(ReasoningStep(
            step_type='analyze',
            content=analysis['summary'],
            confidence=analysis['confidence'],
            metadata=analysis.get('metadata', {})
        ))
        
        # Step 4: Synthesis
        synthesis = await self._synthesize(query, current_context, analysis, intent)
        steps.append(ReasoningStep(
            step_type='synthesize',
            content=synthesis['summary'],
            confidence=synthesis['confidence'],
            metadata=synthesis.get('metadata', {})
        ))
        
        # Step 5: Decision/Recommendation
        decision = await self._make_decision(query, synthesis, intent)
        steps.append(ReasoningStep(
            step_type='decide',
            content=decision['recommendation'],
            confidence=decision['confidence'],
            metadata=decision.get('metadata', {})
        ))
        
        return {
            'query': query,
            'intent': intent,
            'steps': [
                {
                    'type': step.step_type,
                    'content': step.content,
                    'confidence': step.confidence,
                    'metadata': step.metadata
                }
                for step in steps
            ],
            'final_answer': decision['recommendation'],
            'confidence': decision['confidence'],
            'context_used': current_context[:500] + "..." if len(current_context) > 500 else current_context
        }
    
    async def _detect_intent(self, query: str) -> str:
        """
        Detect user intent from query.
        DO NOT guess - use exact matches from knowledge base only.
        Returns 'provision' if provisioning keywords found, otherwise 'unknown'.
        """
        query_lower = query.lower()
        
        # Only detect provisioning intent if keywords are present
        # Do not guess other intents - let the knowledge base determine
        scores = {}
        for intent, keywords in self.intent_keywords.items():
            score = sum(1 for keyword in keywords if keyword in query_lower)
            if score > 0:
                scores[intent] = score
        
        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]
        
        # Return 'unknown' instead of 'general' - let knowledge base determine
        return 'unknown'
    
    async def _format_context(self, results: List[Dict[str, Any]]) -> str:
        """Format search results into context string"""
        context_parts = []
        for i, result in enumerate(results, 1):
            metadata = result.get('metadata', {})
            if not isinstance(metadata, dict):
                metadata = {}
            doc_type = metadata.get('type', 'unknown')
            score = result.get('score', 0)
            document = result.get('document', '')
            context_parts.append(
                f"[{i}] {doc_type.upper()} (relevance: {score:.2f}): {document}"
            )
        return "\n".join(context_parts)
    
    async def _analyze(
        self,
        query: str,
        context: str,
        intent: str
    ) -> Dict[str, Any]:
        """Analyze query against context"""
        # Extract key information from context
        analysis_parts = []
        
        # Look for resource types
        resource_types = ['vm', 'instance', 'database', 'storage', 'network', 'kubernetes', 'container']
        found_resources = [rt for rt in resource_types if rt in context.lower()]
        if found_resources:
            analysis_parts.append(f"Identified resource types: {', '.join(found_resources)}")
        
        # Look for regions
        regions = ['us-east', 'us-west', 'eu-', 'ap-', 'global']
        found_regions = [r for r in regions if r in context.lower()]
        if found_regions:
            analysis_parts.append(f"Identified regions: {', '.join(set(found_regions))}")
        
        summary = " | ".join(analysis_parts) if analysis_parts else "Provisioning and deployment context"
        
        return {
            'summary': summary,
            'confidence': 0.8,
            'metadata': {
                'resources': found_resources,
                'regions': found_regions,
            }
        }
    
    async def _synthesize(
        self,
        query: str,
        context: str,
        analysis: Dict[str, Any],
        intent: str
    ) -> Dict[str, Any]:
        """Synthesize information into actionable insights"""
        synthesis_parts = []
        
        # Provisioning-only synthesis
        if intent == 'provision':
            synthesis_parts.append("Provisioning operation detected. Reviewing available resources and configurations.")
            synthesis_parts.append("Checking for similar deployments and best practices.")
        else:
            synthesis_parts.append("Deployment-related query. Analyzing context for provisioning patterns.")
        
        # Add analysis insights
        if analysis.get('metadata'):
            metadata = analysis['metadata']
            if metadata.get('resources'):
                synthesis_parts.append(f"Focusing on: {', '.join(metadata['resources'])}")
        
        summary = " ".join(synthesis_parts)
        
        return {
            'summary': summary,
            'confidence': 0.85,
            'metadata': analysis.get('metadata', {})
        }
    
    async def _make_decision(
        self,
        query: str,
        synthesis: Dict[str, Any],
        intent: str
    ) -> Dict[str, Any]:
        """
        Make final decision or recommendation.
        MUST follow procedures from cloud_operations_provisionning_knowledge1.txt and knowledge2.txt.
        DO NOT guess intent - use exact matches from knowledge base only.
        """
        # Get the best matching document from context
        context_results = await self.vector_store.search(query, top_k=1)
        
        if not context_results:
            # No match found - return generic response, do not guess
            return {
                'recommendation': "No matching provisioning pattern found in knowledge base. Please provide more specific details about the resource you want to provision.",
                'confidence': 0.0,
                'metadata': {
                    'intent': 'unknown',
                    'reasoning_steps': 0,
                    'matched': False
                }
            }
        
        best_match = context_results[0]
        match_score = best_match.get('score', 0.0)
        match_doc = best_match.get('document', '')
        match_meta = best_match.get('metadata', {})
        
        # Only proceed if we have a strong match (score > 0.3 for cosine similarity)
        if match_score < 0.3:
            return {
                'recommendation': "No strong match found in knowledge base. Please provide more specific details.",
                'confidence': match_score,
                'metadata': {
                    'intent': 'unknown',
                    'reasoning_steps': 0,
                    'matched': False,
                    'best_score': match_score
                }
            }
        
        # Extract intent from metadata if available (from cloud_deployments CSV)
        raw = match_meta.get('raw', {})
        detected_intent = raw.get('intent', 'provision') if isinstance(raw, dict) else 'provision'
        
        # Build recommendation based on exact knowledge base match
        recommendation_parts = []
        recommendation_parts.append(f"Based on knowledge base match (score: {match_score:.2f}):")
        recommendation_parts.append(f"Matched pattern: {match_doc[:200]}...")
        
        # Include specific provisioning guidance from knowledge files
        if detected_intent == 'provision':
            recommendation_parts.append("\nProvisioning steps:")
            recommendation_parts.append("1. Validate all required fields are present in the payload")
            recommendation_parts.append("2. Check compliance and security requirements per knowledge base")
            recommendation_parts.append("3. Apply deployment best practices from cloud_operations_provisionning_knowledge files")
            recommendation_parts.append("4. Ensure payload structure matches Golang provisioner API expectations")
        
        recommendation = "\n".join(recommendation_parts)
        
        return {
            'recommendation': recommendation,
            'confidence': match_score,
            'metadata': {
                'intent': detected_intent,
                'reasoning_steps': len(recommendation_parts),
                'matched': True,
                'match_score': match_score,
                'match_document': match_doc[:500]
            }
        }
    
    async def cleanup(self):
        """Cleanup resources"""
        pass

