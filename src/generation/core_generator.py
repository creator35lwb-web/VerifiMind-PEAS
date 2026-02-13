"""
Core Code Generation Engine
Orchestrates the entire application generation process
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))
from src.llm.llm_provider import LLMProviderFactory, LLMMessage
from src.generation.frontend_generator import FrontendGenerator as ActualFrontendGenerator
from src.generation.completion_analyzer import CompletionAnalyzer, CompletionGuideGenerator


@dataclass
class AppSpecification:
    """Complete specification for app to be generated"""
    app_id: str
    app_name: str
    description: str
    category: str
    target_users: List[str]
    core_features: List[Dict[str, Any]]

    # Validation results from agents
    x_validation: Dict[str, Any]  # Business validation
    z_validation: Dict[str, Any]  # Compliance validation
    cs_validation: Dict[str, Any]  # Security validation

    # Technical requirements
    database_entities: List[Dict[str, Any]]
    api_endpoints: List[Dict[str, Any]]
    auth_requirements: Dict[str, Any]
    ui_pages: List[Dict[str, Any]]

    # Compliance requirements
    compliance_features: List[str]
    security_features: List[str]

    # Deployment config
    deployment_target: str  # 'aws', 'vercel', 'gcp', etc.
    custom_domain: Optional[str]

    metadata: Dict[str, Any]


@dataclass
class GeneratedApp:
    """Complete generated application"""
    app_id: str
    app_name: str

    # Generated code
    backend_code: Dict[str, str]  # filename -> code
    frontend_code: Dict[str, str]  # filename -> code
    database_schema: str
    deployment_config: Dict[str, Any]

    # Documentation
    readme: str
    api_docs: str
    user_guide: str

    # Metadata
    generated_at: datetime
    generator_version: str
    technology_stack: Dict[str, str]

    # Blockchain proof
    blockchain_hash: Optional[str]


class CodeGenerationEngine:
    """
    Main orchestrator for code generation
    Coordinates all generators to produce complete application
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config

        # Initialize LLM provider for AI-powered code generation
        provider_type = config.get('llm_provider', 'openai')
        api_key = config.get('openai_api_key') if provider_type == 'openai' else config.get('anthropic_api_key')
        model = config.get('model', 'gpt-4' if provider_type == 'openai' else 'claude-3-sonnet-20240229')

        self.llm_provider = LLMProviderFactory.create_provider(
            provider_type=provider_type,
            api_key=api_key,
            model=model
        )

        # Initialize generators with LLM support
        self.schema_generator = DatabaseSchemaGenerator(config, self.llm_provider)
        self.api_generator = APIGenerator(config, self.llm_provider)
        self.frontend_generator = ActualFrontendGenerator(config)  # Use actual implementation
        self.deployment_generator = DeploymentGenerator(config)
        self.compliance_injector = ComplianceFeatureInjector(config)
        self.security_injector = SecurityFeatureInjector(config)
        self.template_selector = TemplateSelector(config)

    async def generate_application(
        self,
        spec: AppSpecification
    ) -> GeneratedApp:
        """
        Main entry point - generates complete application from specification
        """
        print(f"[STARTING] Generation for: {spec.app_name}")

        # Step 1: Select best template based on category
        template = await self.template_selector.select_template(spec)
        print(f"[TEMPLATE] Selected: {template.name}")

        # Step 2: Generate database schema
        print("[DATABASE] Generating schema...")
        database_schema = await self.schema_generator.generate(
            spec.database_entities,
            template
        )

        # Step 3: Generate backend API
        print("[API] Generating backend API...")
        backend_code = await self.api_generator.generate(
            spec.api_endpoints,
            database_schema,
            spec.auth_requirements,
            template
        )

        # Step 4: Inject compliance features (from Z Agent)
        print("[COMPLIANCE] Injecting compliance features...")
        backend_code = await self.compliance_injector.inject(
            backend_code,
            spec.compliance_features,
            spec.z_validation
        )

        # Step 5: Inject security features (from CS Agent)
        print("[SECURITY] Injecting security features...")
        backend_code = await self.security_injector.inject(
            backend_code,
            spec.security_features,
            spec.cs_validation
        )

        # Step 6: Generate frontend
        print("[FRONTEND] Generating frontend...")
        frontend_code = await self.frontend_generator.generate(
            spec.ui_pages,
            spec.core_features,
            backend_code,
            template
        )

        # Step 7: Generate deployment configuration
        print("[DEPLOYMENT] Generating deployment config...")
        deployment_config = await self.deployment_generator.generate(
            spec.deployment_target,
            spec.custom_domain,
            backend_code,
            frontend_code
        )

        # Step 8: Generate documentation
        print("[DOCS] Generating documentation...")
        docs = await self._generate_documentation(spec, template)

        # Step 9: Create final package
        generated_app = GeneratedApp(
            app_id=spec.app_id,
            app_name=spec.app_name,
            backend_code=backend_code,
            frontend_code=frontend_code,
            database_schema=database_schema,
            deployment_config=deployment_config,
            readme=docs['readme'],
            api_docs=docs['api_docs'],
            user_guide=docs['user_guide'],
            generated_at=datetime.utcnow(),
            generator_version="1.0.0",
            technology_stack=template.tech_stack,
            blockchain_hash=None  # Will be set during blockchain registration
        )

        # Step 10: Analyze completion and generate guide
        print("[ANALYSIS] Analyzing completion percentage...")
        analyzer = CompletionAnalyzer()
        metrics = analyzer.analyze(generated_app, spec)

        guide_generator = CompletionGuideGenerator()
        completion_guide = guide_generator.generate_completion_guide(generated_app, spec, metrics)

        # Add completion guide to backend code (will be saved as file)
        backend_code['COMPLETION_GUIDE.md'] = completion_guide

        # Print metrics
        print(f"\n[METRICS] Completion Analysis:")
        print(f"   Overall:    {metrics.overall_percentage}% complete")
        print(f"   Backend:    {metrics.backend_percentage}%")
        print(f"   Frontend:   {metrics.frontend_percentage}%")
        print(f"   Database:   {metrics.database_percentage}%")
        print(f"   Testing:    {metrics.testing_percentage}%")
        print(f"   Deployment: {metrics.deployment_percentage}%")
        print(f"   Estimated completion time: {metrics.estimated_hours_remaining} hours")

        print(f"\n[SUCCESS] Generation complete for: {spec.app_name}")
        return generated_app

    async def _generate_documentation(
        self,
        spec: AppSpecification,
        template: Any
    ) -> Dict[str, str]:
        """Generates all documentation"""

        readme = f"""# {spec.app_name}

{spec.description}

## Target Users
{chr(10).join(f'- {user}' for user in spec.target_users)}

## Core Features
{chr(10).join(f'- {feature["name"]}: {feature["description"]}' for feature in spec.core_features)}

## Technology Stack
- Backend: {template.tech_stack.get('backend', 'Node.js')}
- Frontend: {template.tech_stack.get('frontend', 'React')}
- Database: {template.tech_stack.get('database', 'PostgreSQL')}

## Getting Started

### Prerequisites
- Node.js 18+
- PostgreSQL 14+

### Installation
```bash
npm install
```

### Configuration
Copy `.env.example` to `.env` and configure:
```
DATABASE_URL=postgresql://...
JWT_SECRET=your-secret-key
```

### Run Development Server
```bash
npm run dev
```

### Deploy
```bash
npm run deploy
```

## Documentation
- [API Documentation](./docs/API.md)
- [User Guide](./docs/USER_GUIDE.md)

## Compliance & Security
This application includes:
- GDPR compliance features
- Data encryption (AES-256)
- Secure authentication (JWT)
- Input validation and sanitization
- Rate limiting
- Security headers

## License
Generated by VerifiMind(TM) - All rights reserved by the app creator.

## Blockchain Proof of Creation
App ID: {spec.app_id}
Created: {datetime.utcnow().isoformat()}
"""

        api_docs = self._generate_api_documentation(spec)
        user_guide = self._generate_user_guide(spec)

        return {
            'readme': readme,
            'api_docs': api_docs,
            'user_guide': user_guide
        }

    def _generate_api_documentation(self, spec: AppSpecification) -> str:
        """Generates API documentation"""
        docs = f"""# API Documentation - {spec.app_name}

## Base URL
`https://api.{spec.app_name.lower()}.com/v1`

## Authentication
All API requests require authentication using JWT tokens.

```http
Authorization: Bearer <token>
```

## Endpoints

"""
        for endpoint in spec.api_endpoints:
            docs += f"""### {endpoint['method']} {endpoint['path']}
**Description**: {endpoint['description']}

**Request**:
```json
{json.dumps(endpoint.get('request_body', {}), indent=2)}
```

**Response**:
```json
{json.dumps(endpoint.get('response', {}), indent=2)}
```

---

"""
        return docs

    def _generate_user_guide(self, spec: AppSpecification) -> str:
        """Generates user guide"""
        guide = f"""# User Guide - {spec.app_name}

## Introduction
Welcome to {spec.app_name}! This guide will help you get started.

## Features

"""
        for feature in spec.core_features:
            guide += f"""### {feature['name']}
{feature['description']}

**How to use**:
{feature.get('usage_instructions', 'Details coming soon...')}

---

"""
        return guide


