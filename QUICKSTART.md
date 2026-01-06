# AESA Quick Start Guide

This guide will help you run the complete AESA application with all components.

## Prerequisites

- **Docker Desktop** installed and running
- **Git** installed
- **8GB RAM** minimum recommended
- **Ports available**: 3000 (frontend), 8000 (backend), 5432 (postgres)

## Option 1: Run with Docker Compose (Recommended)

This is the easiest way to run the entire application.

### Step 1: Start Docker Desktop

Make sure Docker Desktop is running on your machine.

### Step 2: Clone and Navigate to Repository

```bash
git clone https://github.com/Absolute-Martial/AESA.git
cd AESA
```

### Step 3: Build and Start All Services

```bash
docker-compose up --build
```

This command will:
- Build the frontend (Next.js)
- Build the backend (FastAPI)
- Start PostgreSQL database
- Initialize the database schema
- Start all services

### Step 4: Access the Application

Once all services are running, you can access:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **GraphQL Playground**: http://localhost:8000/graphql
- **PostgreSQL**: localhost:5432 (user: postgres, password: postgres, database: aesa)

### Step 5: Stop the Application

Press `Ctrl+C` in the terminal, then run:

```bash
docker-compose down
```

To also remove volumes (database data):

```bash
docker-compose down -v
```

---

## Option 2: Run Services Individually (Development)

For development with hot-reload and debugging.

### Step 1: Start PostgreSQL

```bash
docker-compose up postgres -d
```

Wait for PostgreSQL to be healthy (about 10 seconds).

### Step 2: Set Up Backend

```bash
# Navigate to backend directory
cd backend

# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations (if any)
# alembic upgrade head

# Start the backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: http://localhost:8000

### Step 3: Set Up Frontend (New Terminal)

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

Frontend will be available at: http://localhost:3000

---

## Option 3: Run with Pre-built Docker Images

If the images are published to ghcr.io:

### Step 1: Pull Images

```bash
docker pull ghcr.io/absolute-martial/aesa-backend:latest
docker pull ghcr.io/absolute-martial/aesa-frontend:latest
```

### Step 2: Create docker-compose.prod.yml

```yaml
version: '3.8'

services:
  frontend:
    image: ghcr.io/absolute-martial/aesa-frontend:latest
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    depends_on:
      - backend

  backend:
    image: ghcr.io/absolute-martial/aesa-backend:latest
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/aesa
      - ENGINE_PATH=/app/engine/scheduler
    depends_on:
      - postgres

  postgres:
    image: postgres:15-alpine
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=aesa
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

### Step 3: Run

```bash
docker-compose -f docker-compose.prod.yml up
```

---

## Troubleshooting

### Port Already in Use

If you get "port already in use" errors:

```bash
# Check what's using the port (Windows)
netstat -ano | findstr :3000
netstat -ano | findstr :8000
netstat -ano | findstr :5432

# Check what's using the port (Linux/Mac)
lsof -i :3000
lsof -i :8000
lsof -i :5432

# Kill the process or change the port in docker-compose.yml
```

### Docker Build Fails

```bash
# Clean Docker cache and rebuild
docker-compose down -v
docker system prune -a
docker-compose up --build --force-recreate
```

### Database Connection Issues

```bash
# Check if PostgreSQL is running
docker-compose ps

# Check PostgreSQL logs
docker-compose logs postgres

# Restart PostgreSQL
docker-compose restart postgres
```

### Frontend Can't Connect to Backend

Make sure:
1. Backend is running on port 8000
2. Check `NEXT_PUBLIC_API_URL` environment variable
3. Check CORS settings in backend

### Backend Can't Connect to Database

Make sure:
1. PostgreSQL is running and healthy
2. Check `DATABASE_URL` environment variable
3. Wait for PostgreSQL health check to pass

---

## Development Tips

### Hot Reload

When running with `docker-compose up`, the application supports hot reload:
- Frontend: Changes to `frontend/src` will auto-reload
- Backend: Changes to `backend/app` will auto-reload (if using `--reload` flag)

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
```

### Access Database

```bash
# Using docker exec
docker-compose exec postgres psql -U postgres -d aesa

# Or use a GUI tool like pgAdmin, DBeaver, or TablePlus
# Host: localhost
# Port: 5432
# User: postgres
# Password: postgres
# Database: aesa
```

### Run Tests

```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend tests (if configured)
cd frontend
npm test
```

### Build C Engine

```bash
cd engine
make all
make test
```

---

## Environment Variables

Create a `.env` file in the root directory (copy from `.env.example`):

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# Backend
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/aesa
COPILOT_API_URL=http://localhost:4141
ENGINE_PATH=./engine/scheduler
DEBUG=true

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000

# Optional: GitHub Token for AI features
# GITHUB_TOKEN=your_github_token_here
```

---

## Next Steps

1. **Explore the API**: Visit http://localhost:8000/docs for interactive API documentation
2. **Create a User**: Use the API or frontend to create your first user account
3. **Add Tasks**: Start adding tasks and let AESA optimize your schedule
4. **Check GraphQL**: Visit http://localhost:8000/graphql for GraphQL playground
5. **Review Logs**: Monitor logs for any issues or debugging

---

## Production Deployment

For production deployment, see:
- `CONTRIBUTING.md` for deployment guidelines
- `README.md` for architecture overview
- `.github/workflows/` for CI/CD pipelines

---

## Support

If you encounter issues:
1. Check the logs: `docker-compose logs -f`
2. Review the troubleshooting section above
3. Check GitHub Issues: https://github.com/Absolute-Martial/AESA/issues
4. Review the documentation in the repository

---

## Quick Commands Reference

```bash
# Start everything
docker-compose up --build

# Start in background
docker-compose up -d

# Stop everything
docker-compose down

# Stop and remove volumes
docker-compose down -v

# View logs
docker-compose logs -f

# Restart a service
docker-compose restart backend

# Rebuild a service
docker-compose up --build backend

# Access database
docker-compose exec postgres psql -U postgres -d aesa

# Run backend tests
docker-compose exec backend pytest tests/

# Check service status
docker-compose ps
```

---

**Happy Scheduling! 🚀**
