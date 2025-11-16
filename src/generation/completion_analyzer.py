"""
Completion Analyzer - Calculates how complete a generated app is
and generates actionable completion guides
"""

from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class CompletionMetrics:
    """Metrics showing how complete the generated app is"""
    overall_percentage: float
    backend_percentage: float
    frontend_percentage: float
    database_percentage: float
    testing_percentage: float
    deployment_percentage: float

    completed_items: List[str]
    missing_items: List[str]

    estimated_hours_remaining: float


class CompletionAnalyzer:
    """
    Analyzes generated applications to determine completion percentage
    and what remains to be done
    """

    def __init__(self):
        pass

    def analyze(
        self,
        generated_app: Any,
        spec: Any
    ) -> CompletionMetrics:
        """
        Analyzes a generated app and calculates completion metrics

        Returns CompletionMetrics with accurate percentages
        """

        completed = []
        missing = []

        # Backend Analysis
        backend_complete, backend_items = self._analyze_backend(generated_app, spec)
        completed.extend([f"Backend: {item}" for item in backend_items['completed']])
        missing.extend([f"Backend: {item}" for item in backend_items['missing']])

        # Frontend Analysis
        frontend_complete, frontend_items = self._analyze_frontend(generated_app, spec)
        completed.extend([f"Frontend: {item}" for item in frontend_items['completed']])
        missing.extend([f"Frontend: {item}" for item in frontend_items['missing']])

        # Database Analysis
        database_complete, database_items = self._analyze_database(generated_app, spec)
        completed.extend([f"Database: {item}" for item in database_items['completed']])
        missing.extend([f"Database: {item}" for item in database_items['missing']])

        # Testing Analysis
        testing_complete, testing_items = self._analyze_testing(generated_app)
        completed.extend([f"Testing: {item}" for item in testing_items['completed']])
        missing.extend([f"Testing: {item}" for item in testing_items['missing']])

        # Deployment Analysis
        deployment_complete, deployment_items = self._analyze_deployment(generated_app)
        completed.extend([f"Deployment: {item}" for item in deployment_items['completed']])
        missing.extend([f"Deployment: {item}" for item in deployment_items['missing']])

        # Calculate weighted overall percentage
        # Backend 30%, Frontend 35%, Database 15%, Testing 10%, Deployment 10%
        overall = (
            backend_complete * 0.30 +
            frontend_complete * 0.35 +
            database_complete * 0.15 +
            testing_complete * 0.10 +
            deployment_complete * 0.10
        )

        # Estimate hours remaining based on missing items
        hours_remaining = self._estimate_completion_time(missing)

        return CompletionMetrics(
            overall_percentage=round(overall, 1),
            backend_percentage=round(backend_complete, 1),
            frontend_percentage=round(frontend_complete, 1),
            database_percentage=round(database_complete, 1),
            testing_percentage=round(testing_complete, 1),
            deployment_percentage=round(deployment_complete, 1),
            completed_items=completed,
            missing_items=missing,
            estimated_hours_remaining=round(hours_remaining, 1)
        )

    def _analyze_backend(self, app: Any, spec: Any) -> tuple[float, Dict]:
        """Analyzes backend completeness"""
        required = [
            'server.js',
            'database connection',
            'authentication',
            'user model',
            'user controller',
            'user routes',
            'auth routes',
            'middleware (auth, validation, security)',
            'domain-specific models',
            'domain-specific controllers',
            'domain-specific routes',
            'error handling',
            'input validation',
        ]

        completed = []
        missing = []

        # Check what exists
        backend_code = app.backend_code if hasattr(app, 'backend_code') else {}

        if 'src/server.js' in backend_code:
            completed.append('Express server with security middleware')
        else:
            missing.append('Express server setup')

        if 'src/db/connection.js' in backend_code:
            completed.append('PostgreSQL database connection')
        else:
            missing.append('Database connection')

        if 'src/middleware/auth.js' in backend_code:
            completed.append('JWT authentication middleware')
        else:
            missing.append('Authentication middleware')

        if 'src/models/user.js' in backend_code:
            completed.append('User model with CRUD operations')
        else:
            missing.append('User model')

        # Check for domain-specific models
        model_files = [f for f in backend_code.keys() if f.startswith('src/models/') and f != 'src/models/user.js']
        if model_files:
            completed.append(f'Domain-specific models ({len(model_files)} files)')
        else:
            missing.append('Domain-specific models (for your app\'s entities)')

        # Check for domain-specific controllers
        controller_files = [f for f in backend_code.keys() if f.startswith('src/controllers/')]
        if controller_files:
            completed.append(f'Controllers ({len(controller_files)} files)')
        else:
            missing.append('Domain-specific controllers')

        # Check for domain-specific routes
        route_files = [f for f in backend_code.keys() if f.startswith('src/routes/') and f != 'src/routes/auth.js']
        if route_files:
            completed.append(f'API routes ({len(route_files)} files)')
        else:
            missing.append('Domain-specific API routes')

        if 'src/middleware/validation.js' in backend_code:
            completed.append('Input validation middleware')

        if 'src/middleware/security.js' in backend_code:
            completed.append('Security middleware (CSRF, XSS protection)')

        # Calculate percentage
        completed_count = len(completed)
        total_required = len(required)
        percentage = (completed_count / total_required) * 100

        return percentage, {'completed': completed, 'missing': missing}

    def _analyze_frontend(self, app: Any, spec: Any) -> tuple[float, Dict]:
        """Analyzes frontend completeness"""
        required = [
            'Next.js configuration',
            'TypeScript configuration',
            'Tailwind CSS configuration',
            'Root layout',
            'Home page',
            'Login page',
            'Register page',
            'Dashboard page',
            'Profile page',
            'Domain-specific pages',
            'UI components (Button, Input, Card, etc.)',
            'Auth context/hooks',
            'API integration layer',
            'State management',
            'Error handling',
            'Loading states',
        ]

        completed = []
        missing = []

        frontend_code = app.frontend_code if hasattr(app, 'frontend_code') else {}

        if 'frontend/package.json' in frontend_code:
            completed.append('Next.js + React + TypeScript + Tailwind configured')
        else:
            missing.append('Frontend framework setup')

        if 'frontend/src/app/layout.tsx' in frontend_code:
            completed.append('Root layout with navigation')

        if 'frontend/src/app/page.tsx' in frontend_code:
            completed.append('Home/Landing page')

        if 'frontend/src/app/login/page.tsx' in frontend_code:
            completed.append('Login page with form validation')

        if 'frontend/src/app/register/page.tsx' in frontend_code:
            completed.append('Registration page')

        # Check for UI components
        component_files = [f for f in frontend_code.keys() if 'components/ui/' in f]
        if component_files:
            completed.append(f'Reusable UI components ({len(component_files)} components)')
        else:
            missing.append('UI component library')

        if 'frontend/src/hooks/useAuth.tsx' in frontend_code:
            completed.append('Authentication context and hooks')
        else:
            missing.append('Authentication hooks')

        if 'frontend/src/lib/api.ts' in frontend_code:
            completed.append('API integration layer with Axios')
        else:
            missing.append('API client setup')

        # Check for domain-specific pages
        app_pages = [f for f in frontend_code.keys() if f.startswith('frontend/src/app/') and f.endswith('/page.tsx')]
        domain_pages = [p for p in app_pages if 'login' not in p and 'register' not in p and p != 'frontend/src/app/page.tsx']

        if domain_pages:
            completed.append(f'Domain-specific pages ({len(domain_pages)} pages)')
        else:
            missing.append('Domain-specific pages (dashboard, data views, etc.)')

        # Calculate percentage
        completed_count = len(completed)
        percentage = (completed_count / len(required)) * 100

        return percentage, {'completed': completed, 'missing': missing}

    def _analyze_database(self, app: Any, spec: Any) -> tuple[float, Dict]:
        """Analyzes database schema completeness"""
        completed = []
        missing = []

        schema = app.database_schema if hasattr(app, 'database_schema') else ''

        if 'CREATE TABLE' in schema:
            # Count tables
            table_count = schema.count('CREATE TABLE')
            completed.append(f'Database schema with {table_count} tables')

            if 'uuid-ossp' in schema:
                completed.append('UUID extension for primary keys')

            if 'INDEX' in schema or 'CREATE INDEX' in schema:
                completed.append('Indexes for query optimization')
            else:
                missing.append('Database indexes')

            if 'FOREIGN KEY' in schema or 'REFERENCES' in schema:
                completed.append('Foreign key relationships')
            else:
                missing.append('Foreign key constraints')

            if 'created_at' in schema and 'updated_at' in schema:
                completed.append('Timestamp tracking')

            # Check for users table
            if 'users' in schema.lower():
                completed.append('Users table with authentication fields')
            else:
                missing.append('Users table')

        else:
            missing.append('Database schema generation')

        # Database should be fairly complete with what's generated
        percentage = (len(completed) / (len(completed) + len(missing))) * 100 if completed or missing else 0

        return percentage, {'completed': completed, 'missing': missing}

    def _analyze_testing(self, app: Any) -> tuple[float, Dict]:
        """Analyzes testing setup"""
        completed = []
        missing = []

        backend_code = app.backend_code if hasattr(app, 'backend_code') else {}

        # Check for test files
        test_files = [f for f in backend_code.keys() if 'test' in f.lower() or 'spec' in f.lower()]

        if not test_files:
            missing.extend([
                'Unit tests for models',
                'Unit tests for controllers',
                'Integration tests for API endpoints',
                'Authentication tests',
                'Test configuration (Jest)',
            ])

        # Testing is typically 0% complete in initial generation
        percentage = 0.0

        return percentage, {'completed': completed, 'missing': missing}

    def _analyze_deployment(self, app: Any) -> tuple[float, Dict]:
        """Analyzes deployment readiness"""
        completed = []
        missing = []

        deployment_config = app.deployment_config if hasattr(app, 'deployment_config') else {}

        if 'Dockerfile' in deployment_config or 'Dockerfile' in getattr(app, 'backend_code', {}):
            completed.append('Docker configuration')
        else:
            missing.append('Docker configuration')

        if 'docker-compose.yml' in deployment_config or 'docker-compose.yml' in getattr(app, 'backend_code', {}):
            completed.append('Docker Compose for local development')
        else:
            missing.append('Docker Compose setup')

        if '.env.example' in getattr(app, 'backend_code', {}):
            completed.append('Environment configuration template')

        # Always missing initially
        missing.extend([
            'CI/CD pipeline (GitHub Actions)',
            'Production environment variables',
            'SSL certificate setup',
            'Domain configuration',
            'Database migration scripts',
        ])

        percentage = (len(completed) / (len(completed) + len(missing))) * 100 if completed or missing else 0

        return percentage, {'completed': completed, 'missing': missing}

    def _estimate_completion_time(self, missing_items: List[str]) -> float:
        """Estimates hours needed to complete missing items"""

        # Time estimates (in hours) for different types of tasks
        time_map = {
            'model': 0.5,
            'controller': 0.75,
            'route': 0.5,
            'page': 1.0,
            'component': 0.5,
            'test': 1.5,
            'deployment': 2.0,
            'authentication': 1.0,
            'api': 0.5,
            'default': 1.0,
        }

        total_hours = 0
        for item in missing_items:
            item_lower = item.lower()

            # Find matching category
            hours = time_map['default']
            for key, value in time_map.items():
                if key in item_lower:
                    hours = value
                    break

            total_hours += hours

        return total_hours


