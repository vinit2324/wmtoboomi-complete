# webMethods to Boomi Migration Accelerator

Enterprise platform for automating 80-90% of webMethods to Boomi migrations.

**Built for Jade Global Inc.**

![Jade Global](./frontend/public/jade-logo1.png)

## Overview

This platform automates the conversion of webMethods integration packages to Boomi components, significantly reducing migration effort and time.

### Key Features

- **Multi-Customer Management** - Manage multiple customer accounts with encrypted credentials
- **Package Parsing** - Parse webMethods packages (manifest.v3, node.ndf, flow.xml)
- **Flow Verb Analysis** - Identify all 9 webMethods flow verbs (MAP, BRANCH, LOOP, etc.)
- **wMPublic Service Tracking** - Track and convert wMPublic service invocations
- **Automated Conversion** - Convert to valid Boomi XML components
- **Boomi API Integration** - Push components directly to Boomi
- **AI Assistant** - Get help with migration questions using LLM
- **Analysis Dashboard** - Visualize complexity and dependencies

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- MongoDB Atlas account (connection string provided)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn app.main:app --host localhost --port 7201 --reload
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

### Access the Application

- **Frontend**: http://localhost:7200
- **Backend API**: http://localhost:7201
- **API Documentation**: http://localhost:7201/docs

## Configuration

### Backend (.env)

```bash
BACKEND_PORT=7201
BACKEND_HOST=localhost
MONGODB_URL=mongodb+srv://vinit:Delhi123@vvmdb1.6umwxkw.mongodb.net/wmtoboomi?retryWrites=true&w=majority&appName=VVMDB1
ENCRYPTION_KEY=your-generated-fernet-key
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE=524288000
CORS_ORIGINS=http://localhost:7200,http://127.0.0.1:7200
```

### Frontend (.env)

```bash
VITE_API_URL=http://localhost:7201
VITE_APP_NAME=webMethods to Boomi Migration Accelerator
```

## Architecture

### Technology Stack

**Backend:**
- Python 3.10+
- FastAPI
- MongoDB Atlas (Motor async driver)
- lxml (XML parsing)
- NetworkX (dependency analysis)
- Cryptography (Fernet encryption)

**Frontend:**
- React 18
- TypeScript
- Vite
- TailwindCSS
- React Query
- Monaco Editor
- Recharts
- ReactFlow

### MongoDB Collections

- `customers` - Customer accounts and settings
- `projects` - Migration projects and parsed data
- `conversions` - Converted Boomi components
- `mappings` - Field mappings
- `logs` - Activity logs

## webMethods to Boomi Mapping

Based on official Boomi community documentation.

### The 9 Flow Verbs

| webMethods Verb | Boomi Shape | Notes |
|----------------|-------------|-------|
| MAP | Map shape / Set Properties | Data transformation |
| BRANCH | Decision shape | Conditional logic |
| LOOP | ForEach (implicit) | Boomi handles automatically |
| REPEAT | ForEach with condition | While loop behavior |
| SEQUENCE | Try/Catch | Grouping and error handling |
| Try/Catch | Try/Catch | Error handling |
| Try/Finally | Try/Catch | Cleanup handling |
| Catch | Try/Catch | Exception handling |
| Finally | Try/Catch | Always execute |
| EXIT | Stop | Exit process |

### Component Conversions

| webMethods | Boomi | Automation |
|-----------|-------|------------|
| Document Type | Profile (XML/JSON/EDI) | 95% |
| Flow Service (simple) | Process | 90% |
| Flow Service (complex) | Process | 70% |
| JDBC Adapter | Database Connector | 50-80% |
| HTTP/JMS/FTP Adapter | Connectors | 85% |
| Java Service | Groovy Script | 20% |

## API Endpoints

### Customers
- `POST /api/customers` - Create customer
- `GET /api/customers` - List customers
- `GET /api/customers/{id}` - Get customer
- `PUT /api/customers/{id}` - Update customer
- `DELETE /api/customers/{id}` - Delete customer
- `POST /api/customers/{id}/test-boomi` - Test Boomi connection
- `POST /api/customers/{id}/test-llm` - Test LLM connection

### Projects
- `POST /api/projects` - Upload package
- `GET /api/projects` - List projects
- `GET /api/projects/{id}` - Get project
- `POST /api/projects/{id}/parse` - Parse package
- `POST /api/projects/{id}/analyze` - Analyze project
- `DELETE /api/projects/{id}` - Delete project
- `GET /api/projects/{id}/files` - Get file tree
- `GET /api/projects/{id}/files/{path}` - Get file content

### Conversions
- `POST /api/conversions` - Convert service
- `POST /api/conversions/convert-all` - Convert all services
- `GET /api/conversions` - List conversions
- `GET /api/conversions/{id}` - Get conversion
- `POST /api/conversions/{id}/push` - Push to Boomi

### AI Assistant
- `POST /api/ai/chat` - Chat with AI
- `POST /api/ai/generate-groovy` - Generate Groovy from Java
- `POST /api/ai/map-wmpublic` - Map wMPublic service

## Usage Guide

### 1. Create a Customer

1. Navigate to **Customers**
2. Click **Add Customer**
3. Enter customer name
4. Configure Boomi credentials (Account ID, Username, API Token)
5. Configure LLM settings (Provider, API Key, Model)
6. Save and test connections

### 2. Upload a Package

1. Select a customer from the sidebar
2. Navigate to **Projects**
3. Drag & drop a webMethods package ZIP file
4. Wait for upload to complete

### 3. Parse & Analyze

1. Click **Parse** to parse the package
2. Once parsed, click **Analyze** to analyze complexity
3. View results in the Analysis Dashboard

### 4. Convert to Boomi

1. Navigate to **Conversions**
2. Click **Convert All Services**
3. Review conversion results and notes
4. Click **Push to Boomi** to deploy

### 5. Use AI Assistant

1. Navigate to **AI Assistant**
2. Optionally select a project for context
3. Ask questions about migration

## Branding

Jade Global brand colors:
- Primary: `#00A86B`
- Dark: `#008C5A`
- Light: `#E8F5F0`
- Accent: `#00C878`

Place your logo at `frontend/public/jade-logo1.png`

## Security

- Sensitive credentials are encrypted using Fernet symmetric encryption
- Generate an encryption key: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
- Store the key in `ENCRYPTION_KEY` environment variable

## Development

### Generate Encryption Key

```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```

### Run Tests

```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm test
```

### Build for Production

```bash
# Frontend
cd frontend
npm run build

# Backend uses uvicorn in production
uvicorn app.main:app --host 0.0.0.0 --port 7201
```

## Troubleshooting

### MongoDB Connection Issues
- Verify connection string in `.env`
- Check network connectivity to MongoDB Atlas
- Ensure IP is whitelisted in MongoDB Atlas

### Parsing Errors
- Ensure uploaded file is a valid ZIP
- Check file contains expected webMethods structure
- View logs for detailed error messages

### Conversion Issues
- Complex JDBC queries may require manual review
- Java services need manual Groovy conversion
- Check conversion notes for specific issues

## License

Proprietary - Jade Global Inc.

## Support

For support, contact Jade Global Integration Services team.

---

**Version:** 3.0.0  
**Date:** November 24, 2025  
**Author:** Jade Global Inc.
