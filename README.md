# AESA - AI Engineering Study Assistant

An enterprise-grade, local-first scheduling and personal learning assistant for KU Engineering students. AESA combines intelligent task scheduling with AI-powered study planning to help students optimize their academic performance.

## 🎯 Overview

AESA follows a **Brain-Engine** architecture pattern:
- **Brain**: Python/FastAPI backend with LangGraph AI orchestration handles intelligence, user interaction, and state management
- **Engine**: C-based constraint satisfaction solver handles performance-critical scheduling optimization

### Key Features

- 📅 **Smart Scheduling**: AI-powered task placement based on energy levels and priorities
- 🧠 **Deep Work Detection**: Identifies and protects 90+ minute focus blocks
- 📊 **Study Analytics**: Track study time, subjects, and productivity patterns
- 🤖 **AI Assistant**: Natural language interface for schedule management
- ⏱️ **Study Timer**: Track sessions with automatic deep work flagging
- 🎯 **Goal Tracking**: Set and monitor study goals with progress visualization

## 🏗️ Architecture

```mermaid
graph TB
    subgraph "Frontend (Next.js 14)"
        UI[React Components]
        Apollo[Apollo Client]
        WS[WebSocket Client]
    end
    
    subgraph "Backend (FastAPI)"
        REST[REST API]
        GQL[GraphQL API]
        Agent[LangGraph Agent]
        Tools[AI Tools]
        Scheduler[Scheduler Module]
        Bridge[C Bridge]
    end
    
    subgraph "Data Layer"
        PG[(PostgreSQL)]
        Engine[C Engine]
    end
    
    UI --> Apollo --> GQL
    UI --> REST --> Agent
    Agent --> Tools --> Scheduler
    Scheduler --> Bridge --> Engine
    Scheduler --> PG
```

### Technology Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 14, React, TypeScript, Tailwind CSS, Apollo Client |
| Backend | FastAPI, Python 3.11+, Strawberry GraphQL, LangGraph |
| Database | PostgreSQL 15, asyncpg |
| Engine | C99 (constraint satisfaction solver) |
| AI | LangGraph, copilot-api (OpenAI-compatible) |
| DevOps | Docker, GitHub Actions, GHCR |

## 📁 Project Structure

```
aesa/
├── frontend/                 # Next.js application
│   ├── src/
│   │   ├── app/             # App Router pages
│   │   ├── components/      # React components
│   │   └── lib/             # Utilities, hooks, GraphQL
│   └── Dockerfile
├── backend/                  # FastAPI application
│   ├── app/
│   │   ├── api/             # REST endpoints
│   │   ├── graphql/         # GraphQL schema
│   │   ├── agent/           # LangGraph agent
│   │   ├── tools/           # AI tools
│   │   ├── scheduler/       # Scheduling logic
│   │   └── models/          # SQLAlchemy models
│   └── Dockerfile
├── engine/                   # C optimization engine
│   ├── src/                 # C source files
│   ├── tests/               # C tests
│   └── Makefile
├── database/
│   └── init.sql             # Schema + triggers
├── docker-compose.yml
└── .github/workflows/       # CI/CD pipelines
```

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 18+ (for local frontend development)
- Python 3.11+ (for local backend development)
- GCC with C99 support (for engine development)

### Using Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/your-org/aesa.git
cd aesa

# Copy environment example
cp .env.example .env

# Start all services
docker-compose up -d

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# GraphQL Playground: http://localhost:8000/graphql
```

### Local Development

#### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/aesa
export COPILOT_API_URL=http://localhost:4141
export ENGINE_PATH=../engine/scheduler

# Run development server
uvicorn app.main:app --reload --port 8000
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Set environment variables
export NEXT_PUBLIC_API_URL=http://localhost:8000

# Run development server
npm run dev
```

#### C Engine

```bash
cd engine

# Build the scheduler
make

# Run tests
make test

# Memory check (requires valgrind)
make memcheck
```

## 📡 API Reference

### REST Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/schedule/today` | GET | Get today's schedule with gaps |
| `/api/schedule/week` | GET | Get weekly schedule |
| `/api/schedule/optimize` | POST | Trigger schedule optimization |
| `/api/schedule/preferences` | GET/PUT | Manage user preferences |
| `/api/tasks` | GET/POST | List or create tasks |
| `/api/tasks/{id}` | PATCH/DELETE | Update or delete task |
| `/api/timeline/today` | GET | Get optimized daily timeline |
| `/api/timeline/blocks` | POST | Create time block |
| `/api/timeline/blocks/{id}` | PATCH/DELETE | Manage time blocks |
| `/api/timer/start` | POST | Start study timer |
| `/api/timer/stop` | POST | Stop study timer |
| `/api/timer/status` | GET | Get current timer status |
| `/api/goals` | GET/POST | List or create goals |
| `/api/goals/{id}/progress` | POST | Update goal progress |
| `/api/chat` | POST | Send message to AI assistant |
| `/health` | GET | Health check endpoint |

### GraphQL API

Access the GraphQL Playground at `/graphql` for interactive API exploration.

#### Example Queries

```graphql
# Get today's schedule
query {
  todaySchedule {
    date
    blocks {
      id
      title
      startTime
      endTime
      blockType
    }
    stats {
      focusTimeMinutes
      deepWorkMinutes
    }
  }
}

# Get tasks with filter
query {
  tasks(filter: { isCompleted: false }) {
    id
    title
    priority
    deadline
  }
}
```

#### Example Mutations

```graphql
# Create a new task
mutation {
  createTask(input: {
    title: "Study Neural Networks"
    taskType: "study"
    durationMinutes: 90
    priority: 75
  }) {
    id
    title
  }
}

# Start study timer
mutation {
  startTimer(subjectCode: "MATH101") {
    isRunning
    startedAt
  }
}
```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `COPILOT_API_URL` | LLM proxy endpoint | `http://localhost:4141` |
| `ENGINE_PATH` | Path to C scheduler binary | `./engine/scheduler` |
| `CORS_ORIGINS` | Allowed CORS origins | `["http://localhost:3000"]` |
| `DEBUG` | Enable debug mode | `false` |
| `NEXT_PUBLIC_API_URL` | Backend API URL (frontend) | Required |

## 🧪 Testing

### Backend Tests

```bash
cd backend
pytest                           # Run all tests
pytest tests/unit/              # Unit tests only
pytest tests/property/          # Property-based tests
pytest --cov=app                # With coverage
```

### Frontend Tests

```bash
cd frontend
npm test                        # Run all tests
npm run test:coverage           # With coverage
```

### C Engine Tests

```bash
cd engine
make test                       # Run all tests
make memcheck                   # Memory leak check
```

## 🐳 Docker Images

Docker images are published to GitHub Container Registry:

```bash
# Pull latest images
docker pull ghcr.io/your-org/aesa-frontend:latest
docker pull ghcr.io/your-org/aesa-backend:latest
```

## 📚 Documentation

- [Contributing Guide](CONTRIBUTING.md) - Development guidelines and PR process
- [Changelog](CHANGELOG.md) - Version history and changes
- [Engine Documentation](engine/README.md) - C scheduler details
- [API Documentation](http://localhost:8000/docs) - OpenAPI/Swagger docs (when running)

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details on:

- Development setup
- Code style requirements
- Pull request process
- Testing guidelines

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- KU Engineering Department for domain expertise
- The FastAPI and Next.js communities for excellent frameworks
- LangGraph team for AI orchestration capabilities
