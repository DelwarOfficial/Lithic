# Deployment Guide

This document covers production deployment strategies for Lithic CLI.

## Prerequisites

- Python 3.12+
- Git repository access
- Network access for LLM providers (if using)

## Installation Methods

### Standard Installation

```bash
pip install lithic-cli
```

### Development Installation

```bash
git clone https://github.com/DelwarOfficial/Lithic-CLI.git
cd Lithic-CLI
pip install -e .
```

### Using uv (Recommended for Development)

```bash
git clone https://github.com/DelwarOfficial/Lithic-CLI.git
cd Lithic-CLI
uv sync
uv run lithic --help
```

## Configuration

### Environment Variables

Set these environment variables for production:

```bash
# LLM Provider (optional - graph-only mode works without API keys)
export LITHIC_PROVIDER=anthropic  # or openai, ollama, openrouter
export ANTHROPIC_API_KEY=your_key_here
export OPENAI_API_KEY=your_key_here

# Graph Configuration
export LITHIC_GRAPH_DIR=/app/graphs  # Default: ./graphify-out
export LITHIC_PROJECT_ROOT=/app/project  # Default: current directory

# Response Configuration
export LITHIC_RESPONSE_MODE=concise  # concise, normal, caveman_full, review, commit

# Advanced Options
export LITHIC_TRACING_ENABLED=true  # Enable OpenTelemetry tracing
export REDIS_URL=redis://localhost:6379  # For distributed caching
```

### Configuration File

Optional `.env` file in project root:

```bash
LITHIC_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
LITHIC_RESPONSE_MODE=concise
LITHIC_GRAPH_DIR=./graphs
```

## Production Deployment Patterns

### 1. CLI-Only Deployment

Simple deployment for command-line usage:

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install lithic-cli
COPY . .
RUN lithic index .
CMD ["lithic", "ask", "What is this project?"]
```

### 2. Web Dashboard Deployment

Deploy with web interface:

```dockerfile
FROM python:3.12-slim
WORKDIR /app
RUN pip install lithic-cli[web,enterprise]
COPY . .
RUN lithic index .
EXPOSE 8000
CMD ["lithic", "web", "--host", "0.0.0.0", "--port", "8000"]
```

### 3. MCP Server Deployment

Deploy as Model Context Protocol server:

```dockerfile
FROM python:3.12-slim
WORKDIR /app
RUN pip install lithic-cli[mcp]
COPY . .
RUN lithic index .
CMD ["lithic", "mcp", "serve"]
```

## Kubernetes Deployment

### Basic Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: lithic-cli
spec:
  replicas: 1
  selector:
    matchLabels:
      app: lithic-cli
  template:
    metadata:
      labels:
        app: lithic-cli
    spec:
      containers:
      - name: lithic-cli
        image: lithic-cli:latest
        env:
        - name: LITHIC_PROVIDER
          value: "anthropic"
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: lithic-secrets
              key: anthropic-api-key
        ports:
        - containerPort: 8000
        volumeMounts:
        - name: project-data
          mountPath: /app/project
        - name: graph-cache
          mountPath: /app/graphs
      volumes:
      - name: project-data
        persistentVolumeClaim:
          claimName: project-pvc
      - name: graph-cache
        emptyDir: {}
```

### Service Definition

```yaml
apiVersion: v1
kind: Service
metadata:
  name: lithic-cli-service
spec:
  selector:
    app: lithic-cli
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

## Performance Optimization

### Graph Caching

- Pre-build graphs in container build phase
- Use persistent volumes for graph storage
- Configure Redis for distributed caching

### Memory Management

```bash
# Set memory limits for large projects
export LITHIC_MAX_GRAPH_SIZE=500MB
export LITHIC_COMPRESSION_CACHE_SIZE=1000
```

### Rate Limiting

```bash
# Configure API rate limits
export LITHIC_RATE_LIMIT=100  # requests per minute
export LITHIC_TIMEOUT=30      # seconds
```

## Monitoring

### Health Checks

```bash
# Basic health check
lithic stats

# Web dashboard health
curl http://localhost:8000/health

# MCP server health  
echo '{"jsonrpc":"2.0","method":"ping","id":1}' | lithic mcp serve
```

### Metrics Collection

Enable OpenTelemetry tracing:

```bash
export LITHIC_TRACING_ENABLED=true
export OTEL_EXPORTER_JAEGER_ENDPOINT=http://jaeger:14268/api/traces
```

### Logging

Configure structured logging:

```bash
export LITHIC_LOG_LEVEL=INFO
export LITHIC_LOG_FORMAT=json
```

## Security

### API Key Management

- Never commit API keys to version control
- Use environment variables or secret management systems
- Rotate keys regularly
- Use least-privilege API keys when available

### Network Security

- Run on private networks when possible
- Use HTTPS for web dashboard deployment
- Configure firewall rules for MCP server ports
- Enable authentication for production deployments

### File System Security

- Run with minimal file system permissions
- Use read-only containers when possible
- Restrict graph output directory permissions

## Troubleshooting

### Common Issues

**Graph build fails:**
```bash
# Check project structure
lithic index . --verbose

# Verify API keys
echo $ANTHROPIC_API_KEY | head -c 10
```

**Memory issues:**
```bash
# Reduce cache sizes
export LITHIC_COMPRESSION_CACHE_SIZE=100
export LITHIC_GRAPH_CACHE_SIZE=50MB
```

**Performance problems:**
```bash
# Enable performance monitoring
lithic stats --verbose

# Check graph size
du -sh graphify-out/
```

### Log Analysis

```bash
# Enable debug logging
export LITHIC_LOG_LEVEL=DEBUG

# Filter logs
lithic ask "test" 2>&1 | grep ERROR
```

## Backup and Recovery

### Graph Backup

```bash
# Backup graph data
tar -czf graph-backup.tar.gz graphify-out/

# Restore graph data
tar -xzf graph-backup.tar.gz
```

### Configuration Backup

```bash
# Export environment configuration
env | grep LITHIC > lithic.env

# Restore configuration
source lithic.env
```

## Scaling

### Horizontal Scaling

- Deploy multiple instances behind load balancer
- Use shared Redis cache for consistency
- Separate read and write operations

### Vertical Scaling

- Increase memory for larger projects
- Use faster storage for graph data
- Optimize CPU allocation for compression

## Support

For deployment issues:

1. Check the [GitHub Issues](https://github.com/DelwarOfficial/Lithic-CLI/issues)
2. Review logs with debug level enabled
3. Verify environment configuration
4. Test with minimal configuration first

## Security Considerations

This is development-stage software. For production use:

- Conduct security review of dependencies
- Implement proper authentication and authorization
- Use network isolation and monitoring
- Follow your organization's security policies
- Consider the software's current maturity level

## Version Compatibility

- Python 3.12+ required
- Compatible with major LLM providers
- Graph format is stable across minor versions
- Breaking changes documented in release notes