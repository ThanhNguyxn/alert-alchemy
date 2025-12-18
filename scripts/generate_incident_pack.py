#!/usr/bin/env python3
"""Generate diverse incident YAML files for the web game.

Creates incidents with varied categories, severities, and realistic data.
Deterministic given a seed for reproducible builds.
"""

import argparse
import hashlib
import random
import sys
from pathlib import Path

# ═══════════════════════════════════════════════════════════════
# Incident Templates by Category
# ═══════════════════════════════════════════════════════════════

CATEGORIES = {
    "web-api": {
        "services": ["api-gateway", "auth-service", "user-service", "payment-api", "search-api", "notification-service"],
        "titles": [
            "API Gateway 5xx Surge",
            "Authentication Token Failures",
            "Rate Limiter Blocking Legit Traffic",
            "GraphQL Resolver Timeout",
            "REST Endpoint Memory Leak",
            "CORS Policy Breaking Mobile App",
            "API Versioning Mismatch",
            "Webhook Delivery Failures",
        ],
        "actions": ["rollback", "restart", "scale", "disable-flag", "clear-cache"],
    },
    "database": {
        "services": ["postgres-primary", "postgres-replica", "redis-cache", "elasticsearch", "mongodb-cluster"],
        "titles": [
            "Database Connection Pool Exhausted",
            "Slow Query Blocking Transactions",
            "Replication Lag Spike",
            "Index Corruption Detected",
            "Deadlock in Payment Table",
            "Redis Memory Fragmentation",
            "Elasticsearch Cluster Yellow",
            "MongoDB Shard Imbalance",
        ],
        "actions": ["increase-pool", "add-index", "restart", "scale", "clear-cache"],
    },
    "infrastructure": {
        "services": ["k8s-control-plane", "ingress-nginx", "cert-manager", "vault", "terraform-state"],
        "titles": [
            "Kubernetes Node NotReady",
            "Ingress Controller OOMKilled",
            "Certificate Expiry Imminent",
            "Vault Seal Event",
            "DNS Resolution Failures",
            "Load Balancer Health Check Flapping",
            "Container Image Pull Errors",
            "PersistentVolume Stuck Terminating",
        ],
        "actions": ["restart", "scale", "rollback", "disable-flag"],
    },
    "streaming": {
        "services": ["kafka-broker", "kafka-connect", "flink-jobs", "rabbitmq", "aws-kinesis"],
        "titles": [
            "Kafka Consumer Lag Explosion",
            "Message Queue Backpressure",
            "Stream Processing Job Crash Loop",
            "Dead Letter Queue Overflow",
            "Partition Rebalancing Storm",
            "Event Serialization Failures",
            "Kafka Connect Sink Errors",
            "RabbitMQ Memory Alarm",
        ],
        "actions": ["scale", "restart", "rollback", "clear-cache"],
    },
    "security": {
        "services": ["waf", "oauth-provider", "ldap-sync", "secrets-manager", "audit-log"],
        "titles": [
            "Credential Rotation Failure",
            "WAF False Positive Surge",
            "OAuth Token Revocation Storm",
            "LDAP Sync Hanging",
            "API Key Leaked in Logs",
            "Certificate Chain Invalid",
            "Session Fixation Detected",
            "Audit Log Pipeline Broken",
        ],
        "actions": ["disable-flag", "rollback", "restart", "clear-cache"],
    },
    "observability": {
        "services": ["prometheus", "grafana", "jaeger", "fluentd", "alertmanager"],
        "titles": [
            "Metrics Cardinality Explosion",
            "Log Pipeline Dropping Events",
            "Trace Sampling Rate Too Low",
            "Alert Storm Overwhelming On-Call",
            "Dashboard Query Timeout",
            "Prometheus TSDB Corruption",
            "Grafana Datasource Unreachable",
            "Log Shipper Memory Spike",
        ],
        "actions": ["restart", "scale", "rollback", "clear-cache"],
    },
}

SEVERITIES = ["critical", "high", "medium", "low"]
SEVERITY_WEIGHTS = [1, 2, 4, 3]  # Distribution

