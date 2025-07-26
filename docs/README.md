# AI PKM Tool Documentation

Welcome to the comprehensive documentation for the AI Personal Knowledge Management Tool. This documentation covers everything from initial setup to advanced deployment and troubleshooting.

## Quick Start

New to the AI PKM Tool? Start here:

1. **[Installation Guide](installation-guide.md)** - Get up and running quickly
2. **[Environment Variables](environment-variables.md)** - Configure your installation
3. **[Health Endpoints](health-endpoints.md)** - Verify everything is working

## Documentation Structure

### 📦 Setup and Installation

- **[Installation Guide](installation-guide.md)**
  - Automated setup scripts
  - Manual installation steps
  - GPU acceleration setup
  - Verification and testing

- **[Environment Variables](environment-variables.md)**
  - Complete configuration reference
  - AI model configuration
  - Database and storage settings
  - Performance tuning options

### 🚀 Deployment

- **[Deployment Guide](deployment-guide.md)**
  - Local development deployment
  - Docker Compose setup
  - Cloud deployment (AWS, GCP, Azure)
  - Kubernetes orchestration
  - Load balancing and high availability

### 🔧 Operations and Maintenance

- **[Health Endpoints](health-endpoints.md)**
  - Service monitoring endpoints
  - Integration with monitoring systems
  - Automated health checks
  - Performance metrics

- **[Troubleshooting Guide](troubleshooting-guide.md)**
  - Common issues and solutions
  - Diagnostic procedures
  - Performance optimization
  - Recovery procedures

### 💻 Development

- **[Development Guide](development.md)**
  - Development environment setup
  - Code structure and patterns
  - Testing procedures
  - Contributing guidelines

- **[Implementation Status](implementation-status.md)**
  - Current feature status
  - Roadmap and planned features
  - Known limitations

### 📋 Features

- **[PDF Viewer Guide](pdf-viewer.md)**
  - PDF viewing capabilities
  - Annotation features
  - Search and navigation

## Getting Started Workflows

### For New Users

1. **Quick Setup**: Follow the [Installation Guide](installation-guide.md) automated setup
2. **Configuration**: Review [Environment Variables](environment-variables.md) for your needs
3. **Verification**: Use [Health Endpoints](health-endpoints.md) to confirm everything works
4. **First Use**: Upload a document and explore the features

### For Developers

1. **Development Setup**: Follow the development section in [Installation Guide](installation-guide.md)
2. **Code Overview**: Read the [Development Guide](development.md)
3. **Feature Status**: Check [Implementation Status](implementation-status.md)
4. **Testing**: Set up health monitoring with [Health Endpoints](health-endpoints.md)

### For System Administrators

1. **Production Deployment**: Follow [Deployment Guide](deployment-guide.md)
2. **Configuration Management**: Master [Environment Variables](environment-variables.md)
3. **Monitoring Setup**: Implement [Health Endpoints](health-endpoints.md) monitoring
4. **Troubleshooting**: Familiarize yourself with [Troubleshooting Guide](troubleshooting-guide.md)

## Key Features Covered

### AI-Powered Document Processing
- **Multimodal Support**: PDF, images, audio, video processing with RAG-Anything and MinerU 2.0
- **Knowledge Graphs**: LightRAG-powered relationship discovery
- **Semantic Search**: Advanced AI-powered search capabilities
- **OpenAI Integration**: Configurable AI models for various tasks

### System Architecture
- **Microservices Design**: FastAPI backend with React frontend
- **Background Processing**: Celery + Redis for async document processing
- **Vector Storage**: ChromaDB for semantic search
- **Flexible Deployment**: Docker, Kubernetes, cloud-native options

### Monitoring and Operations
- **Health Monitoring**: Comprehensive service health checks
- **Performance Metrics**: Response time and resource monitoring
- **Error Handling**: Graceful degradation and recovery
- **Logging**: Structured logging for debugging and monitoring

## Support and Community

### Getting Help

1. **Check Documentation**: Most questions are answered in these guides
2. **Health Checks**: Use the health endpoints to diagnose issues
3. **Troubleshooting**: Follow the systematic troubleshooting guide
4. **Logs**: Check application logs for detailed error information

### Contributing

- Read the [Development Guide](development.md) for contribution guidelines
- Check [Implementation Status](implementation-status.md) for areas needing work
- Follow the setup procedures for development environment

### Reporting Issues

When reporting issues, please include:

1. **System Information**: OS, Python version, deployment method
2. **Configuration**: Relevant environment variables (redact sensitive data)
3. **Health Check Results**: Output from health endpoints
4. **Logs**: Relevant log entries
5. **Steps to Reproduce**: Clear reproduction steps

## Documentation Maintenance

This documentation is actively maintained and updated with each release. Key principles:

- **Accuracy**: All procedures are tested and verified
- **Completeness**: Covers all major use cases and configurations
- **Clarity**: Written for users of all technical levels
- **Currency**: Updated with new features and changes

### Version Information

- **Documentation Version**: Matches application version
- **Last Updated**: Check individual file timestamps
- **Compatibility**: Covers all supported deployment methods

## Quick Reference

### Essential Commands

```bash
# Quick setup
python scripts/install-deps.py && python setup.py && python scripts/start-dev.py

# Health check
curl http://localhost:8000/api/v1/health/comprehensive

# Docker deployment
python scripts/start-docker.py --mode prod --build

# Stop services
python scripts/stop-dev.py
```

### Key URLs

- **Application**: http://localhost:3000 (frontend)
- **API**: http://localhost:8000 (backend)
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/v1/health/comprehensive

### Important Files

- **Configuration**: `.env` (environment variables)
- **Docker**: `docker-compose.yml`, `docker-compose.dev.yml`
- **Scripts**: `scripts/` directory for automation
- **Data**: `data/` directory for storage

This documentation provides everything you need to successfully deploy, operate, and develop with the AI PKM Tool. Start with the appropriate guide for your use case and refer back to other sections as needed.