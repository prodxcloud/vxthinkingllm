"""
VaLLM API Routes v2 - Advanced NLP with spaCy and Document Extraction

Features:
- spaCy NLP for entity extraction (services, regions, errors, configs)
- PDF/Document upload and text extraction
- Cloud/DevOps specific entity recognition
- Infrastructure diagram analysis (text-based)

USAGE:
======
    POST /api/model/v2/query     - NLP-enhanced query with entity extraction
    POST /api/model/v2/upload    - Upload documents for analysis
    POST /api/model/v2/extract   - Extract cloud entities from text
"""

import io
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request, File, UploadFile, Form
from pydantic import BaseModel

# Try to import spaCy
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

# Try to import PDF extraction
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# Try to import image processing
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# Try to import OCR for text extraction from images
try:
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False


router = APIRouter()

# =============================================================================
# CLOUD/DEVOPS ENTITY PATTERNS
# =============================================================================

CLOUD_PATTERNS = {
    "aws_services": [
        "ec2", "s3", "lambda", "rds", "eks", "ecs", "fargate", "cloudwatch",
        "cloudfront", "route53", "vpc", "iam", "dynamodb", "sqs", "sns",
        "api gateway", "elasticache", "aurora", "redshift", "kinesis",
        "athena", "glue", "emr", "sagemaker", "ecr", "secrets manager"
    ],
    "azure_services": [
        "aks", "azure functions", "cosmos db", "blob storage", "azure sql",
        "azure monitor", "azure devops", "azure ad", "key vault", "app service"
    ],
    "gcp_services": [
        "gke", "cloud run", "bigquery", "cloud storage", "cloud functions",
        "pub/sub", "cloud sql", "firestore", "vertex ai", "gcr"
    ],
    "kubernetes": [
        "pod", "deployment", "service", "ingress", "configmap", "secret",
        "namespace", "node", "cluster", "helm", "kubectl", "statefulset",
        "daemonset", "replicaset", "pvc", "pv", "hpa", "vpa"
    ],
    "docker": [
        "container", "image", "dockerfile", "docker-compose", "registry",
        "volume", "network", "swarm", "docker hub", "buildx"
    ],
    "devops_tools": [
        "terraform", "ansible", "jenkins", "github actions", "gitlab ci",
        "argocd", "flux", "prometheus", "grafana", "datadog", "splunk",
        "elasticsearch", "fluentd", "jaeger", "istio", "envoy", "nginx"
    ],
    "web_frameworks": [
        "fastapi", "flask", "django", "express", "spring boot", "rails",
        "uvicorn", "gunicorn", "next.js", "nest.js", "gin", "fiber"
    ],
    "security_issues": [
        "stack trace", "debug mode", "xss", "csrf", "sql injection", "ssrf",
        "authentication", "authorization", "jwt", "oauth", "cors", "secrets",
        "credentials", "password", "api key", "token", "vulnerability", "cve"
    ],
    "error_types": [
        "timeout", "connection refused", "out of memory", "oom", "crash",
        "failed", "error", "exception", "denied", "unauthorized", "forbidden",
        "rate limit", "throttle", "latency", "slow", "high cpu", "high memory"
    ],
    "regions": [
        "us-east-1", "us-west-2", "eu-west-1", "eu-central-1", "ap-southeast-1",
        "ap-northeast-1", "sa-east-1", "ca-central-1", "ap-south-1"
    ]
}


# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class QueryV2Request(BaseModel):
    """V2 Query with NLP enhancement"""
    query: str
    extract_entities: bool = True
    include_recommendations: bool = True
    top_k: int = 5


class EntityExtractionRequest(BaseModel):
    """Extract cloud entities from text"""
    text: str
    entity_types: Optional[List[str]] = None  # Filter specific types


class ExtractedEntity(BaseModel):
    """Extracted entity"""
    text: str
    label: str
    category: str
    confidence: float


class DocumentAnalysis(BaseModel):
    """Document analysis result"""
    filename: str
    content_preview: str
    word_count: int
    entities: List[ExtractedEntity]
    cloud_services: List[str]
    recommendations: List[str]