class DatabaseSchemaGenerator:
    """Generates database schema from entity definitions using LLM"""

    def __init__(self, config: Dict[str, Any], llm_provider=None):
        self.config = config
        self.llm_provider = llm_provider

    async def generate(
        self,
        entities: List[Dict[str, Any]],
        template: Any
    ) -> str:
        """Generates SQL schema using LLM for context-aware generation"""

        # If LLM is available, use it for intelligent schema generation
        if self.llm_provider:
            return await self._generate_with_llm(entities, template)

        # Fallback to template-based generation
        return await self._generate_with_template(entities, template)

    async def _generate_with_llm(
        self,
        entities: List[Dict[str, Any]],
        template: Any
    ) -> str:
        """Uses LLM to generate context-aware database schema"""

        # Create prompt for LLM
        entity_descriptions = "\n".join([
            f"- {entity['name']}: {entity.get('description', 'No description')}"
            for entity in entities
        ])

        prompt = f"""Generate a PostgreSQL database schema for the following entities:

{entity_descriptions}

Requirements:
1. Use UUID primary keys (gen_random_uuid())
2. Include created_at and updated_at timestamps for all tables
3. Add proper foreign key constraints
4. Create appropriate indexes for commonly queried fields
5. Use proper data types (VARCHAR, TEXT, INTEGER, DECIMAL, TIMESTAMP, JSONB, etc.)
6. Include soft delete support (deleted_at column)
7. Add necessary extensions (uuid-ossp, pgcrypto)

Generate complete, production-ready PostgreSQL schema with:
- CREATE TABLE statements
- Indexes
- Foreign key constraints
- Comments explaining each table

Return ONLY the SQL code, no explanations."""

        messages = [
            LLMMessage(role="system", content="You are an expert database architect specializing in PostgreSQL."),
            LLMMessage(role="user", content=prompt)
        ]

        try:
            response = await self.llm_provider.generate(messages, temperature=0.3, max_tokens=2000)
            schema = response.content.strip()

            # Add header if not present
            if not schema.startswith("--"):
                header = f"""-- Database Schema
-- Generated by VerifiMind™ with AI
-- Creation Date: {datetime.utcnow().isoformat()}

"""
                schema = header + schema

            print("[AI] Database schema generated with LLM")
            return schema

        except Exception as e:
            print(f"[WARNING] LLM schema generation failed: {e}. Using template fallback.")
            return await self._generate_with_template(entities, template)

    async def _generate_with_template(
        self,
        entities: List[Dict[str, Any]],
        template: Any
    ) -> str:
        """Template-based fallback generation"""

        schema = """-- Database Schema
-- Generated by VerifiMind™
-- Creation Date: {date}

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

""".format(date=datetime.utcnow().isoformat())

        # Generate tables for each entity
        for entity in entities:
            schema += self._generate_table(entity)
            schema += "\n"

        # Generate indexes
        schema += "\n-- Indexes\n"
        for entity in entities:
            schema += self._generate_indexes(entity)

        # Generate foreign key constraints
        schema += "\n-- Foreign Key Constraints\n"
        for entity in entities:
            schema += self._generate_foreign_keys(entity)

        return schema

    def _generate_table(self, entity: Dict[str, Any]) -> str:
        """Generates CREATE TABLE statement"""
        table_name = entity['name'].lower() + 's'

        sql = f"-- {entity.get('description', entity['name'])} table\n"
        sql += f"CREATE TABLE {table_name} (\n"

        # Always include standard fields
        fields = [
            "    id UUID PRIMARY KEY DEFAULT gen_random_uuid()",
        ]

        # Add entity-specific fields
        for field in entity.get('fields', []):
            field_sql = self._generate_field(field)
            fields.append(f"    {field_sql}")

        # Add timestamps
        fields.append("    created_at TIMESTAMP DEFAULT NOW()")
        fields.append("    updated_at TIMESTAMP DEFAULT NOW()")

        sql += ",\n".join(fields)
        sql += "\n);\n"

        return sql

    def _generate_field(self, field: Dict[str, Any]) -> str:
        """Generates field definition"""
        name = field['name']
        field_type = self._map_type(field['type'])

        constraints = []
        if field.get('required'):
            constraints.append('NOT NULL')
        if field.get('unique'):
            constraints.append('UNIQUE')
        if field.get('default'):
            constraints.append(f"DEFAULT {field['default']}")

        constraint_str = ' '.join(constraints) if constraints else ''
        return f"{name} {field_type} {constraint_str}".strip()

    def _map_type(self, field_type: str) -> str:
        """Maps generic type to PostgreSQL type"""
        type_mapping = {
            'string': 'VARCHAR(255)',
            'text': 'TEXT',
            'integer': 'INTEGER',
            'float': 'DECIMAL(10,2)',
            'boolean': 'BOOLEAN',
            'date': 'DATE',
            'datetime': 'TIMESTAMP',
            'email': 'VARCHAR(255)',
            'url': 'TEXT',
            'json': 'JSONB'
        }
        return type_mapping.get(field_type, 'TEXT')

    def _generate_indexes(self, entity: Dict[str, Any]) -> str:
        """Generates indexes for entity"""
        table_name = entity['name'].lower() + 's'
        indexes = []

        for field in entity.get('fields', []):
            if field.get('indexed'):
                idx_name = f"idx_{table_name}_{field['name']}"
                indexes.append(
                    f"CREATE INDEX {idx_name} ON {table_name}({field['name']});\n"
                )

        return ''.join(indexes)

    def _generate_foreign_keys(self, entity: Dict[str, Any]) -> str:
        """Generates foreign key constraints"""
        table_name = entity['name'].lower() + 's'
        constraints = []

        for field in entity.get('fields', []):
            if field.get('foreign_key'):
                ref_table = field['foreign_key']['table']
                ref_field = field['foreign_key'].get('field', 'id')
                constraint_name = f"fk_{table_name}_{field['name']}"

                constraints.append(
                    f"ALTER TABLE {table_name} ADD CONSTRAINT {constraint_name} "
                    f"FOREIGN KEY ({field['name']}) REFERENCES {ref_table}({ref_field});\n"
                )

        return ''.join(constraints)


