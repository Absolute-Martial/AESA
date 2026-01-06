# Contributing to AESA

Thank you for your interest in contributing to the AI Engineering Study Assistant! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Code Style Guidelines](#code-style-guidelines)
- [Git Workflow](#git-workflow)
- [Pull Request Process](#pull-request-process)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment. Be kind, constructive, and professional in all interactions.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/your-username/aesa.git
   cd aesa
   ```
3. **Add the upstream remote**:
   ```bash
   git remote add upstream https://github.com/your-org/aesa.git
   ```
4. **Set up your development environment** (see below)

## Development Setup

### Prerequisites

- Docker & Docker Compose (recommended)
- Node.js 18+
- Python 3.11+
- GCC with C99 support
- PostgreSQL 15 (if not using Docker)

### Quick Setup with Docker

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Manual Setup

#### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/aesa
export ENGINE_PATH=../engine/scheduler

# Run server
uvicorn app.main:app --reload --port 8000
```

#### Frontend

```bash
cd frontend
npm install
export NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

#### C Engine

```bash
cd engine
make
make test
```

## Code Style Guidelines

### Python (Backend)

- Follow [PEP 8](https://pep8.org/) style guide
- Use [Google-style docstrings](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)
- Maximum line length: 100 characters
- Use type hints for all function signatures
- Format code with `black` and lint with `ruff`

```python
def calculate_priority(task: Task, deadline: datetime) -> int:
    """Calculate task priority based on deadline proximity.
    
    Args:
        task: The task to calculate priority for.
        deadline: The task's deadline.
        
    Returns:
        Priority score from 0-100.
        
    Raises:
        ValueError: If deadline is in the past.
    """
    pass
```

### TypeScript (Frontend)

- Follow the project's ESLint configuration
- Use JSDoc comments for components and utilities
- Use TypeScript strict mode
- Prefer functional components with hooks
- Maximum line length: 100 characters

```typescript
/**
 * TaskCard component displays a single task in the Flow Board.
 * 
 * @param props - Component props
 * @param props.task - The task to display
 * @param props.isActive - Whether this task is currently active
 * @param props.onEdit - Callback when edit is requested
 * @returns The rendered TaskCard component
 */
export function TaskCard({ task, isActive, onEdit }: TaskCardProps): JSX.Element {
  // ...
}
```

### C (Engine)

- Follow C99 standard
- Use snake_case for functions and variables
- Use UPPER_CASE for constants and macros
- Include header guards in all `.h` files
- Document all public functions

```c
/**
 * Optimize the schedule using backtracking CSP.
 * 
 * @param tasks Array of tasks to schedule
 * @param num_tasks Number of tasks in the array
 * @param fixed_slots Array of fixed time slots
 * @param num_fixed Number of fixed slots
 * @return Optimized timeline or NULL on failure
 */
Timeline* optimize_schedule(
    Task* tasks, 
    int num_tasks,
    TimeSlot* fixed_slots,
    int num_fixed
);
```

## Git Workflow

We follow a branching strategy with three primary branches:

- `main` - Development branch (default)
- `staging` - Integration testing
- `production` - Production releases

### Branch Naming

| Type | Pattern | Example |
|------|---------|---------|
| Feature | `feature/{ticket-id}-{description}` | `feature/123-add-timer` |
| Bug Fix | `fix/{ticket-id}-{description}` | `fix/456-timer-overflow` |
| Hotfix | `hotfix/{ticket-id}-{description}` | `hotfix/789-critical-bug` |
| Documentation | `docs/{description}` | `docs/api-reference` |

### Workflow Steps

1. **Create a branch** from `main`:
   ```bash
   git checkout main
   git pull upstream main
   git checkout -b feature/123-my-feature
   ```

2. **Make your changes** with clear, atomic commits:
   ```bash
   git add .
   git commit -m "feat: add study timer component"
   ```

3. **Keep your branch updated**:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

4. **Push and create a PR**:
   ```bash
   git push origin feature/123-my-feature
   ```

### Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting (no code change)
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance tasks

Examples:
```
feat(scheduler): add energy-based task placement
fix(timer): resolve overflow in duration calculation
docs(api): update GraphQL schema documentation
```

## Pull Request Process

1. **Fill out the PR template** completely
2. **Link related issues** using `Closes #123`
3. **Ensure all checks pass**:
   - Linting (ESLint, Ruff)
   - Type checking (TypeScript, mypy)
   - Unit tests
   - Property-based tests
   - Build verification
4. **Request review** from at least one maintainer
5. **Address feedback** promptly
6. **Squash commits** if requested before merge

### PR Checklist

- [ ] Code follows style guidelines
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] No new warnings or errors
- [ ] Self-reviewed the changes
- [ ] Linked related issues

## Testing Guidelines

### Test Types

1. **Unit Tests**: Test individual functions/components
2. **Property-Based Tests**: Test invariants across many inputs
3. **Integration Tests**: Test component interactions

### Running Tests

```bash
# Backend
cd backend
pytest                          # All tests
pytest tests/unit/             # Unit tests
pytest tests/property/         # Property tests
pytest --cov=app               # With coverage

# Frontend
cd frontend
npm test                       # All tests
npm run test:coverage          # With coverage

# C Engine
cd engine
make test                      # All tests
make memcheck                  # Memory check
```

### Writing Tests

#### Python (pytest + hypothesis)

```python
import pytest
from hypothesis import given, strategies as st

def test_priority_calculation():
    """Test specific priority calculation example."""
    task = create_task(deadline=tomorrow())
    assert calculate_priority(task) == 90

@given(st.integers(min_value=0, max_value=100))
def test_priority_bounds(priority: int):
    """Property: priority is always within bounds."""
    task = create_task(priority=priority)
    result = normalize_priority(task)
    assert 0 <= result <= 100
```

#### TypeScript (Jest + fast-check)

```typescript
import { fc } from 'fast-check';

test('task card renders correctly', () => {
  const task = createMockTask();
  render(<TaskCard task={task} />);
  expect(screen.getByText(task.title)).toBeInTheDocument();
});

test('priority is always valid', () => {
  fc.assert(
    fc.property(fc.integer({ min: 0, max: 100 }), (priority) => {
      const result = normalizePriority(priority);
      return result >= 0 && result <= 100;
    })
  );
});
```

### Test Coverage

- Aim for >80% code coverage
- Focus on critical paths and edge cases
- Property tests should run minimum 100 iterations

## Documentation

### Code Documentation

- **Python**: Google-style docstrings for all public functions, classes, and modules
- **TypeScript**: JSDoc comments for all components and utilities
- **C**: Doxygen-style comments for all public functions
- **GraphQL**: Descriptions for all types, queries, and mutations

### Updating Documentation

When making changes:

1. Update relevant docstrings/comments
2. Update README.md if adding features
3. Update CHANGELOG.md with your changes
4. Update API documentation if endpoints change

### Documentation Style

- Use clear, concise language
- Include code examples where helpful
- Keep documentation close to the code
- Update docs in the same PR as code changes

## Questions?

If you have questions about contributing:

1. Check existing issues and discussions
2. Open a new issue with the `question` label
3. Reach out to maintainers

Thank you for contributing to AESA! 🎉