# =============================================================================
# NLP ENTITY EXTRACTOR
# =============================================================================

class CloudEntityExtractor:
    """Extract cloud/DevOps entities using pattern matching and spaCy"""
    
    def __init__(self):
        self.nlp = None
        if SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                # Model not downloaded
                pass
    
    def extract_pattern_entities(self, text: str) -> List[ExtractedEntity]:
        """Extract entities using regex patterns"""
        entities = []
        text_lower = text.lower()
        
        for category, patterns in CLOUD_PATTERNS.items():
            for pattern in patterns:
                if pattern.lower() in text_lower:
                    entities.append(ExtractedEntity(
                        text=pattern,
                        label=pattern.upper().replace(" ", "_"),
                        category=category,
                        confidence=0.9
                    ))
        
        # Extract IP addresses
        ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        for match in re.finditer(ip_pattern, text):
            entities.append(ExtractedEntity(
                text=match.group(),
                label="IP_ADDRESS",
                category="network",
                confidence=0.95
            ))
        
        # Extract ports
        port_pattern = r':(\d{2,5})\b'
        for match in re.finditer(port_pattern, text):
            entities.append(ExtractedEntity(
                text=f":{match.group(1)}",
                label="PORT",
                category="network",
                confidence=0.85
            ))
        
        # Extract instance IDs (AWS style)
        instance_pattern = r'\bi-[a-f0-9]{8,17}\b'
        for match in re.finditer(instance_pattern, text, re.IGNORECASE):
            entities.append(ExtractedEntity(
                text=match.group(),
                label="EC2_INSTANCE",
                category="aws_services",
                confidence=0.95
            ))
        
        # Extract ARNs
        arn_pattern = r'arn:aws:[a-z0-9-]+:[a-z0-9-]*:\d*:[a-zA-Z0-9-_/:]+'
        for match in re.finditer(arn_pattern, text):
            entities.append(ExtractedEntity(
                text=match.group(),
                label="AWS_ARN",
                category="aws_services",
                confidence=0.98
            ))
        
        return entities
    
    def extract_spacy_entities(self, text: str) -> List[ExtractedEntity]:
        """Extract entities using spaCy NLP"""
        entities = []
        
        if self.nlp is None:
            return entities
        
        doc = self.nlp(text)
        
        for ent in doc.ents:
            # Map spaCy labels to our categories
            category = "general"
            if ent.label_ in ["ORG", "PRODUCT"]:
                category = "organization"
            elif ent.label_ in ["GPE", "LOC"]:
                category = "location"
            elif ent.label_ in ["DATE", "TIME"]:
                category = "temporal"
            elif ent.label_ == "CARDINAL":
                category = "numeric"
            
            entities.append(ExtractedEntity(
                text=ent.text,
                label=ent.label_,
                category=category,
                confidence=0.8
            ))
        
        return entities
    
    def extract_all(self, text: str) -> List[ExtractedEntity]:
        """Extract all entities from text"""
        entities = []
        
        # Pattern-based extraction (always works)
        entities.extend(self.extract_pattern_entities(text))
        
        # spaCy extraction (if available)
        entities.extend(self.extract_spacy_entities(text))
        
        # Remove duplicates
        seen = set()
        unique_entities = []
        for e in entities:
            key = (e.text.lower(), e.category)
            if key not in seen:
                seen.add(key)
                unique_entities.append(e)
        
        return unique_entities


# Global extractor instance
entity_extractor = CloudEntityExtractor()


# =============================================================================
# DOCUMENT PROCESSOR
# =============================================================================

def extract_text_from_pdf(file_content: bytes) -> str:
    """Extract text from PDF file"""
    if not PDF_AVAILABLE:
        return "[PDF extraction not available - install PyPDF2]"
    
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
        text_parts = []
        for page in pdf_reader.pages:
            text_parts.append(page.extract_text())
        return "\n".join(text_parts)
    except Exception as e:
        return f"[Error extracting PDF: {e}]"


