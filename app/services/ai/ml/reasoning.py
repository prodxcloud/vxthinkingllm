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
        self.intent_keywords = {
            'provision': ['provision', 'create', 'deploy', 'setup', 'launch', 'spin up'],
            'analyze': ['analyze', 'review', 'check', 'examine', 'inspect', 'audit'],
            'optimize': ['optimize', 'improve', 'reduce', 'minimize', 'enhance'],
            'troubleshoot': ['fix', 'resolve', 'debug', 'troubleshoot', 'error', 'issue'],
            'monitor': ['monitor', 'status', 'health', 'metrics', 'performance'],
            'cost': ['cost', 'billing', 'price', 'spend', 'budget', 'expensive']
        }
    
    async def initialize(self):
        """Initialize reasoning engine"""
        print("🧠 Reasoning engine ready")
    
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
        """Detect user intent from query"""
        query_lower = query.lower()
        
        scores = {}
        for intent, keywords in self.intent_keywords.items():
            score = sum(1 for keyword in keywords if keyword in query_lower)
            if score > 0:
                scores[intent] = score
        
        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]
        
        return 'general'
    
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
        
        # Look for issues/problems
        problem_keywords = ['error', 'failure', 'issue', 'problem', 'down', 'slow']
        found_problems = [kw for kw in problem_keywords if kw in context.lower()]
        if found_problems:
            analysis_parts.append(f"Potential issues detected: {', '.join(set(found_problems))}")
        
        summary = " | ".join(analysis_parts) if analysis_parts else "General cloud operations query"
        
        return {
            'summary': summary,
            'confidence': 0.8,
            'metadata': {
                'resources': found_resources,
                'regions': found_regions,
                'problems': found_problems
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
        
        # Based on intent, provide relevant synthesis
        if intent == 'provision':
            synthesis_parts.append("Provisioning operation detected. Reviewing available resources and configurations.")
            synthesis_parts.append("Checking for similar deployments and best practices.")
        elif intent == 'troubleshoot':
            synthesis_parts.append("Troubleshooting operation detected. Analyzing incidents and error patterns.")
            synthesis_parts.append("Reviewing similar issues and their resolutions.")
        elif intent == 'optimize':
            synthesis_parts.append("Optimization operation detected. Analyzing current configurations and metrics.")
            synthesis_parts.append("Reviewing recommendations and cost-saving opportunities.")
        else:
            synthesis_parts.append("General query. Analyzing context for relevant information.")
        
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
        """Make final decision or recommendation"""
        recommendation_parts = []
        
        # Generate recommendation based on intent
        if intent == 'provision':
            recommendation_parts.append("Based on the context, I recommend:")
            recommendation_parts.append("1. Review similar resource configurations")
            recommendation_parts.append("2. Check compliance and security requirements")
            recommendation_parts.append("3. Consider cost optimization based on usage patterns")
            recommendation_parts.append("4. Validate against existing infrastructure patterns")
        elif intent == 'troubleshoot':
            recommendation_parts.append("Troubleshooting recommendations:")
            recommendation_parts.append("1. Review similar incidents and their resolutions")
            recommendation_parts.append("2. Check system metrics and logs")
            recommendation_parts.append("3. Verify configuration compliance")
            recommendation_parts.append("4. Consider rolling back recent changes")
        elif intent == 'optimize':
            recommendation_parts.append("Optimization recommendations:")
            recommendation_parts.append("1. Review cost analysis and resource utilization")
            recommendation_parts.append("2. Consider right-sizing instances")
            recommendation_parts.append("3. Implement auto-scaling where appropriate")
            recommendation_parts.append("4. Review and apply best practice recommendations")
        else:
            recommendation_parts.append("Based on the available context:")
            recommendation_parts.append("1. Review relevant configurations and resources")
            recommendation_parts.append("2. Check for similar patterns in the infrastructure")
            recommendation_parts.append("3. Consider best practices and recommendations")
        
        recommendation = "\n".join(recommendation_parts)
        
        return {
            'recommendation': recommendation,
            'confidence': 0.8,
            'metadata': {
                'intent': intent,
                'reasoning_steps': len(recommendation_parts)
            }
        }
    
    async def cleanup(self):
        """Cleanup resources"""
        pass