LOG_TEMPLATES = [
    "[{ts}] [ERROR] [{svc}] Connection refused: max retries exceeded",
    "[{ts}] [WARN] [{svc}] Response time 2340ms exceeds threshold 500ms",
    "[{ts}] [ERROR] [{svc}] Timeout waiting for upstream response",
    "[{ts}] [INFO] [{svc}] Circuit breaker OPEN for dependency {dep}",
    "[{ts}] [ERROR] [{svc}] OOM: container killed by kernel",
    "[{ts}] [WARN] [{svc}] Retry attempt 3/5 for request {req_id}",
    "[{ts}] [ERROR] [{svc}] SSL handshake failed: certificate expired",
    "[{ts}] [CRITICAL] [{svc}] Database connection pool exhausted",
    "[{ts}] [WARN] [{svc}] Request rate 1500/s approaching limit 2000/s",
    "[{ts}] [ERROR] [{svc}] JSON parse error: unexpected token at position 0",
    "[{ts}] [INFO] [{svc}] Health check failed, marking unhealthy",
    "[{ts}] [ERROR] [{svc}] Authentication failed: token expired",
]

TRACE_TEMPLATES = [
    "[{span}] {svc} → {dep}: {dur}ms (OK)",
    "[{span}] {svc} → {dep}: {dur}ms (TIMEOUT)",
    "[{span}] {svc} → {dep}: {dur}ms (ERROR: 503)",
    "[{span}] {svc} → database: {dur}ms (SLOW)",
    "[{span}] {svc} → cache: {dur}ms (MISS)",
]

DESCRIPTIONS = [
    "Users are reporting intermittent failures when accessing {feature}. Error rates have spiked in the last 15 minutes. Initial investigation suggests {cause}.",
    "Monitoring detected anomalous behavior in {svc}. Latency percentiles are elevated and {symptom}. This may be related to recent changes in {area}.",
    "Alert triggered for {metric} exceeding threshold. The {svc} is showing signs of degradation. Customer impact is currently {impact}.",
    "Incident escalated after automated remediation failed. The {svc} is experiencing {problem}. On-call engineer is investigating root cause.",
    "Production issue affecting {feature}. Multiple services reporting connectivity problems to {dep}. Blast radius is {radius}.",
]

ACTION_NOTES = {
    "rollback": "Revert to last known good deployment",
    "restart": "Restart affected pods/services",
    "scale": "Add more replicas to handle load",
    "disable-flag": "Turn off the feature flag causing issues",
    "increase-pool": "Raise connection pool limits",
    "add-index": "Add database index for slow query",
    "clear-cache": "Flush cached data that may be stale",
}


def generate_seed_rng(seed: str) -> random.Random:
    """Create deterministic RNG from seed string."""
    seed_int = int(hashlib.sha256(seed.encode()).hexdigest()[:16], 16)
    return random.Random(seed_int)


def generate_incident(rng: random.Random, index: int) -> dict:
    """Generate a single incident with realistic data."""
    category = rng.choice(list(CATEGORIES.keys()))
    cat_data = CATEGORIES[category]
    
    title = rng.choice(cat_data["titles"])
    severity = rng.choices(SEVERITIES, weights=SEVERITY_WEIGHTS)[0]
    services = rng.sample(cat_data["services"], min(rng.randint(2, 4), len(cat_data["services"])))
    
    # Generate ID
    inc_id = f"GEN-{index:03d}"
    
    # Description
    desc_template = rng.choice(DESCRIPTIONS)
    description = desc_template.format(
        feature="the checkout flow" if "payment" in title.lower() else "core functionality",
        cause="connection pool exhaustion" if "pool" in title.lower() else "increased traffic",
        svc=services[0],
        symptom="error rates climbing",
        area="the payment processing pipeline" if "payment" in title.lower() else "infrastructure",
        metric="error_rate" if rng.random() > 0.5 else "p95_latency",
        impact="moderate" if severity in ["medium", "low"] else "high",
        problem="cascading failures" if severity == "critical" else "degraded performance",
        dep=services[1] if len(services) > 1 else "database",
        radius="expanding" if severity in ["critical", "high"] else "contained",
    )
    
    # Metrics based on severity
    base_error = {"critical": 45, "high": 25, "medium": 12, "low": 5}[severity]
    base_latency = {"critical": 3500, "high": 2000, "medium": 800, "low": 300}[severity]
    
    metrics = {
        "error_rate": base_error + rng.randint(-5, 15),
        "p95_latency": base_latency + rng.randint(-200, 500),
        "cpu_usage": rng.randint(40, 95),
        "memory_usage": rng.randint(50, 90),
        "request_rate": rng.randint(500, 5000),
    }
    
    # Logs
    logs = []
    for i in range(rng.randint(6, 10)):
        log = rng.choice(LOG_TEMPLATES).format(
            ts=f"2024-01-15T10:{rng.randint(0,59):02d}:{rng.randint(0,59):02d}Z",
            svc=rng.choice(services),
            dep=services[1] if len(services) > 1 else "database",
            req_id=f"req-{rng.randint(1000,9999)}",
        )
        logs.append(log)
    
    # Traces
    traces = []
    for i in range(rng.randint(3, 6)):
        trace = rng.choice(TRACE_TEMPLATES).format(
            span=f"{rng.randint(1000,9999):04x}",
            svc=rng.choice(services),
            dep=services[1] if len(services) > 1 else "cache",
            dur=rng.randint(50, 3000),
        )
        traces.append(trace)
    
    # Actions
    actions = []
    available = cat_data["actions"][:]
    correct = rng.choice(available)
    rng.shuffle(available)
    for action in available[:4]:
        actions.append({
            "name": action,
            "note": ACTION_NOTES.get(action, "Take this action"),
        })
    
    return {
        "id": inc_id,
        "title": title,
        "severity": severity,
        "description": description,
        "category": category,
        "tags": [category, severity],
        "services": services,
        "metrics": metrics,
        "logs": logs,
        "traces": traces,
        "actions": actions,
        "available_actions": [a["name"] for a in actions],
        "correct_action": correct,
        "optimal_resolution_steps": [
            "Inspect the incident to gather clues",
            f"Apply {correct} to address root cause",
            "Monitor metrics for improvement",
        ],
    }


