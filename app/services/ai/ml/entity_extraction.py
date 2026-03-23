"""
Entity Extraction Module for VaLLM - Extract specific values from user queries.

This module parses user queries to extract specific entities like hostnames, 
app names, regions, instance types, etc. that should override training data values.
"""

import re
import logging
from typing import Dict, Optional, Any, List, Union
from urllib.parse import urlparse

logger = logging.getLogger("vallm.entity_extraction")


class EntityExtractor:
    """Extract entities from user provisioning queries."""
    
    def __init__(self):
        # Hostname patterns - improved for complex domains
        self.hostname_patterns = [
            r'\b(?:on|to|at|deploy\s+(?:to|on))\s+([a-zA-Z0-9][-a-zA-Z0-9]*(?:\.[a-zA-Z0-9][-a-zA-Z0-9]*)*\.[a-zA-Z]{2,})\b',
            r'\bhostname[:\s]+([a-zA-Z0-9][-a-zA-Z0-9]*(?:\.[a-zA-Z0-9][-a-zA-Z0-9]*)*\.[a-zA-Z]{2,})\b',
            r'\b([a-zA-Z0-9][-a-zA-Z0-9]*(?:\.[a-zA-Z0-9][-a-zA-Z0-9]*)*\.(?:com|org|net|io|dev|local|internal))\b',
        ]
        
        # App name patterns
        self.app_name_patterns = [
            r'\b(?:app|application)\s+([a-zA-Z][a-zA-Z0-9_-]*)\b',
            r'\b([a-zA-Z][a-zA-Z0-9_-]*)-(?:api|app|service)\b',
            r'\bFastAPI\s+app\s+([a-zA-Z][a-zA-Z0-9_-]*)\b',
            r'\bservice\s+([a-zA-Z][a-zA-Z0-9_-]+)\b'
        ]
        
        # Database patterns - improved to handle underscores
        self.db_name_patterns = [
            r'\b(?:database|db)\s+(?:named?|called?)\s+([a-zA-Z][a-zA-Z0-9_]*)\b',
            r'\bname\s+([a-zA-Z][a-zA-Z0-9_]*(?:_db|_database)?)\b',
            r'\b(?:MySQL|PostgreSQL|database)\s+([a-zA-Z][a-zA-Z0-9_]+)\b'
        ]
        
        # Database user patterns  
        self.db_user_patterns = [
            r'\b(?:user|username)\s+([a-zA-Z][a-zA-Z0-9_]*)\b'
        ]
        
        # Instance type patterns - ordered by specificity (most specific first)
        self.instance_type_patterns = [
            # RDS/managed DB instance classes FIRST (db.t3.medium, db.r5.large) - before AWS patterns
            r'\b(db\.[a-z][0-9][a-z]?\.[a-z0-9]+)\b',
            # GCP instance types (n2-standard-4, e2-medium, c2-standard-8, e2-micro, etc.)
            r'\b((?:n[12]|e2|c2|a2|g2|m[12])-(?:standard|highmem|highcpu|micro|small|medium)(?:-\d+)?)\b',
            # Azure instance types (Standard_B2s, Standard_D4s_v3)
            r'\b(Standard_[A-Z][a-zA-Z0-9_]+(?:_v\d+)?)\b',
            # AWS instance types (t2-t4g, m4-m7i, c4-c7g, r4-r7i, p3, g4, i3, d2)
            r'\b(t[2-4]g?\.[a-z0-9]+)\b',
            r'\b(m[4-7][a-z]?\.[a-z0-9]+)\b',
            r'\b(c[4-7][a-z]?\.[a-z0-9]+)\b',
            r'\b(r[4-7][a-z]?\.[a-z0-9]+)\b',
            r'\b(p[2-5][a-z]?\.[a-z0-9]+)\b',
            r'\b(g[4-5][a-z]?\.[a-z0-9]+)\b',
            r'\b(i[3-4][a-z]?\.[a-z0-9]+)\b',
            r'\b(d[2-3][a-z]?\.[a-z0-9]+)\b',
        ]

        # Region patterns - all major cloud regions
        self.region_patterns = [
            r'\b(us-(?:east|west)-[12])\b',
            r'\b(us-east-2)\b',
            r'\b(eu-(?:central|west|north|south)-[1-3])\b',
            r'\b(ap-(?:southeast|northeast|south|east)-[1-3])\b',
            r'\b(ca-central-1)\b',
            r'\b(sa-east-1)\b',
            r'\b(me-(?:south|central)-1)\b',
            r'\b(af-south-1)\b',
            # GCP regions
            r'\b((?:us|europe|asia|australia|southamerica|northamerica)-(?:central|east|west|north|south|southeast|northeast)\d?)\b',
            # Azure regions
            r'\b((?:east|west|central|north|south)(?:us|europe|asia|india|japan|australia|uk|canada|brazil|korea|france|germany|norway|switzerland|uae|southafrica)(?:\d)?)\b',
        ]

        # Cloud provider detection patterns
        self.cloud_provider_patterns = [
            (r'\b(?:aws|amazon\s*web\s*services|ec2|s3|lambda|eks|rds|cloudfront)\b', 'aws'),
            (r'\b(?:gcp|google\s*cloud|gke|gce|cloud\s*run|bigquery|compute\s*engine)\b', 'gcp'),
            (r'\b(?:azure|microsoft\s*azure|aks|azure\s*vm|azure\s*sql)\b', 'azure'),
            (r'\b(?:digitalocean|droplet|doks)\b', 'digitalocean'),
            (r'\b(?:valtunox)\b', 'valtunox'),
        ]

        # Database engine detection patterns
        self.db_engine_patterns = [
            (r'\b(?:postgresql|postgres|pg)\b', 'postgresql'),
            (r'\b(?:mysql)\b', 'mysql'),
            (r'\b(?:mariadb)\b', 'mariadb'),
            (r'\b(?:mongodb|mongo)\b', 'mongodb'),
            (r'\b(?:aurora[- ]postgresql|aurora[- ]postgres)\b', 'aurora-postgresql'),
            (r'\b(?:aurora[- ]mysql|aurora)\b', 'aurora-mysql'),
            (r'\b(?:redis)\b', 'redis'),
            (r'\b(?:mssql|sql\s*server)\b', 'mssql'),
        ]

        # Monitoring tool detection
        self.monitoring_tool_patterns = [
            (r'\b(?:prometheus)\b', 'prometheus'),
            (r'\b(?:grafana)\b', 'grafana'),
            (r'\b(?:zabbix)\b', 'zabbix'),
            (r'\b(?:datadog)\b', 'datadog'),
            (r'\b(?:nagios)\b', 'nagios'),
            (r'\b(?:new\s*relic)\b', 'newrelic'),
        ]

        # CICD tool detection
        self.cicd_tool_patterns = [
            (r'\b(?:jenkins)\b', 'jenkins'),
            (r'\b(?:argocd|argo\s*cd)\b', 'argocd'),
            (r'\b(?:github[- ]actions[- ]runner|github[- ]runner)\b', 'github-actions-runner'),
            (r'\b(?:gitlab[- ]runner)\b', 'gitlab-runner'),
            (r'\b(?:tekton)\b', 'tekton'),
            (r'\b(?:drone)\b', 'drone'),
        ]

        # VPN protocol detection
        self.vpn_protocol_patterns = [
            (r'\b(?:wireguard)\b', 'wireguard'),
            (r'\b(?:openvpn)\b', 'openvpn'),
            (r'\b(?:ipsec)\b', 'ipsec'),
        ]

        # OS detection patterns
        self.os_patterns = [
            (r'\b(?:ubuntu[- ]?24\.04)\b', 'ubuntu-24.04'),
            (r'\b(?:ubuntu[- ]?22\.04)\b', 'ubuntu-22.04'),
            (r'\b(?:ubuntu)\b', 'ubuntu'),
            (r'\b(?:debian[- ]?12)\b', 'debian-12'),
            (r'\b(?:debian)\b', 'debian-12'),
            (r'\b(?:centos[- ]?stream[- ]?9)\b', 'centos-stream-9'),
            (r'\b(?:centos)\b', 'centos'),
            (r'\b(?:amazon[- ]linux[- ]2)\b', 'amazon-linux-2'),
            (r'\b(?:windows[- ]server[- ]2022)\b', 'windows-server-2022'),
            (r'\b(?:windows)\b', 'windows-server-2022'),
        ]
        
        # Port patterns
        self.port_patterns = [
            r'\bport\s+(\d{2,5})\b',
            r'\bports?\s+(\d{2,5}):(\d{2,5})\b',
            r'\b:(\d{2,5})\b'
        ]
        
        # Container/image patterns
        self.image_patterns = [
            r'\b(nginx(?::[a-zA-Z0-9._-]+)?)\b',
            r'\b(postgres(?::[a-zA-Z0-9._-]+)?)\b',
            r'\b(mysql(?::[a-zA-Z0-9._-]+)?)\b',
            r'\b(redis(?::[a-zA-Z0-9._-]+)?)\b',
            r'\b([a-zA-Z0-9._/-]+):([a-zA-Z0-9._-]+)\b'
        ]
        
        # Version patterns  
        self.version_patterns = [
            r'\bversion\s+(\d+(?:\.\d+)*)\b',
            r'\bv(\d+(?:\.\d+)*)\b',
            r'\bkubernetes\s+(\d+(?:\.\d+)*)\b'
        ]
        
        # Storage/volume patterns
        self.storage_patterns = [
            r'\b(\d+)GB?\b',
            r'\bvolume\s+(\d+)GB?\b',
            r'\bdisk\s+(\d+)GB?\b'
        ]

    def extract_entities(self, query: str) -> Dict[str, Any]:
        """
        Extract all relevant entities from a user query.
        
        Args:
            query: The user's natural language query
            
        Returns:
            Dict containing extracted entities
        """
        if not query:
            return {}
            
        query_lower = query.lower()
        entities = {}
        
        # Extract hostname
        hostname = self._extract_hostname(query)
        if hostname:
            entities['hostname'] = hostname
            entities['server_name'] = hostname  # For static websites
            
        # Extract app name
        app_name = self._extract_app_name(query)
        if app_name:
            entities['app_name'] = app_name
            entities['container_name'] = f"{app_name}-container"
            
        # Extract database info
        db_name = self._extract_database_name(query)
        if db_name:
            entities['database_name'] = db_name
            
        db_user = self._extract_database_user(query)
        if db_user:
            entities['database_user'] = db_user
            
        # Extract instance type
        instance_type = self._extract_instance_type(query)
        if instance_type:
            entities['instance_type'] = instance_type
            entities['node_type'] = instance_type  # For Kubernetes
            
        # Extract region  
        region = self._extract_region(query)
        if region:
            entities['region'] = region
            
        # Extract ports
        ports = self._extract_ports(query)
        if ports:
            entities.update(ports)
            
        # Extract container/image
        image = self._extract_image(query)
        if image:
            entities['docker_image'] = image
            entities['image'] = image
            
        # Extract version
        version = self._extract_version(query)
        if version:
            entities['kubernetes_version'] = version
            entities['postgres_version'] = version
            
        # Extract storage
        storage = self._extract_storage(query)
        if storage:
            entities['volume_size_gb'] = str(storage)
            
        # Extract cloud provider
        cloud_provider = self._extract_pattern_match(query, self.cloud_provider_patterns)
        if cloud_provider:
            entities['cloud_provider'] = cloud_provider

        # Extract database engine
        db_engine = self._extract_pattern_match(query, self.db_engine_patterns)
        if db_engine:
            entities['database_engine'] = db_engine

        # Extract monitoring tool
        mon_tool = self._extract_pattern_match(query, self.monitoring_tool_patterns)
        if mon_tool:
            entities['monitoring_tool'] = mon_tool

        # Extract CICD tool
        cicd_tool = self._extract_pattern_match(query, self.cicd_tool_patterns)
        if cicd_tool:
            entities['cicd_tool'] = cicd_tool

        # Extract VPN protocol
        vpn_proto = self._extract_pattern_match(query, self.vpn_protocol_patterns)
        if vpn_proto:
            entities['vpn_protocol'] = vpn_proto

        # Extract OS
        os_name = self._extract_pattern_match(query, self.os_patterns)
        if os_name:
            entities['os'] = os_name

        # Extract numbers for node count, etc.
        numbers = self._extract_numbers(query)
        if numbers:
            # Assign numbers based on context
            if 'node' in query_lower and numbers:
                entities['node_count'] = str(numbers[0])

        logger.info(f"Extracted entities: {entities}")
        return entities

    def _extract_hostname(self, query: str) -> Optional[str]:
        """Extract hostname from query."""
        for pattern in self.hostname_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                hostname = match.group(1)
                # Validate hostname format
                if self._is_valid_hostname(hostname):
                    return hostname
        return None

    def _extract_app_name(self, query: str) -> Optional[str]:
        """Extract application name from query.""" 
        for pattern in self.app_name_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(1)
        return None

    def _extract_database_name(self, query: str) -> Optional[str]:
        """Extract database name from query."""
        for pattern in self.db_name_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(1)
        return None

    def _extract_database_user(self, query: str) -> Optional[str]:
        """Extract database user from query."""
        for pattern in self.db_user_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(1)
        return None

    def _extract_instance_type(self, query: str) -> Optional[str]:
        """Extract AWS instance type from query."""
        for pattern in self.instance_type_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(1).lower()
        return None

    def _extract_region(self, query: str) -> Optional[str]:  
        """Extract AWS region from query."""
        for pattern in self.region_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(1)
        return None

    def _extract_ports(self, query: str) -> Dict[str, Any]:
        """Extract port information from query."""
        ports = {}
        
        # Look for port mappings like 80:80
        port_mapping_match = re.search(r'\bports?\s+(\d{2,5}):(\d{2,5})\b', query, re.IGNORECASE)
        if port_mapping_match:
            ports['ports'] = f"{port_mapping_match.group(1)}:{port_mapping_match.group(2)}"
            ports['http_port'] = int(port_mapping_match.group(1))
            ports['app_port'] = int(port_mapping_match.group(2))
            return ports
            
        # Look for single port numbers
        port_matches = re.findall(r'\bport\s+(\d{2,5})\b', query, re.IGNORECASE)
        if port_matches:
            port = int(port_matches[-1])  # Take the last port mentioned
            if port == 80:
                ports['http_port'] = port
            elif port in [8000, 8080, 3000, 5000]:
                ports['app_port'] = port
            else:
                ports['port'] = port
                
        return ports

    def _extract_image(self, query: str) -> Optional[str]:
        """Extract Docker image name from query."""
        for pattern in self.image_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                if ':' in match.group(0):
                    return match.group(0)
                else:
                    return match.group(1)
        return None

    def _extract_version(self, query: str) -> Optional[str]:
        """Extract version number from query."""
        for pattern in self.version_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(1)
        return None

    def _extract_storage(self, query: str) -> Optional[int]:
        """Extract storage size in GB from query."""
        for pattern in self.storage_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue
        return None

    def _extract_numbers(self, query: str) -> List[int]:
        """Extract all numbers from query."""
        numbers = []
        for match in re.finditer(r'\b(\d+)\b', query):
            try:
                num = int(match.group(1))
                if num > 0:  # Only positive numbers
                    numbers.append(num)
            except ValueError:
                continue
        return numbers

    def _extract_pattern_match(self, query: str, patterns: list) -> Optional[str]:
        """Extract first match from a list of (pattern, value) tuples."""
        for pattern, value in patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return value
        return None

    def _is_valid_hostname(self, hostname: str) -> bool:
        """Validate hostname format."""
        if not hostname or len(hostname) > 253:
            return False
            
        # Must contain at least one dot
        if '.' not in hostname:
            return False
            
        # Check each label
        labels = hostname.split('.')
        for label in labels:
            if not label or len(label) > 63:
                return False
            if not re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?$', label):
                return False
                
        return True


# Global extractor instance
entity_extractor = EntityExtractor()


def extract_entities_from_query(query: str) -> Dict[str, Any]:
    """
    Convenience function to extract entities from a query.
    
    Args:
        query: User's natural language query
        
    Returns:
        Dict of extracted entities
    """
    return entity_extractor.extract_entities(query)


# Test function
if __name__ == "__main__":
    # Test cases
    test_queries = [
        "Deploy static website to nginx on docs.example.com, port 80",
        "Deploy FastAPI app billing-api, port 8000, http port 80", 
        "Create an EKS cluster, 3 nodes, m5.large, kubernetes 1.29 in us-east-1",
        "Deploy PostgreSQL database, version 16, name analytics_db, user admin",
        "Run a nginx Docker container, port 80:80",
        "Deploy EC2 instance t3.medium 50GB gp3 Ubuntu in us-west-2"
    ]
    
    extractor = EntityExtractor()
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        entities = extractor.extract_entities(query)
        print(f"Entities: {entities}")