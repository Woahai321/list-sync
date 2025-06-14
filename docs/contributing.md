# Contributing to ListSync

We welcome contributions to ListSync! This guide will help you get started with development and explain our contribution process.

## Table of Contents

1. [Development Setup](#development-setup)
2. [Project Structure](#project-structure)
3. [Development Workflow](#development-workflow)
4. [Code Standards](#code-standards)
5. [Testing](#testing)
6. [Documentation](#documentation)
7. [Pull Request Process](#pull-request-process)
8. [Release Process](#release-process)

## Development Setup

### Prerequisites

- **Python 3.9+** with Poetry for dependency management
- **Node.js 18+** with npm for frontend development
- **Docker & Docker Compose** for containerized development
- **Git** for version control
- **Chrome/Chromium** for Selenium testing

### Local Development Environment

1. **Clone the Repository**
   ```bash
   git clone https://github.com/your-repo/list-sync.git
   cd list-sync
   ```

2. **Backend Setup (Python)**
   ```bash
   # Install Poetry if not already installed
   pip install poetry==1.8.3
   
   # Install Python dependencies
   poetry install
   
   # Install additional API dependencies
   poetry run pip install -r api_requirements.txt
   
   # Activate virtual environment
   poetry shell
   ```

3. **Frontend Setup (Next.js)**
   ```bash
   cd listsync-web
   npm install
   ```

4. **Environment Configuration**
   ```bash
   # Copy example environment file
   cp envsample.txt .env
   
   # Edit .env with your development settings
   nano .env
   ```

5. **Database Setup**
   ```bash
   # Database will be automatically initialized on first run
   python -m list_sync --setup
   ```

### Development Docker Setup

For containerized development:

```bash
# Build development image
docker-compose -f docker-compose.local.yml build

# Start development environment
docker-compose -f docker-compose.local.yml up -d

# View logs
docker-compose -f docker-compose.local.yml logs -f
```

### IDE Configuration

**Recommended VS Code Extensions:**
- Python
- Pylance
- Black Formatter
- ES7+ React/Redux/React-Native snippets
- TypeScript and JavaScript Language Features
- Tailwind CSS IntelliSense
- Docker

**Python Settings (settings.json):**
```json
{
    "python.defaultInterpreterPath": ".venv/bin/python",
    "python.formatting.provider": "black",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.linting.flake8Enabled": true
}
```

## Project Structure

```
list-sync-main/
├── list_sync/                    # Core Python application
│   ├── providers/               # List provider implementations
│   ├── notifications/           # Notification services
│   ├── ui/                     # CLI interface components
│   ├── utils/                  # Utility modules
│   ├── main.py                 # Main application entry point
│   ├── config.py               # Configuration management
│   ├── database.py             # Database operations
│   └── sync_service.py         # Core sync logic
├── listsync-web/               # Next.js frontend application
│   ├── src/
│   │   ├── app/               # Next.js App Router pages
│   │   ├── components/        # React components
│   │   ├── hooks/             # Custom React hooks
│   │   ├── lib/               # Utility libraries
│   │   └── types/             # TypeScript type definitions
│   ├── public/                # Static assets
│   └── package.json           # Node.js dependencies
├── docs/                       # Documentation
├── development-files/          # Development utilities
├── api_server.py              # FastAPI backend server
├── pyproject.toml             # Python project configuration
├── Dockerfile                 # Multi-stage container build
├── docker-compose.yml         # Production deployment
└── docker-compose.local.yml   # Development environment
```

### Key Components

**Backend (Python):**
- **Core Application** - `list_sync/` - Main sync logic and providers
- **API Server** - `api_server.py` - FastAPI REST API
- **Database** - SQLite with automatic migrations
- **Providers** - Modular list source implementations

**Frontend (Next.js):**
- **App Router** - Modern Next.js routing
- **Components** - Reusable UI components with Radix UI
- **Hooks** - Custom React hooks for API integration
- **Types** - TypeScript interfaces and types

## Development Workflow

### Branch Strategy

- **main** - Production-ready code
- **develop** - Integration branch for features
- **feature/** - Individual feature branches
- **bugfix/** - Bug fix branches
- **hotfix/** - Critical production fixes

### Feature Development

1. **Create Feature Branch**
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/your-feature-name
   ```

2. **Development Process**
   - Write code following our standards
   - Add tests for new functionality
   - Update documentation as needed
   - Test thoroughly in development environment

3. **Commit Guidelines**
   ```bash
   # Use conventional commit format
   git commit -m "feat: add new list provider support"
   git commit -m "fix: resolve sync timeout issue"
   git commit -m "docs: update API documentation"
   ```

4. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   # Create pull request via GitHub/GitLab interface
   ```

### Local Testing

**Backend Testing:**
```bash
# Run Python tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=list_sync

# Run specific test file
poetry run pytest tests/test_providers.py
```

**Frontend Testing:**
```bash
cd listsync-web

# Run Next.js tests
npm test

# Run with coverage
npm run test:coverage

# Run E2E tests
npm run test:e2e
```

**Integration Testing:**
```bash
# Start full stack locally
docker-compose -f docker-compose.local.yml up

# Run integration tests
npm run test:integration
```

## Code Standards

### Python Code Standards

**Style Guidelines:**
- **PEP 8** compliance with Black formatting
- **Type hints** for all function parameters and returns
- **Docstrings** for all classes and functions
- **Error handling** with specific exception types

**Example:**
```python
from typing import List, Optional, Dict
import logging

def sync_list(
    list_id: str, 
    list_type: str, 
    limit: Optional[int] = None
) -> Dict[str, int]:
    """
    Synchronize items from a specific list.
    
    Args:
        list_id: Identifier for the list to sync
        list_type: Type of list provider (imdb, trakt, etc.)
        limit: Maximum number of items to sync
        
    Returns:
        Dictionary containing sync results and statistics
        
    Raises:
        ValueError: If list_id or list_type is invalid
        ConnectionError: If provider is unreachable
    """
    try:
        # Implementation here
        return {"requested": 10, "failed": 0}
    except Exception as e:
        logging.error(f"Sync failed for {list_type} list {list_id}: {e}")
        raise
```

**Linting Configuration:**
```toml
# pyproject.toml
[tool.black]
line-length = 88
target-version = ['py39']

[tool.pylint.messages_control]
disable = ["C0114", "C0116"]

[tool.flake8]
max-line-length = 88
extend-ignore = ["E203", "W503"]
```

### TypeScript/React Standards

**Component Structure:**
```typescript
// components/SyncStatus.tsx
import React from 'react';
import { cn } from '@/lib/utils';

interface SyncStatusProps {
  isActive: boolean;
  progress?: number;
  className?: string;
}

export function SyncStatus({ 
  isActive, 
  progress = 0, 
  className 
}: SyncStatusProps) {
  return (
    <div className={cn("sync-status", className)}>
      {/* Component implementation */}
    </div>
  );
}

export default SyncStatus;
```

**Hook Pattern:**
```typescript
// hooks/useSync.ts
import { useState, useEffect } from 'react';

interface SyncState {
  isLoading: boolean;
  progress: number;
  error?: string;
}

export function useSync(listId?: string) {
  const [state, setState] = useState<SyncState>({
    isLoading: false,
    progress: 0,
  });

  const startSync = async () => {
    // Implementation
  };

  return { ...state, startSync };
}
```

**Naming Conventions:**
- **Components** - PascalCase (`SyncStatus`)
- **Hooks** - camelCase with `use` prefix (`useSync`)
- **Utilities** - camelCase (`formatTime`)
- **Constants** - UPPER_SNAKE_CASE (`API_BASE_URL`)

### API Standards

**FastAPI Endpoint Structure:**
```python
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/api/lists", tags=["lists"])

class ListCreateRequest(BaseModel):
    list_type: str
    list_id: str
    auto_sync: bool = True

class ListResponse(BaseModel):
    id: int
    list_type: str
    list_id: str
    list_url: Optional[str]
    item_count: int
    last_synced: Optional[str]

@router.post("/", response_model=ListResponse)
async def create_list(request: ListCreateRequest):
    """Create a new list configuration."""
    try:
        # Implementation
        return ListResponse(...)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

## Testing

### Test Structure

```
tests/
├── unit/                    # Unit tests
│   ├── test_providers.py   # Provider functionality
│   ├── test_database.py    # Database operations
│   └── test_config.py      # Configuration management
├── integration/             # Integration tests
│   ├── test_sync_flow.py   # End-to-end sync testing
│   └── test_api.py         # API endpoint testing
└── fixtures/               # Test data and fixtures
    ├── sample_lists.json
    └── mock_responses.py
```

### Test Examples

**Unit Test:**
```python
# tests/unit/test_providers.py
import pytest
from unittest.mock import Mock, patch
from list_sync.providers.imdb import IMDbProvider

class TestIMDbProvider:
    def test_construct_list_url_chart(self):
        provider = IMDbProvider()
        url = provider.construct_list_url("top")
        assert url == "https://www.imdb.com/chart/top/"
    
    def test_construct_list_url_user_list(self):
        provider = IMDbProvider()
        url = provider.construct_list_url("ls123456789")
        assert url == "https://www.imdb.com/list/ls123456789/"
    
    @patch('list_sync.providers.imdb.requests.get')
    def test_fetch_list_items(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<html>Mock HTML</html>"
        mock_get.return_value = mock_response
        
        provider = IMDbProvider()
        items = provider.fetch_list_items("top")
        
        assert isinstance(items, list)
        mock_get.assert_called_once()
```

**Integration Test:**
```python
# tests/integration/test_sync_flow.py
import pytest
from fastapi.testclient import TestClient
from api_server import app

client = TestClient(app)

class TestSyncFlow:
    def test_full_sync_workflow(self):
        # Create list
        response = client.post("/api/lists/", json={
            "list_type": "imdb",
            "list_id": "top",
            "auto_sync": True
        })
        assert response.status_code == 200
        list_data = response.json()
        
        # Trigger sync
        response = client.post(f"/api/sync/lists/{list_data['id']}")
        assert response.status_code == 200
        
        # Check sync results
        response = client.get(f"/api/lists/{list_data['id']}")
        assert response.status_code == 200
        updated_list = response.json()
        assert updated_list["item_count"] > 0
```

### Frontend Testing

**Component Test:**
```typescript
// __tests__/components/SyncStatus.test.tsx
import { render, screen } from '@testing-library/react';
import { SyncStatus } from '@/components/SyncStatus';

describe('SyncStatus', () => {
  it('renders inactive state correctly', () => {
    render(<SyncStatus isActive={false} />);
    expect(screen.getByText(/inactive/i)).toBeInTheDocument();
  });

  it('shows progress when active', () => {
    render(<SyncStatus isActive={true} progress={50} />);
    expect(screen.getByText(/50%/)).toBeInTheDocument();
  });
});
```

## Documentation

### Code Documentation

**Python Docstrings:**
```python
def sync_items(items: List[Dict], overseerr_api: str) -> SyncResults:
    """
    Synchronize media items with Overseerr.
    
    This function processes a list of media items and requests them
    via the Overseerr API. It handles duplicate detection, error
    recovery, and progress tracking.
    
    Args:
        items: List of media items with title, year, and type
        overseerr_api: Base URL for Overseerr API
        
    Returns:
        SyncResults object containing statistics and failed items
        
    Raises:
        ConnectionError: When Overseerr API is unreachable
        ValueError: When items list is empty or malformed
        
    Example:
        >>> items = [{"title": "Movie", "year": 2023, "type": "movie"}]
        >>> results = sync_items(items, "http://overseerr:5055")
        >>> print(f"Requested: {results.requested_count}")
    """
```

**TypeScript JSDoc:**
```typescript
/**
 * Custom hook for managing sync operations
 * 
 * @param listId - Optional list ID to sync specific list
 * @returns Object containing sync state and control functions
 * 
 * @example
 * ```tsx
 * function SyncComponent() {
 *   const { isLoading, startSync, progress } = useSync("imdb-top");
 *   
 *   return (
 *     <button onClick={startSync} disabled={isLoading}>
 *       {isLoading ? `${progress}%` : 'Start Sync'}
 *     </button>
 *   );
 * }
 * ```
 */
export function useSync(listId?: string): SyncHookReturn {
  // Implementation
}
```

### Documentation Files

When contributing, update relevant documentation:

- **README.md** - Overview and quick start
- **docs/api.md** - API endpoint documentation
- **docs/configuration.md** - Configuration options
- **docs/troubleshooting.md** - Common issues and solutions

## Pull Request Process

### PR Requirements

- [ ] **Code follows style guidelines**
- [ ] **Tests added for new functionality**
- [ ] **Documentation updated**
- [ ] **All tests passing**
- [ ] **No linting errors**
- [ ] **PR description explains changes**

### PR Template

```markdown
## Description
Brief description of the changes made.

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

## Checklist
- [ ] Code follows the style guidelines
- [ ] Self-review of code completed
- [ ] Documentation updated
- [ ] No new warnings introduced
```

### Review Process

1. **Automated Checks** - CI/CD pipeline runs tests and linting
2. **Code Review** - Maintainer reviews code quality and design
3. **Testing** - Manual testing of functionality
4. **Approval** - PR approved by maintainer
5. **Merge** - PR merged to develop branch

## Release Process

### Version Management

We use semantic versioning (SemVer):
- **MAJOR** - Breaking changes
- **MINOR** - New features (backward compatible)
- **PATCH** - Bug fixes (backward compatible)

### Release Workflow

1. **Feature Freeze** - No new features for release
2. **Testing** - Comprehensive testing of release candidate
3. **Documentation** - Update changelog and documentation
4. **Tag Release** - Create git tag with version number
5. **Build Images** - Build and push Docker images
6. **Deploy** - Deploy to production environment

### Contributing Guidelines

- **Start Small** - Begin with bug fixes or small features
- **Discuss First** - Open an issue for major changes
- **Follow Standards** - Adhere to code and documentation standards
- **Be Patient** - Review process may take time
- **Stay Engaged** - Respond to review feedback promptly

### Getting Help

- **GitHub Issues** - Report bugs or request features
- **Discussions** - Ask questions or discuss ideas
- **Discord** - Join our community chat (if available)
- **Email** - Contact maintainers directly

Thank you for contributing to ListSync! Your contributions make this project better for everyone.