def extract_text_from_image(file_content: bytes) -> tuple:
    """
    Extract text from image using OCR and analyze image properties.
    Returns: (extracted_text, image_info)
    """
    image_info = {
        "width": 0,
        "height": 0,
        "format": None,
        "mode": None,
        "has_text": False
    }
    
    if not PIL_AVAILABLE:
        return "[Image processing not available - install Pillow: pip install Pillow]", image_info
    
    try:
        img = Image.open(io.BytesIO(file_content))
        image_info = {
            "width": img.width,
            "height": img.height,
            "format": img.format,
            "mode": img.mode,
            "has_text": False
        }
        
        # Try OCR if available
        if OCR_AVAILABLE:
            try:
                text = pytesseract.image_to_string(img)
                if text.strip():
                    image_info["has_text"] = True
                    return text, image_info
            except Exception:
                pass
        
        # If no OCR, try to describe what we can detect
        description = f"[Image: {img.width}x{img.height} {img.format or 'unknown'} format]"
        
        # Analyze image for common diagram patterns
        if img.mode == "RGB" or img.mode == "RGBA":
            description += "\n[Tip: Install pytesseract for OCR text extraction from diagrams]"
        
        return description, image_info
        
    except Exception as e:
        return f"[Error processing image: {e}]", image_info


def analyze_architecture_diagram(text: str, image_info: dict) -> dict:
    """Analyze extracted text for architecture/infrastructure patterns"""
    analysis = {
        "diagram_type": "unknown",
        "detected_services": [],
        "detected_connections": [],
        "infrastructure_patterns": []
    }
    
    text_lower = text.lower()
    
    # Detect diagram type
    if any(x in text_lower for x in ["aws", "amazon", "ec2", "s3", "lambda"]):
        analysis["diagram_type"] = "AWS Architecture"
    elif any(x in text_lower for x in ["azure", "microsoft", "aks", "blob"]):
        analysis["diagram_type"] = "Azure Architecture"
    elif any(x in text_lower for x in ["gcp", "google cloud", "gke", "bigquery"]):
        analysis["diagram_type"] = "GCP Architecture"
    elif any(x in text_lower for x in ["kubernetes", "k8s", "pod", "deployment", "service"]):
        analysis["diagram_type"] = "Kubernetes Architecture"
    elif any(x in text_lower for x in ["docker", "container", "dockerfile"]):
        analysis["diagram_type"] = "Container Architecture"
    elif any(x in text_lower for x in ["vpc", "subnet", "firewall", "load balancer"]):
        analysis["diagram_type"] = "Network Architecture"
    elif any(x in text_lower for x in ["ci/cd", "pipeline", "jenkins", "github actions"]):
        analysis["diagram_type"] = "CI/CD Pipeline"
    
    # Detect services from text
    for category, services in CLOUD_PATTERNS.items():
        for service in services:
            if service.lower() in text_lower:
                analysis["detected_services"].append({
                    "name": service,
                    "category": category
                })
    
    # Detect connection patterns
    connection_patterns = [
        (r"->|→|-->", "directional flow"),
        (r"<->|↔|<-->", "bidirectional"),
        (r"api|rest|grpc|http", "API connection"),
        (r"database|db|rds|sql", "database connection"),
        (r"queue|sqs|kafka|pubsub", "message queue"),
        (r"cache|redis|memcached", "caching layer"),
    ]
    
    for pattern, conn_type in connection_patterns:
        if re.search(pattern, text_lower):
            analysis["detected_connections"].append(conn_type)
    
    # Detect infrastructure patterns
    if "load balancer" in text_lower or "alb" in text_lower or "nlb" in text_lower:
        analysis["infrastructure_patterns"].append("Load Balanced")
    if "auto scaling" in text_lower or "hpa" in text_lower:
        analysis["infrastructure_patterns"].append("Auto-Scaling")
    if "multi-az" in text_lower or "high availability" in text_lower:
        analysis["infrastructure_patterns"].append("High Availability")
    if "vpc" in text_lower and "subnet" in text_lower:
        analysis["infrastructure_patterns"].append("VPC Network Isolation")
    if "cdn" in text_lower or "cloudfront" in text_lower:
        analysis["infrastructure_patterns"].append("CDN Distribution")
    
    return analysis


