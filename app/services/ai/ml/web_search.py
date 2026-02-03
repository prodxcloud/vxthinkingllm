"""
Web search integration for VaLLM - Cloud/DevOps focused
Prioritizes trusted sources: HashiCorp, IBM, StackOverflow, Medium, etc.
"""

import requests
from urllib.parse import quote
from typing import List, Dict, Any, Optional
import logging
import json

logger = logging.getLogger("vallm")


class CloudDevOpsWebSearch:
    """
    Web search optimized for Cloud, DevOps, Programming, Observability,
    Networking, and IT Support queries with trusted source prioritization.
    """
    
    # Trusted sources for Cloud/DevOps/Programming
    TRUSTED_SOURCES = {
        'documentation': [
            'python.org',
            'docs.aws.amazon.com',
            'docs.microsoft.com/azure',
            'cloud.google.com/docs',
            'kubernetes.io',
            'docker.com/docs',
            'terraform.io',
            'ansible.com/docs'
        ],
        'community': [
            'stackoverflow.com',
            'serverfault.com',
            'superuser.com',
            'github.com',
            'gitlab.com'
        ],
        'blogs': [
            'medium.com',
            'dev.to',
            'hashnode.com',
            'hackernoon.com'
        ],
        'vendors': [
            'hashicorp.com',
            'ibm.com',
            'redhat.com',
            'nginx.com',
            'apache.org',
            'jetbrains.com',
            'atlassian.com'
        ],
        'monitoring': [
            'prometheus.io',
            'grafana.com',
            'datadoghq.com',
            'newrelic.com',
            'elastic.co'
        ]
    }
    
    def __init__(self, max_results: int = 5, prioritize_sources: bool = True):
        """Initialize web search for cloud/devops queries."""
        self.max_results = max_results
        self.prioritize_sources = prioritize_sources
        self.domain_keywords = {
            'cloud': ['aws', 'azure', 'gcp', 'cloud', 'iaas', 'paas'],
            'devops': ['kubernetes', 'docker', 'cicd', 'jenkins', 'terraform'],
            'networking': ['vpc', 'subnet', 'dns', 'loadbalancer', 'vpn'],
            'observability': ['prometheus', 'grafana', 'datadog', 'logs', 'metrics'],
            'programming': ['python', 'bash', 'golang', 'api', 'sdk'],
            'it_support': ['troubleshoot', 'incident', 'resolution', 'fix']
        }
        logger.info("CloudDevOps Web Search initialized with trusted sources")
    
    def get_all_trusted_sources(self) -> List[str]:
        """Get flattened list of all trusted sources."""
        sources = []
        for category in self.TRUSTED_SOURCES.values():
            sources.extend(category)
        return sources
    
    def search(self, query: str, domain_focus: str = "cloud", 
               specific_sources: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Perform web search with domain-specific enhancement and source filtering.
        
        Args:
            query: User query
            domain_focus: One of: cloud, devops, networking, observability, programming, it_support
            specific_sources: Optional list of specific sources to search
            
        Returns:
            List of search results prioritized by trusted sources
        """
        # Enhance query with domain keywords
        enhanced_query = self._enhance_query(query, domain_focus)
        
        try:
            # Get base results
            results = self._search_duckduckgo(enhanced_query)
            
            # Search trusted sources specifically
            if self.prioritize_sources:
                trusted_results = self._search_trusted_sources(
                    query, domain_focus, specific_sources
                )
                results.extend(trusted_results)
            
            # Deduplicate and prioritize
            results = self._deduplicate_and_prioritize(results)
            
            return results[:self.max_results]
            
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return []
    
    def _enhance_query(self, query: str, domain_focus: str) -> str:
        """Add domain-specific keywords to improve relevance."""
        domain_terms = self.domain_keywords.get(domain_focus, [])
        
        # Add focus keywords if not already in query
        q_lower = query.lower()
        for term in domain_terms[:2]:  # Add up to 2 relevant terms
            if term not in q_lower:
                query = f"{query} {term}"
                break
        
        return query
    
    def _search_trusted_sources(
        self, 
        query: str, 
        domain_focus: str,
        specific_sources: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search specifically within trusted sources using site: operator.
        
        Args:
            query: Search query
            domain_focus: Domain focus area
            specific_sources: Specific sources to target
            
        Returns:
            List of results from trusted sources
        """
        results = []
        
        # Determine which sources to search
        if specific_sources:
            sources_to_search = specific_sources
        else:
            # Select sources based on domain focus
            if domain_focus in ['cloud', 'devops']:
                sources_to_search = [
                    'hashicorp.com',
                    'terraform.io',
                    'kubernetes.io',
                    'docs.aws.amazon.com',
                    'stackoverflow.com',
                    'medium.com',
                    'ibm.com'
                ]
            elif domain_focus == 'programming':
                sources_to_search = [
                    'python.org',
                    'stackoverflow.com',
                    'github.com',
                    'medium.com',
                    'dev.to'
                ]
            elif domain_focus == 'observability':
                sources_to_search = [
                    'prometheus.io',
                    'grafana.com',
                    'datadoghq.com',
                    'elastic.co',
                    'medium.com'
                ]
            else:
                sources_to_search = self.get_all_trusted_sources()[:5]
        
        # Search each trusted source
        for source in sources_to_search[:3]:  # Limit to 3 sources to avoid rate limits
            try:
                site_query = f"site:{source} {query}"
                site_results = self._search_duckduckgo(site_query, max_results=2)
                
                for result in site_results:
                    result['trusted_source'] = source
                    result['source_category'] = self._get_source_category(source)
                    results.append(result)
                    
            except Exception as e:
                logger.warning(f"Failed to search {source}: {e}")
                continue
        
        return results
    
    def _get_source_category(self, source: str) -> str:
        """Determine the category of a trusted source."""
        for category, sources in self.TRUSTED_SOURCES.items():
            if any(source in s or s in source for s in sources):
                return category
        return 'general'
    
    def _search_duckduckgo(self, query: str, max_results: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search using DuckDuckGo API (free, no key required)."""
        if max_results is None:
            max_results = self.max_results
            
        try:
            # Use DuckDuckGo Instant Answer API
            url = "https://api.duckduckgo.com/"
            params = {
                "q": query,
                "format": "json",
                "no_html": 1,
                "skip_disambig": 1
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            results = []
            
            # Get abstract/answer
            if data.get("Abstract"):
                results.append({
                    "title": data.get("Heading", "Answer"),
                    "url": data.get("AbstractURL", ""),
                    "snippet": data.get("Abstract", ""),
                    "source": "duckduckgo_instant",
                    "is_trusted": self._is_trusted_url(data.get("AbstractURL", ""))
                })
            
            # Get related topics
            for topic in data.get("RelatedTopics", [])[:max_results]:
                if isinstance(topic, dict) and "Text" in topic:
                    url = topic.get("FirstURL", "")
                    results.append({
                        "title": topic.get("Text", "").split(" - ")[0],
                        "url": url,
                        "snippet": topic.get("Text", ""),
                        "source": "duckduckgo_related",
                        "is_trusted": self._is_trusted_url(url)
                    })
            
            logger.info(f"DuckDuckGo search: {len(results)} results for '{query}'")
            return results
            
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
            return []
    
    def _is_trusted_url(self, url: str) -> bool:
        """Check if URL is from a trusted source."""
        if not url:
            return False
        
        url_lower = url.lower()
        all_sources = self.get_all_trusted_sources()
        return any(source in url_lower for source in all_sources)
    
    def _deduplicate_and_prioritize(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicates and prioritize trusted sources.
        
        Scoring:
        - Trusted sources: +10 points
        - Documentation: +5 points
        - Has snippet: +2 points
        """
        seen_urls = set()
        unique_results = []
        
        for result in results:
            url = result.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                
                # Calculate priority score
                score = 0
                if result.get('is_trusted', False):
                    score += 10
                if result.get('source_category') == 'documentation':
                    score += 5
                if result.get('snippet'):
                    score += 2
                
                result['priority_score'] = score
                unique_results.append(result)
        
        # Sort by priority score (descending)
        unique_results.sort(key=lambda x: x.get('priority_score', 0), reverse=True)
        
        logger.info(f"Deduplicated: {len(results)} -> {len(unique_results)} results")
        return unique_results
    
    def deep_search(self, query: str, domain_focus: str = "cloud",
                   specific_sources: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Perform deep search with context aggregation and trusted source focus.
        
        Returns:
            Dictionary with results and aggregated context
        """
        # Initial search with trusted sources
        results = self.search(query, domain_focus, specific_sources)
        
        # Aggregate context with source attribution
        context_parts = []
        trusted_count = 0
        
        for r in results:
            is_trusted = r.get('is_trusted', False)
            source_cat = r.get('source_category', 'general')
            trusted_marker = " ✓ [TRUSTED]" if is_trusted else ""
            
            context_parts.append(
                f"**{r['title']}**{trusted_marker}\n"
                f"Category: {source_cat}\n"
                f"{r['snippet'][:300]}...\n"
                f"Source: {r['url']}\n"
            )
            
            if is_trusted:
                trusted_count += 1
        
        context_text = "\n\n".join(context_parts)
        
        return {
            "query": query,
            "domain_focus": domain_focus,
            "results": results,
            "context": context_text,
            "total_results": len(results),
            "trusted_results": trusted_count,
            "trusted_sources_available": self.get_all_trusted_sources()
        }