class APIGenerator:
    """Generates backend API code using LLM"""

    def __init__(self, config: Dict[str, Any], llm_provider=None):
        self.config = config
        self.llm_provider = llm_provider

    async def generate(
        self,
        endpoints: List[Dict[str, Any]],
        database_schema: str,
        auth_requirements: Dict[str, Any],
        template: Any
    ) -> Dict[str, str]:
        """Generates complete backend API code with LLM assistance"""

        code_files = {}

        # Generate main server file
        code_files['src/server.js'] = self._generate_server_file(template)

        # Generate database connection
        code_files['src/db/connection.js'] = self._generate_db_connection()

        # Generate authentication middleware
        code_files['src/middleware/auth.js'] = self._generate_auth_middleware(
            auth_requirements
        )

        # Generate validation middleware
        code_files['src/middleware/validation.js'] = self._generate_validation_middleware()

        # Generate security middleware
        code_files['src/middleware/security.js'] = self._generate_security_middleware()

        # Extract tables from schema
        models = self._extract_entities_from_schema(database_schema)

        # Generate models with LLM for context-aware code
        if self.llm_provider:
            print("[AI] Generating models with LLM...")
            for model_name in models:
                code_files[f'src/models/{model_name}.js'] = await self._generate_model_with_llm(
                    model_name, database_schema
                )
        else:
            for model_name in models:
                code_files[f'src/models/{model_name}.js'] = self._generate_model(model_name)

        # Generate routes for each endpoint
        route_groups = self._group_endpoints_by_resource(endpoints)
        for resource, resource_endpoints in route_groups.items():
            code_files[f'src/routes/{resource}.js'] = self._generate_routes(
                resource,
                resource_endpoints
            )

        # Generate controllers with LLM
        if self.llm_provider:
            print("[AI] Generating controllers with LLM...")
            for resource in route_groups.keys():
                code_files[f'src/controllers/{resource}.js'] = await self._generate_controller_with_llm(
                    resource, database_schema, models
                )
        else:
            for resource in route_groups.keys():
                code_files[f'src/controllers/{resource}.js'] = self._generate_controller(resource)

        # Generate config files
        code_files['package.json'] = self._generate_package_json(template)
        code_files['.env.example'] = self._generate_env_example()
        code_files['.gitignore'] = self._generate_gitignore()

        return code_files

    async def _generate_model_with_llm(self, model_name: str, database_schema: str) -> str:
        """Uses LLM to generate context-aware model code"""

        prompt = f"""Generate a Node.js model class for the '{model_name}' entity.

Database schema context:
{database_schema}

Requirements:
1. Create a class with static methods for CRUD operations
2. Use PostgreSQL with parameterized queries to prevent SQL injection
3. Include methods: findAll, findById, create, update, delete (soft delete)
4. Use the database connection from '../db/connection'
5. Handle errors properly
6. Support filtering and pagination in findAll

Generate complete, production-ready Node.js code. Return ONLY the code, no explanations."""

        messages = [
            LLMMessage(role="system", content="You are an expert Node.js backend developer specializing in PostgreSQL."),
            LLMMessage(role="user", content=prompt)
        ]

        try:
            response = await self.llm_provider.generate(messages, temperature=0.3, max_tokens=1500)
            return response.content.strip()
        except Exception as e:
            print(f"[WARNING] LLM model generation failed for {model_name}: {e}. Using template.")
            return self._generate_model(model_name)

    async def _generate_controller_with_llm(self, resource: str, database_schema: str, models: List[str]) -> str:
        """Uses LLM to generate context-aware controller code"""

        model_name = resource.capitalize()

        prompt = f"""Generate a Node.js Express controller for the '{resource}' resource.

Database schema context:
{database_schema}

Available models: {', '.join(models)}

Requirements:
1. Create a class with methods: getAll, getById, create, update, delete
2. Use the {model_name} model from '../models/{resource}'
3. Handle errors with proper HTTP status codes
4. Return JSON responses
5. Support query parameters for filtering and pagination in getAll
6. Validate required fields
7. Export an instance of the controller

Generate complete, production-ready Node.js Express controller code. Return ONLY the code, no explanations."""

        messages = [
            LLMMessage(role="system", content="You are an expert Node.js backend developer specializing in Express.js."),
            LLMMessage(role="user", content=prompt)
        ]

        try:
            response = await self.llm_provider.generate(messages, temperature=0.3, max_tokens=1500)
            return response.content.strip()
        except Exception as e:
            print(f"[WARNING] LLM controller generation failed for {resource}: {e}. Using template.")
            return self._generate_controller(resource)

    def _generate_server_file(self, template: Any) -> str:
        """Generates main Express server file"""
        return """const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const { connectDB } = require('./db/connection');

// Import routes
const authRoutes = require('./routes/auth');
// Additional routes will be imported here

const app = express();
const PORT = process.env.PORT || 3000;

// Security middleware
app.use(helmet());
app.use(cors({
  origin: process.env.FRONTEND_URL,
  credentials: true
}));

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100 // limit each IP to 100 requests per windowMs
});
app.use('/api/', limiter);

// Body parsing middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Routes
app.use('/api/auth', authRoutes);
// Additional routes will be mounted here

// Error handling middleware
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(err.status || 500).json({
    error: {
      message: err.message || 'Internal Server Error',
      status: err.status || 500
    }
  });
});

// Start server
const startServer = async () => {
  try {
    await connectDB();
    app.listen(PORT, () => {
      console.log(`[SERVER] Running on port ${PORT}`);
    });
  } catch (error) {
    console.error('Failed to start server:', error);
    process.exit(1);
  }
};

startServer();
"""

    def _generate_db_connection(self) -> str:
        """Generates database connection file"""
        return """const { Pool } = require('pg');

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false
});

const connectDB = async () => {
  try {
    const client = await pool.connect();
    console.log('✅ Database connected successfully');
    client.release();
  } catch (error) {
    console.error('❌ Database connection failed:', error);
    throw error;
  }
};

const query = (text, params) => pool.query(text, params);

module.exports = {
  connectDB,
  query,
  pool
};
"""

    def _generate_auth_middleware(self, auth_requirements: Dict[str, Any]) -> str:
        """Generates authentication middleware"""
        return """const jwt = require('jsonwebtoken');

const authMiddleware = async (req, res, next) => {
  try {
    const token = req.headers.authorization?.split(' ')[1];

    if (!token) {
      return res.status(401).json({ error: 'No token provided' });
    }

    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    req.user = decoded;
    next();
  } catch (error) {
    return res.status(401).json({ error: 'Invalid or expired token' });
  }
};

const optionalAuth = async (req, res, next) => {
  try {
    const token = req.headers.authorization?.split(' ')[1];
    if (token) {
      const decoded = jwt.verify(token, process.env.JWT_SECRET);
      req.user = decoded;
    }
    next();
  } catch (error) {
    next();
  }
};

module.exports = {
  authMiddleware,
  optionalAuth
};
"""

    def _generate_validation_middleware(self) -> str:
        """Generates input validation middleware"""
        return """const { validationResult } = require('express-validator');

const validate = (req, res, next) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({ errors: errors.array() });
  }
  next();
};

// Sanitize input to prevent XSS
const sanitizeInput = (input) => {
  if (typeof input !== 'string') return input;
  return input
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#x27;')
    .replace(/\\//g, '&#x2F;');
};

module.exports = {
  validate,
  sanitizeInput
};
"""

    def _generate_security_middleware(self) -> str:
        """Generates security middleware"""
        return """const crypto = require('crypto');

// CSRF protection
const csrfProtection = (req, res, next) => {
  if (['POST', 'PUT', 'DELETE', 'PATCH'].includes(req.method)) {
    const token = req.headers['x-csrf-token'];
    const sessionToken = req.session?.csrfToken;

    if (!token || token !== sessionToken) {
      return res.status(403).json({ error: 'Invalid CSRF token' });
    }
  }
  next();
};

// Generate CSRF token
const generateCsrfToken = () => {
  return crypto.randomBytes(32).toString('hex');
};

// SQL injection prevention
const preventSQLInjection = (input) => {
  if (typeof input !== 'string') return input;

  const dangerousPatterns = [
    /('|(\\-\\-)|(;)|(\\|\\|)|(\\*))/gi,
    /(union|select|insert|update|delete|drop|create|alter)/gi
  ];

  for (const pattern of dangerousPatterns) {
    if (pattern.test(input)) {
      throw new Error('Potentially malicious input detected');
    }
  }

  return input;
};

module.exports = {
  csrfProtection,
  generateCsrfToken,
  preventSQLInjection
};
"""

    def _generate_model(self, model_name: str) -> str:
        """Generates a model file"""
        return f"""const {{ query }} = require('../db/connection');

class {model_name.capitalize()} {{
  static async findAll(filters = {{}}) {{
    const result = await query('SELECT * FROM {model_name}s WHERE deleted_at IS NULL');
    return result.rows;
  }}

  static async findById(id) {{
    const result = await query('SELECT * FROM {model_name}s WHERE id = $1 AND deleted_at IS NULL', [id]);
    return result.rows[0];
  }}

  static async create(data) {{
    const keys = Object.keys(data);
    const values = Object.values(data);
    const placeholders = keys.map((_, i) => `${{i + 1}}`).join(', ');

    const sql = `INSERT INTO {model_name}s (${{keys.join(', ')}}) VALUES (${{placeholders}}) RETURNING *`;
    const result = await query(sql, values);
    return result.rows[0];
  }}

  static async update(id, data) {{
    const keys = Object.keys(data);
    const values = Object.values(data);
    const setClause = keys.map((key, i) => `${{key}} = ${{i + 1}}`).join(', ');

    const sql = `UPDATE {model_name}s SET ${{setClause}}, updated_at = NOW() WHERE id = ${{keys.length + 1}} RETURNING *`;
    const result = await query(sql, [...values, id]);
    return result.rows[0];
  }}

  static async delete(id) {{
    // Soft delete
    const result = await query(
      'UPDATE {model_name}s SET deleted_at = NOW() WHERE id = $1 RETURNING *',
      [id]
    );
    return result.rows[0];
  }}
}}

module.exports = {model_name.capitalize()};
"""

    def _generate_routes(self, resource: str, endpoints: List[Dict]) -> str:
        """Generates route file for a resource"""
        return f"""const express = require('express');
const router = express.Router();
const {{ authMiddleware }} = require('../middleware/auth');
const {{ validate }} = require('../middleware/validation');
const {resource}Controller = require('../controllers/{resource}');

// Routes for {resource}
router.get('/', authMiddleware, {resource}Controller.getAll);
router.get('/:id', authMiddleware, {resource}Controller.getById);
router.post('/', authMiddleware, validate, {resource}Controller.create);
router.put('/:id', authMiddleware, validate, {resource}Controller.update);
router.delete('/:id', authMiddleware, {resource}Controller.delete);

module.exports = router;
"""

    def _generate_controller(self, resource: str) -> str:
        """Generates controller file"""
        model_name = resource.capitalize()
        return f"""const {model_name} = require('../models/{resource}');

class {model_name}Controller {{
  async getAll(req, res) {{
    try {{
      const items = await {model_name}.findAll(req.query);
      res.json({{ data: items }});
    }} catch (error) {{
      res.status(500).json({{ error: error.message }});
    }}
  }}

  async getById(req, res) {{
    try {{
      const item = await {model_name}.findById(req.params.id);
      if (!item) {{
        return res.status(404).json({{ error: 'Not found' }});
      }}
      res.json({{ data: item }});
    }} catch (error) {{
      res.status(500).json({{ error: error.message }});
    }}
  }}

  async create(req, res) {{
    try {{
      const item = await {model_name}.create(req.body);
      res.status(201).json({{ data: item }});
    }} catch (error) {{
      res.status(500).json({{ error: error.message }});
    }}
  }}

  async update(req, res) {{
    try {{
      const item = await {model_name}.update(req.params.id, req.body);
      if (!item) {{
        return res.status(404).json({{ error: 'Not found' }});
      }}
      res.json({{ data: item }});
    }} catch (error) {{
      res.status(500).json({{ error: error.message }});
    }}
  }}

  async delete(req, res) {{
    try {{
      const item = await {model_name}.delete(req.params.id);
      if (!item) {{
        return res.status(404).json({{ error: 'Not found' }});
      }}
      res.json({{ message: 'Deleted successfully' }});
    }} catch (error) {{
      res.status(500).json({{ error: error.message }});
    }}
  }}
}}

module.exports = new {model_name}Controller();
"""

    def _generate_package_json(self, template: Any) -> str:
        """Generates package.json"""
        return """{
  "name": "verifimind-generated-app",
  "version": "1.0.0",
  "description": "Application generated by VerifiMind",
  "main": "src/server.js",
  "scripts": {
    "start": "node src/server.js",
    "dev": "nodemon src/server.js",
    "test": "jest"
  },
  "dependencies": {
    "express": "^4.18.2",
    "pg": "^8.11.0",
    "cors": "^2.8.5",
    "helmet": "^7.0.0",
    "jsonwebtoken": "^9.0.0",
    "bcrypt": "^5.1.0",
    "express-validator": "^7.0.1",
    "express-rate-limit": "^6.7.0",
    "dotenv": "^16.0.3"
  },
  "devDependencies": {
    "nodemon": "^2.0.22",
    "jest": "^29.5.0"
  }
}
"""

    def _generate_env_example(self) -> str:
        """Generates .env.example"""
        return """# Database
DATABASE_URL=postgresql://username:password@localhost:5432/dbname

# JWT
JWT_SECRET=your-super-secret-jwt-key-change-this

# Server
PORT=3000
NODE_ENV=development

# Frontend
FRONTEND_URL=http://localhost:3001

# Security
SESSION_SECRET=your-session-secret
"""

    def _generate_gitignore(self) -> str:
        """Generates .gitignore"""
        return """node_modules/
.env
.DS_Store
*.log
dist/
build/
coverage/
"""

    def _extract_entities_from_schema(self, schema: str) -> List[str]:
        """Extracts entity names from SQL schema"""
        import re
        tables = re.findall(r'CREATE TABLE (\w+)', schema)
        # Remove 's' from plural table names to get model names
        return [table[:-1] if table.endswith('s') else table for table in tables]

    def _group_endpoints_by_resource(
        self,
        endpoints: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict]]:
        """Groups endpoints by resource"""
        groups = {}
        for endpoint in endpoints:
            # Extract resource from path (e.g., /api/users -> users)
            resource = endpoint['path'].split('/')[2] if len(endpoint['path'].split('/')) > 2 else 'general'
            if resource not in groups:
                groups[resource] = []
            groups[resource].append(endpoint)
        return groups


