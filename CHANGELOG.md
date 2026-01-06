# Changelog

All notable changes to the AESA (AI Engineering Study Assistant) project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Documentation improvements in progress

---

## [1.0.0] - 2025-12-29

### Added

#### Core Scheduling Engine (C)
- Backtracking constraint satisfaction algorithm for task scheduling
- Energy-based scheduling heuristics (peak, medium, low energy periods)
- Priority-based task ordering
- Fixed slot preservation for immutable events
- Deadline compliance checking
- JSON input/output serialization
- Memory-safe implementation with proper cleanup

#### Backend (FastAPI)
- REST API endpoints for schedule, tasks, timeline, timer, and goals
- GraphQL API with Strawberry for flexible data fetching
- LangGraph AI agent with tool calling capabilities
- AI tools for schedule management and smart planning
- C Engine bridge via subprocess with JSON communication
- PostgreSQL database integration with asyncpg
- SQLAlchemy models for all entities
- Gap detection (micro, standard, deep work blocks)
- Priority system with automatic overdue elevation
- Subject code validation (KU format)
- Study session tracking with deep work detection
- Goal tracking with progress updates
- AI memory and guidelines storage
- Comprehensive error handling with graceful degradation
- Structured logging system
- Analytics aggregation for study statistics
- WebSocket support for real-time notifications

#### Frontend (Next.js)
- Flow Board with Kanban-style columns
- Task cards with drag-and-drop functionality
- Active task card with timer controls
- AI Assistant panel with chat interface
- Context and suggestion cards
- Study timer component with subject selection
- Goal tracker with progress visualization
- Study analytics dashboard with charts
- Dark mode support with theme toggle
- Apollo Client for GraphQL integration
- WebSocket notifications
- Responsive design with Tailwind CSS
- Loading skeletons and error states

#### Infrastructure
- Docker containerization for all services
- Docker Compose for local development
- Multi-stage Dockerfile builds
- GitHub Actions CI workflow (lint, test, build)
- GitHub Actions Docker publish workflow
- GHCR image publishing
- PostgreSQL database with init script
- Database triggers for auto-calculations

#### Documentation
- Comprehensive README with setup instructions
- Contributing guidelines
- PR template with checklist
- Engine documentation
- API reference

### Security
- Environment-based configuration
- No hardcoded credentials
- CORS configuration
- Input validation

### Testing
- Property-based tests for scheduling algorithms
- Unit tests for core functionality
- Test coverage for critical paths

---

## Version History

### Versioning Guidelines

- **MAJOR** version: Incompatible API changes
- **MINOR** version: New functionality (backward compatible)
- **PATCH** version: Bug fixes (backward compatible)

### Release Process

1. Update version in relevant files
2. Update CHANGELOG.md with changes
3. Create PR to `staging` branch
4. After testing, merge to `production`
5. Create GitHub Release with version tag

---

## Categories

Changes are grouped into the following categories:

- **Added**: New features
- **Changed**: Changes to existing functionality
- **Deprecated**: Features to be removed in future versions
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Security-related changes

---

[Unreleased]: https://github.com/your-org/aesa/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/your-org/aesa/releases/tag/v1.0.0