def extract_text_from_file(filename: str, content: bytes) -> tuple:
    """
    Extract text from various file types.
    Returns: (text, file_info)
    """
    ext = Path(filename).suffix.lower()
    file_info = {"type": ext, "is_image": False, "image_info": None}
    
    # Image files
    if ext in [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp"]:
        file_info["is_image"] = True
        text, image_info = extract_text_from_image(content)
        file_info["image_info"] = image_info
        return text, file_info
    
    # PDF files
    if ext == ".pdf":
        return extract_text_from_pdf(content), file_info
    
    # Text-based files
    if ext in [".txt", ".md", ".yaml", ".yml", ".json", ".tf", ".py", ".sh", ".csv", 
               ".xml", ".html", ".hcl", ".toml", ".ini", ".conf", ".log"]:
        return content.decode("utf-8", errors="ignore"), file_info
    
    return f"[Unsupported file type: {ext}]", file_info


def generate_recommendations_from_entities(entities: List[ExtractedEntity]) -> List[str]:
    """Generate recommendations based on extracted entities"""
    recommendations = []
    
    categories = set(e.category for e in entities)
    labels = set(e.label.lower() for e in entities)
    
    # Security recommendations
    if "error_types" in categories:
        if any(x in labels for x in ["timeout", "connection_refused"]):
            recommendations.append("Consider implementing circuit breakers and retry logic for network calls")
        if any(x in labels for x in ["oom", "out_of_memory"]):
            recommendations.append("Review memory limits and implement proper resource requests in Kubernetes")
        if any(x in labels for x in ["unauthorized", "forbidden", "denied"]):
            recommendations.append("Audit IAM policies and RBAC configurations for proper access control")
    
    # Kubernetes recommendations
    if "kubernetes" in categories:
        recommendations.append("Ensure HPA/VPA is configured for auto-scaling workloads")
        recommendations.append("Implement pod disruption budgets for high availability")
    
    # Docker recommendations
    if "docker" in categories:
        recommendations.append("Use multi-stage builds to reduce image size")
        recommendations.append("Enable image vulnerability scanning in your container registry")
    
    # AWS recommendations
    if "aws_services" in categories:
        recommendations.append("Enable CloudWatch alarms for critical metrics")
        recommendations.append("Consider using AWS Cost Explorer to identify optimization opportunities")
    
    # DevOps tools
    if "devops_tools" in categories:
        if "prometheus" in labels or "grafana" in labels:
            recommendations.append("Define SLOs and set up alerting based on error budgets")
        if "terraform" in labels:
            recommendations.append("Use Terraform workspaces for environment separation")
    
    # Web frameworks
    if "web_frameworks" in categories:
        if "fastapi" in labels or "uvicorn" in labels:
            recommendations.append("Set debug=False in production and configure proper exception handlers")
            recommendations.append("Use structured logging with correlation IDs for tracing")
        if "django" in labels or "flask" in labels:
            recommendations.append("Ensure DEBUG=False and configure proper security middleware")
    
    # Security issues
    if "security_issues" in categories:
        if any(x in labels for x in ["stack_trace", "debug_mode"]):
            recommendations.append("Disable debug mode in production to prevent information disclosure")
        if any(x in labels for x in ["xss", "csrf"]):
            recommendations.append("Implement proper security headers and CSRF protection")
        if any(x in labels for x in ["credentials", "password", "api_key", "secrets"]):
            recommendations.append("Use a secrets manager (AWS Secrets Manager, HashiCorp Vault) for sensitive data")
    
    return recommendations[:5]  # Limit to 5


# =============================================================================
# API ENDPOINTS
# =============================================================================

@router.post("/query")
async def query_v2(
    request: QueryV2Request,
    req: Request
):
    """
    V2 Query endpoint with NLP entity extraction
    
    Features:
    - Extracts cloud/DevOps entities from query
    - Provides context-aware recommendations
    - Enhanced search with entity filtering
    """
    try:
        vector_store = req.app.state.vector_store
        reasoning_engine = req.app.state.reasoning_engine
        
        if not vector_store:
            raise HTTPException(status_code=503, detail="Vector store not initialized")
        
        # Extract entities from query
        entities = []
        if request.extract_entities:
            entities = entity_extractor.extract_all(request.query)
        
        # Perform vector search
        search_results = await vector_store.search(
            query=request.query,
            top_k=request.top_k
        )
        
        # Perform reasoning
        reasoning_result = None
        if reasoning_engine:
            reasoning_result = await reasoning_engine.reason(
                query=request.query,
                max_steps=5
            )
        
        # Generate recommendations based on entities
        recommendations = []
        if request.include_recommendations:
            recommendations = generate_recommendations_from_entities(entities)
        
        # Build a more useful response that includes the actual recommendation content
        response_text = ""
        if search_results:
            top_result = search_results[0]
            doc_text = top_result.get('document', '')
            score = top_result.get('score', 0)
            
            # Parse the recommendation from the document text
            response_text = f"📋 Found matching recommendation (score: {score:.2f}):\n\n"
            response_text += doc_text
            
            if len(search_results) > 1:
                response_text += f"\n\n📚 Also found {len(search_results) - 1} related recommendations."
        else:
            response_text = reasoning_result['final_answer'] if reasoning_result else "No matching recommendations found."
        
        return {
            "query": request.query,
            "response": response_text,
            "entities": [e.dict() for e in entities],
            "entity_summary": {
                "total": len(entities),
                "by_category": {
                    cat: len([e for e in entities if e.category == cat])
                    for cat in set(e.category for e in entities)
                }
            },
            "context": [
                {
                    "document": r['document'],
                    "score": r['score'],
                    "metadata": r.get('metadata', {})
                }
                for r in search_results
            ],
            "recommendations": recommendations,
            "nlp_info": {
                "spacy_available": SPACY_AVAILABLE,
                "spacy_model": "en_core_web_sm" if entity_extractor.nlp else None
            },
            "model": "vallm-v2-nlp",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


@router.post("/extract")
async def extract_entities(request: EntityExtractionRequest):
    """
    Extract cloud/DevOps entities from text
    
    Recognizes:
    - AWS/Azure/GCP services
    - Kubernetes resources
    - Docker components
    - DevOps tools
    - Error types
    - IP addresses, ports, instance IDs
    """
    try:
        entities = entity_extractor.extract_all(request.text)
        
        # Filter by types if specified
        if request.entity_types:
            entities = [e for e in entities if e.category in request.entity_types]
        
        return {
            "text_preview": request.text[:200] + "..." if len(request.text) > 200 else request.text,
            "entities": [e.dict() for e in entities],
            "summary": {
                "total_entities": len(entities),
                "categories": list(set(e.category for e in entities)),
                "cloud_services": [e.text for e in entities if "services" in e.category],
                "errors_detected": [e.text for e in entities if e.category == "error_types"]
            },
            "nlp_info": {
                "spacy_available": SPACY_AVAILABLE,
                "pattern_matching": True
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting entities: {str(e)}")


@router.post("/upload")
async def upload_document(
    req: Request,
    file: UploadFile = File(...),
    analyze: bool = Form(default=True)
):
    """
    Upload and analyze cloud/DevOps documents and images
    
    Supported formats:
    - Images (.png, .jpg, .jpeg, .gif, .bmp, .webp) - Architecture diagrams
    - PDF (.pdf) - Documentation
    - Text (.txt, .md) - Readme, notes
    - Config files (.yaml, .yml, .json, .tf, .hcl) - Infrastructure as Code
    - Scripts (.py, .sh) - Automation scripts
    - Logs (.log, .csv) - Log files
    """
    try:
        # Read file content
        content = await file.read()
        
        # Extract text and file info
        text, file_info = extract_text_from_file(file.filename, content)
        
        if not analyze:
            return {
                "filename": file.filename,
                "size_bytes": len(content),
                "file_info": file_info,
                "extracted_text": text[:2000] + "..." if len(text) > 2000 else text
            }
        
        # For images, do architecture analysis
        diagram_analysis = None
        if file_info.get("is_image"):
            diagram_analysis = analyze_architecture_diagram(text, file_info.get("image_info", {}))
        
        # Extract entities
        entities = entity_extractor.extract_all(text)
        
        # Get cloud services mentioned
        cloud_services = list(set(
            e.text for e in entities 
            if "services" in e.category
        ))
        
        # Add services from diagram analysis
        if diagram_analysis:
            for svc in diagram_analysis.get("detected_services", []):
                if svc["name"] not in cloud_services:
                    cloud_services.append(svc["name"])
        
        # Generate recommendations
        recommendations = generate_recommendations_from_entities(entities)
        
        # Add diagram-specific recommendations
        if diagram_analysis:
            if diagram_analysis.get("diagram_type") == "Kubernetes Architecture":
                recommendations.append("Consider implementing NetworkPolicies for pod-to-pod security")
            if "High Availability" not in diagram_analysis.get("infrastructure_patterns", []):
                recommendations.append("Consider adding multi-AZ deployment for high availability")
            if "CDN Distribution" not in diagram_analysis.get("infrastructure_patterns", []):
                recommendations.append("Consider using a CDN for static content delivery")
        
        # Search for related content in vector store
        vector_store = req.app.state.vector_store
        related_docs = []
        if vector_store and cloud_services:
            search_query = " ".join(cloud_services[:5])
            search_results = await vector_store.search(query=search_query, top_k=3)
            related_docs = [r['document'][:200] for r in search_results]
        
        response = {
            "filename": file.filename,
            "file_type": Path(file.filename).suffix,
            "size_bytes": len(content),
            "is_image": file_info.get("is_image", False),
            "word_count": len(text.split()),
            "content_preview": text[:500] + "..." if len(text) > 500 else text,
            "analysis": {
                "entities": [e.dict() for e in entities[:20]],
                "entity_count": len(entities),
                "cloud_services": cloud_services,
                "error_indicators": [e.text for e in entities if e.category == "error_types"]
            },
            "recommendations": recommendations[:5],
            "related_documents": related_docs,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Add image-specific info
        if file_info.get("is_image"):
            response["image_analysis"] = {
                "dimensions": f"{file_info['image_info']['width']}x{file_info['image_info']['height']}" if file_info.get("image_info") else "unknown",
                "format": file_info['image_info'].get('format') if file_info.get("image_info") else "unknown",
                "ocr_available": OCR_AVAILABLE,
                "text_detected": file_info['image_info'].get('has_text', False) if file_info.get("image_info") else False,
                "diagram_analysis": diagram_analysis
            }
        
        return response
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")


@router.get("/status")
async def nlp_status():
    """Check NLP system status and capabilities"""
    return {
        "status": "online",
        "capabilities": {
            "spacy_nlp": {
                "available": SPACY_AVAILABLE,
                "model_loaded": entity_extractor.nlp is not None,
                "install": "pip install spacy && python -m spacy download en_core_web_sm"
            },
            "pdf_extraction": {
                "available": PDF_AVAILABLE,
                "install": "pip install PyPDF2"
            },
            "image_processing": {
                "available": PIL_AVAILABLE,
                "install": "pip install Pillow"
            },
            "ocr_text_extraction": {
                "available": OCR_AVAILABLE,
                "install": "pip install pytesseract (requires Tesseract OCR installed)"
            },
            "pattern_matching": {
                "available": True,
                "install": "Built-in (no installation needed)"
            }
        },
        "supported_file_types": {
            "images": [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".tiff"],
            "documents": [".pdf", ".txt", ".md"],
            "config": [".yaml", ".yml", ".json", ".tf", ".hcl", ".toml", ".ini"],
            "code": [".py", ".sh", ".js", ".ts"],
            "logs": [".log", ".csv"]
        },
        "entity_categories": list(CLOUD_PATTERNS.keys()),
        "entity_patterns_count": {
            cat: len(patterns) for cat, patterns in CLOUD_PATTERNS.items()
        },
        "total_patterns": sum(len(p) for p in CLOUD_PATTERNS.values())
    }