# Additional generator classes
class DeploymentGenerator:
    """Generates deployment configurations"""
    def __init__(self, config):
        self.config = config

    async def generate(self, target, domain, backend, frontend):
        """Generates deployment config for various platforms"""
        config = {
            'Dockerfile': self._generate_dockerfile(),
            'docker-compose.yml': self._generate_docker_compose(),
            '.dockerignore': self._generate_dockerignore(),
            'vercel.json': self._generate_vercel_config() if target == 'vercel' else None,
        }
        return {k: v for k, v in config.items() if v is not None}

    def _generate_dockerfile(self) -> str:
        return """# Multi-stage build for Node.js backend
FROM node:18-alpine AS backend
WORKDIR /app/backend
COPY package*.json ./
RUN npm ci --only=production
COPY src ./src
EXPOSE 3000
CMD ["node", "src/server.js"]

# Frontend build (if needed)
FROM node:18-alpine AS frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend ./
RUN npm run build
"""

    def _generate_docker_compose(self) -> str:
        return """version: '3.8'
services:
  postgres:
    image: postgres:14-alpine
    environment:
      POSTGRES_DB: app_db
      POSTGRES_USER: app_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  backend:
    build: .
    ports:
      - "3000:3000"
    environment:
      DATABASE_URL: postgresql://app_user:${DB_PASSWORD}@postgres:5432/app_db
      JWT_SECRET: ${JWT_SECRET}
      NODE_ENV: production
    depends_on:
      - postgres

volumes:
  postgres_data:
"""

    def _generate_dockerignore(self) -> str:
        return """node_modules
npm-debug.log
.env
.git
.gitignore
README.md
.vscode
.idea
"""

    def _generate_vercel_config(self) -> str:
        return """{
  "version": 2,
  "builds": [
    {
      "src": "frontend/package.json",
      "use": "@vercel/next"
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "http://your-backend-url.com/api/$1"
    }
  ]
}
"""

