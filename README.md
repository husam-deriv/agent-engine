# Deriv Agent Engine

## Overview
The Deriv Agent Engine is a comprehensive platform for building, deploying, and managing AI agents. It enables the creation of customized AI agents that can perform various tasks through a user-friendly interface.

## System Architecture

The system consists of several key components:

### Frontend Components
- **agent-ui**: Modern Next.js frontend application for agent building and interaction
- **frontend**: Main frontend application for user-facing functionality
- **frontend-legacy**: Legacy frontend components maintained for backward compatibility

### Backend Components
- **backend**: Core Python backend service handling agent execution, data processing, and API endpoints
- **backend-legacy**: Previous version of the backend maintained for compatibility
- **backend-prod**: Production-ready backend implementation

### Data & Tools
- **ToolRepository**: Collection of tools that agents can leverage for various tasks
- **ml-on-the-fly**: On-demand machine learning capabilities

## Key Features
- Agent building and customization
- Agent playground for testing
- Dashboard for monitoring and management
- RAG (Retrieval-Augmented Generation) capabilities
- Document processing and data ingestion
- Tool integration framework

## Technology Stack
- **Frontend**: Next.js, React, Modern UI components
- **Backend**: Python, FastAPI, OpenAI integrations
- **Database**: SQLite (development), production databases
- **AI/ML**: Various libraries for machine learning and NLP tasks

## Setup and Installation

### Prerequisites
- Node.js (v16+)
- Python 3.12+
- Git

### Installation Steps
1. Clone the repository:
   ```
   git clone https://github.com/husam-deriv/deriv-agent-engine.git
   cd deriv-agent-engine
   ```

2. Set up environment variables:
   ```
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. Backend setup:
   ```
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. Frontend setup:
   ```
   cd ../agent-ui
   npm install
   npm run dev
   ```

5. Initialize the database:
   ```
   cd ..
   python create_sqlite_db.py
   ```

## Development Workflow

### Running the Application
- Backend: `cd backend && uvicorn main:app --reload`
- Frontend: `cd agent-ui && npm run dev`

### Architecture Diagram
See the schema diagrams in the project root for database and agent space architecture:
- `db_schema.png`
- `db_agent_engine_schema.png`
- `agent_space_schema.png`

## Contributing
Please follow the contribution guidelines when submitting pull requests.