def write_yaml(incident: dict, output_path: Path) -> None:
    """Write incident dict as YAML file."""
    lines = []
    
    def add_field(key: str, value, indent: int = 0):
        prefix = "  " * indent
        if isinstance(value, str):
            if "\n" in value or len(value) > 80:
                lines.append(f"{prefix}{key}: |")
                for line in value.split("\n"):
                    lines.append(f"{prefix}  {line}")
            else:
                # Escape quotes
                escaped = value.replace('"', '\\"')
                lines.append(f'{prefix}{key}: "{escaped}"')
        elif isinstance(value, (int, float)):
            lines.append(f"{prefix}{key}: {value}")
        elif isinstance(value, list):
            if all(isinstance(x, str) for x in value):
                lines.append(f"{prefix}{key}:")
                for item in value:
                    escaped = item.replace('"', '\\"')
                    lines.append(f'{prefix}  - "{escaped}"')
            elif all(isinstance(x, dict) for x in value):
                lines.append(f"{prefix}{key}:")
                for item in value:
                    first = True
                    for k, v in item.items():
                        if first:
                            escaped = str(v).replace('"', '\\"')
                            lines.append(f'{prefix}  - {k}: "{escaped}"')
                            first = False
                        else:
                            escaped = str(v).replace('"', '\\"')
                            lines.append(f'{prefix}    {k}: "{escaped}"')
            else:
                lines.append(f"{prefix}{key}: {value}")
        elif isinstance(value, dict):
            lines.append(f"{prefix}{key}:")
            for k, v in value.items():
                add_field(k, v, indent + 1)
    
    for key in ["id", "title", "severity", "category", "description", "tags", "services", 
                "metrics", "logs", "traces", "actions", "available_actions", "correct_action",
                "optimal_resolution_steps"]:
        if key in incident:
            add_field(key, incident[key])
    
    output_path.write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Generate incident pack for web game")
    parser.add_argument("--seed", type=str, default="default-seed", help="Random seed for deterministic generation")
    parser.add_argument("--count", type=int, default=30, help="Number of incidents to generate")
    parser.add_argument("--output", type=str, default=None, help="Output directory (default: incidents/generated)")
    args = parser.parse_args()
    
    # Determine output directory
    if args.output:
        output_dir = Path(args.output)
    else:
        script_dir = Path(__file__).parent
        output_dir = script_dir.parent / "incidents" / "generated"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate incidents
    rng = generate_seed_rng(str(args.seed))
    
    for i in range(1, args.count + 1):
        incident = generate_incident(rng, i)
        
        # Create filename from id and title
        safe_title = incident["title"].lower().replace(" ", "-").replace("/", "-")[:30]
        filename = f"{incident['id']}-{safe_title}.yaml"
        filepath = output_dir / filename
        
        write_yaml(incident, filepath)
    
    print(f"[OK] Generated {args.count} incidents to {output_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