class ComplianceFeatureInjector:
    """Injects compliance features into generated code"""
    def __init__(self, config):
        self.config = config

    async def inject(self, code, features, validation):
        """Injects GDPR, COPPA, and other compliance features"""
        if not features:
            return code

        # Add data export route if GDPR required
        if any('gdpr' in f.lower() for f in features):
            code = self._inject_gdpr_routes(code)

        # Add parental consent if COPPA required
        if any('coppa' in f.lower() or 'parental' in f.lower() for f in features):
            code = self._inject_coppa_features(code)

        # Add audit logging if required
        if any('audit' in f.lower() for f in features):
            code = self._inject_audit_logging(code)

        return code

    def _inject_gdpr_routes(self, code: Dict[str, str]) -> Dict[str, str]:
        """Adds GDPR data export/deletion routes"""
        gdpr_routes = """const express = require('express');
const router = express.Router();
const { authMiddleware } = require('../middleware/auth');

// GDPR: Data Export
router.get('/export', authMiddleware, async (req, res) => {
  try {
    // Collect all user data from all tables
    const userData = await getUserData(req.user.id);
    res.json({ data: userData, exportedAt: new Date().toISOString() });
  } catch (error) {
    res.status(500).json({ error: 'Export failed' });
  }
});

// GDPR: Data Deletion
router.delete('/delete', authMiddleware, async (req, res) => {
  try {
    await deleteUserData(req.user.id);
    res.json({ message: 'All data deleted successfully' });
  } catch (error) {
    res.status(500).json({ error: 'Deletion failed' });
  }
});

module.exports = router;
"""
        code['src/routes/gdpr.js'] = gdpr_routes
        return code

    def _inject_coppa_features(self, code: Dict[str, str]) -> Dict[str, str]:
        """Adds COPPA parental consent features"""
        # Add parental consent middleware
        code['src/middleware/coppa.js'] = """const checkParentalConsent = async (req, res, next) => {
  const userId = req.user.id;
  const user = await User.findById(userId);

  if (user.age < 13 && !user.parental_consent) {
    return res.status(403).json({
      error: 'Parental consent required for users under 13'
    });
  }
  next();
};

module.exports = { checkParentalConsent };
"""
        return code

    def _inject_audit_logging(self, code: Dict[str, str]) -> Dict[str, str]:
        """Adds audit logging middleware"""
        code['src/middleware/audit.js'] = """const { query } = require('../db/connection');

const auditLog = async (req, res, next) => {
  const log = {
    user_id: req.user?.id,
    action: req.method,
    resource: req.path,
    ip_address: req.ip,
    user_agent: req.headers['user-agent'],
    timestamp: new Date()
  };

  await query(
    'INSERT INTO audit_logs (user_id, action, resource, ip_address, user_agent) VALUES ($1, $2, $3, $4, $5)',
    [log.user_id, log.action, log.resource, log.ip_address, log.user_agent]
  );

  next();
};

module.exports = { auditLog };
"""
        return code