class CompletionGuideGenerator:
    """
    Generates comprehensive completion guides for developers
    to finish the generated application
    """

    def __init__(self):
        self.analyzer = CompletionAnalyzer()

    def generate_completion_guide(
        self,
        generated_app: Any,
        spec: Any,
        metrics: CompletionMetrics
    ) -> str:
        """
        Generates a complete COMPLETION_GUIDE.md file
        """

        guide = f"""# Completion Guide - {spec.app_name}

**Generated by VerifiMind™ on {datetime.now().strftime('%Y-%m-%d %H:%M')}**

## Overview

Your application foundation has been generated and is **{metrics.overall_percentage}% complete**.

**Estimated time to complete**: {metrics.estimated_hours_remaining} hours

---

## What's Already Built ✅

"""

        # Add completed items
        for item in metrics.completed_items:
            guide += f"- ✅ {item}\n"

        guide += f"""

---

## What You Need to Complete ⚠️

The following components need to be implemented to make your app production-ready:

"""

        # Group missing items by category
        backend_missing = [item for item in metrics.missing_items if item.startswith('Backend:')]
        frontend_missing = [item for item in metrics.missing_items if item.startswith('Frontend:')]
        database_missing = [item for item in metrics.missing_items if item.startswith('Database:')]
        testing_missing = [item for item in metrics.missing_items if item.startswith('Testing:')]
        deployment_missing = [item for item in metrics.missing_items if item.startswith('Deployment:')]

        if backend_missing:
            guide += "\n### Backend Missing Items\n\n"
            for item in backend_missing:
                guide += f"- ⚠️ {item.replace('Backend: ', '')}\n"

        if frontend_missing:
            guide += "\n### Frontend Missing Items\n\n"
            for item in frontend_missing:
                guide += f"- ⚠️ {item.replace('Frontend: ', '')}\n"

        if database_missing:
            guide += "\n### Database Missing Items\n\n"
            for item in database_missing:
                guide += f"- ⚠️ {item.replace('Database: ', '')}\n"

        if testing_missing:
            guide += "\n### Testing Missing Items\n\n"
            for item in testing_missing:
                guide += f"- ⚠️ {item.replace('Testing: ', '')}\n"

        if deployment_missing:
            guide += "\n### Deployment Missing Items\n\n"
            for item in deployment_missing:
                guide += f"- ⚠️ {item.replace('Deployment: ', '')}\n"

        guide += f"""

---

## Step-by-Step Completion Plan

Follow these phases to complete your application:

### Phase 1: Domain-Specific Backend (Est: 2-3 hours)

1. **Review Generated Schema**
   - Open `database/schema.sql`
   - Verify the entities match your needs
   - Add any missing tables or fields

2. **Implement Domain Models**
   - Create model files in `src/models/` for each entity
   - Add CRUD methods (findAll, findById, create, update, delete)
   - Use parameterized queries to prevent SQL injection

3. **Implement Controllers**
   - Create controller files in `src/controllers/`
   - Add business logic for each operation
   - Handle errors with proper HTTP status codes

4. **Create API Routes**
   - Add route files in `src/routes/`
   - Connect routes to controllers
   - Add authentication middleware where needed

**Recommended Tool**: Use Claude Code or Cursor to help implement these files.
Example prompt: "Create a model file for [entity] with CRUD operations using PostgreSQL"

### Phase 2: Frontend Pages & Components (Est: 3-4 hours)

1. **Create Domain-Specific Pages**
   - Add pages in `frontend/src/app/` for your main features
   - Use the generated login/register pages as examples
   - Connect to backend API using the provided `apiClient`

2. **Build Feature Components**
   - Create reusable components in `frontend/src/components/`
   - Use the generated Button, Input, Card components as building blocks
   - Implement forms with validation

3. **Add Data Fetching**
   - Use the `useApi` hook for GET requests
   - Implement create/update/delete operations
   - Add loading and error states

**Recommended Tool**: Use Claude Code with the prompt:
"Create a [feature] page that displays data from /api/[endpoint] with create/edit/delete capabilities"

### Phase 3: Testing (Est: 2-3 hours)

1. **Set Up Testing Framework**
   ```bash
   npm install --save-dev jest supertest @testing-library/react @testing-library/jest-dom
   ```

2. **Write API Tests**
   - Test authentication endpoints
   - Test CRUD operations for each resource
   - Test error handling

3. **Write Frontend Tests**
   - Test component rendering
   - Test user interactions
   - Test API integration

### Phase 4: Deployment (Est: 1-2 hours)

1. **Set Up Database**
   - Create PostgreSQL database
   - Run `database/schema.sql`
   - Set DATABASE_URL in production

2. **Configure Environment**
   - Copy `.env.example` to `.env`
   - Set all required environment variables
   - Generate secure JWT_SECRET

3. **Deploy**

   **Option A: Docker (Recommended)**
   ```bash
   docker-compose up --build
   ```

   **Option B: Vercel (Frontend) + Railway/Render (Backend)**
   - Deploy frontend to Vercel
   - Deploy backend to Railway or Render
   - Configure environment variables

---

## Completion Checklist

Use this checklist to track your progress:

### Backend
- [ ] All domain-specific models implemented
- [ ] All controllers implemented
- [ ] All API routes created
- [ ] Business logic tested manually
- [ ] Error handling verified

### Frontend
- [ ] Dashboard page implemented
- [ ] All domain-specific pages created
- [ ] Forms connect to backend successfully
- [ ] Data displays correctly
- [ ] Loading/error states implemented

### Database
- [ ] Schema reviewed and approved
- [ ] Migrations created (if needed)
- [ ] Indexes optimized
- [ ] Data validation rules in place

### Testing
- [ ] API endpoint tests written
- [ ] Authentication tests passing
- [ ] Frontend component tests written
- [ ] Integration tests passing

### Deployment
- [ ] Environment variables configured
- [ ] Database deployed
- [ ] Backend deployed
- [ ] Frontend deployed
- [ ] SSL certificate configured
- [ ] Custom domain set up (optional)

---

## Getting Help

### Using AI Assistants

This app was designed to be completed with AI coding assistants like:

- **Claude Code** (Recommended)
- **Cursor**
- **GitHub Copilot**

**Effective Prompts:**

1. "Review the database schema and create models for all entities"
2. "Implement the [resource]Controller with full CRUD operations"
3. "Create a Next.js page that displays [data] from the API"
4. "Add form validation for [fields] using react-hook-form"
5. "Write tests for the authentication endpoints"

### Resources

- [Express.js Documentation](https://expressjs.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)

---

## Completion Metrics

| Category | Completion | Status |
|----------|------------|--------|
| Backend | {metrics.backend_percentage}% | {'✅' if metrics.backend_percentage >= 80 else '⚠️'} |
| Frontend | {metrics.frontend_percentage}% | {'✅' if metrics.frontend_percentage >= 80 else '⚠️'} |
| Database | {metrics.database_percentage}% | {'✅' if metrics.database_percentage >= 80 else '⚠️'} |
| Testing | {metrics.testing_percentage}% | {'✅' if metrics.testing_percentage >= 80 else '⚠️'} |
| Deployment | {metrics.deployment_percentage}% | {'✅' if metrics.deployment_percentage >= 80 else '⚠️'} |
| **Overall** | **{metrics.overall_percentage}%** | **{'✅ Production Ready' if metrics.overall_percentage >= 80 else '⚠️ Needs Completion'}** |

---

**Good luck! You're {metrics.overall_percentage}% of the way there.**

*Generated by VerifiMind™ - Smart Scaffolding for the AI Era*
"""

        return guide
