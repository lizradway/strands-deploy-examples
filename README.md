# Strands Deploy Examples

This repository contains example code and documentation for deploying Strands Agents to third-party container services.

## Overview

Strands Agents can be deployed to various cloud platforms using containerization. This repository provides ready-to-use examples for different deployment targets and programming languages.

## Available Examples

### Google Cloud Run

Deploy Strands Agents to Google Cloud Run with the following language implementations:

- **Python** (`/cloudrun/python/`) - Python-based Strands Agent with FastAPI
- **TypeScript** (`/cloudrun/typescript/`) - Node.js/TypeScript implementation

## Quick Start

1. Choose your preferred language implementation
2. Navigate to the corresponding directory
3. Follow the deployment instructions in each example
4. Configure your Strands Agent credentials and settings

## Prerequisites

- Docker installed locally
- Access to your chosen cloud platform (Google Cloud, etc.)
- Strands Agent installed + configured 

## Project Structure

```
strands-deploy-examples/
├── cloudrun/
│   ├── python/          # Python implementation
│   │   ├── agent.py     # Main agent code
│   │   ├── Dockerfile   # Container configuration
│   │   └── requirements.txt
│   └── typescript/      # TypeScript implementation
│       ├── index.ts     # Main agent code
│       ├── Dockerfile   # Container configuration
│       └── package.json
└── README.md
```

## Contributing

This is an unofficial repository. Feel free to submit issues and enhancement requests.