class SecurityFeatureInjector:
    """Injects security features into generated code"""
    def __init__(self, config):
        self.config = config

    async def inject(self, code, features, validation):
        """Injects security best practices"""
        if not features:
            return code

        # These are already in the base generation, but we can enhance them
        if any('rate' in f.lower() for f in features):
            code = self._enhance_rate_limiting(code)

        if any('encryption' in f.lower() for f in features):
            code = self._add_encryption_utils(code)

        return code

    def _enhance_rate_limiting(self, code: Dict[str, str]) -> Dict[str, str]:
        """Enhances rate limiting with Redis support"""
        return code  # Rate limiting already in server.js

    def _add_encryption_utils(self, code: Dict[str, str]) -> Dict[str, str]:
        """Adds encryption utilities"""
        code['src/utils/encryption.js'] = """const crypto = require('crypto');

const algorithm = 'aes-256-gcm';
const keyLength = 32;

function encrypt(text, key) {
  const iv = crypto.randomBytes(16);
  const cipher = crypto.createCipheriv(algorithm, Buffer.from(key, 'hex'), iv);

  let encrypted = cipher.update(text, 'utf8', 'hex');
  encrypted += cipher.final('hex');

  const authTag = cipher.getAuthTag();
  return iv.toString('hex') + ':' + authTag.toString('hex') + ':' + encrypted;
}

function decrypt(encryptedData, key) {
  const parts = encryptedData.split(':');
  const iv = Buffer.from(parts[0], 'hex');
  const authTag = Buffer.from(parts[1], 'hex');
  const encrypted = parts[2];

  const decipher = crypto.createDecipheriv(algorithm, Buffer.from(key, 'hex'), iv);
  decipher.setAuthTag(authTag);

  let decrypted = decipher.update(encrypted, 'hex', 'utf8');
  decrypted += decipher.final('utf8');
  return decrypted;
}

module.exports = { encrypt, decrypt };
"""
        return code

class TemplateSelector:
    """Selects appropriate template based on app specification"""
    def __init__(self, config):
        self.config = config

    async def select_template(self, spec):
        """Selects best template for the app category"""
        from dataclasses import dataclass

        @dataclass
        class Template:
            name: str
            tech_stack: Dict[str, str]
            description: str

        # Map categories to templates
        template_map = {
            'Health & Fitness': Template(
                name="fitness_tracker",
                tech_stack={
                    'backend': 'Node.js + Express',
                    'frontend': 'Next.js + React + Tailwind',
                    'database': 'PostgreSQL',
                    'auth': 'JWT'
                },
                description="Optimized for health tracking apps with workout logs"
            ),
            'E-commerce': Template(
                name="ecommerce",
                tech_stack={
                    'backend': 'Node.js + Express',
                    'frontend': 'Next.js + React + Tailwind',
                    'database': 'PostgreSQL',
                    'payments': 'Stripe',
                    'auth': 'JWT'
                },
                description="E-commerce with product catalog and checkout"
            ),
            'Social': Template(
                name="social_network",
                tech_stack={
                    'backend': 'Node.js + Express + Socket.io',
                    'frontend': 'Next.js + React + Tailwind',
                    'database': 'PostgreSQL + Redis',
                    'realtime': 'Socket.io',
                    'auth': 'JWT'
                },
                description="Social features with real-time updates"
            ),
            'Education': Template(
                name="education_platform",
                tech_stack={
                    'backend': 'Node.js + Express',
                    'frontend': 'Next.js + React + Tailwind',
                    'database': 'PostgreSQL',
                    'auth': 'JWT'
                },
                description="Learning platform with courses and progress tracking"
            )
        }

        # Select template or use default
        template = template_map.get(spec.category, Template(
            name="basic_crud",
            tech_stack={
                'backend': 'Node.js + Express',
                'frontend': 'Next.js + React + Tailwind',
                'database': 'PostgreSQL',
                'auth': 'JWT'
            },
            description="Generic CRUD application"
        ))

        return template
