"""
Template Registry for VerifiMind-PEAS v0.4.0
=============================================

Singleton registry managing all prompt templates, including:
- Built-in library templates (loaded from YAML)
- Custom user-defined templates
- Template lookup and filtering

Author: Alton Lee
Version: 0.4.0
"""

import logging
import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from threading import Lock

import yaml

from .models import (
    PromptTemplate,
    TemplateVariable,
    TemplateLibraryEntry,
    GenesisPhase,
)

logger = logging.getLogger(__name__)


class TemplateRegistry:
    """
    Singleton registry for managing all prompt templates.

    Provides centralized access to:
    - Built-in library templates (loaded from YAML)
    - Custom user-defined templates
    - Template filtering by agent, category, tags
    """

    _instance: Optional['TemplateRegistry'] = None
    _lock: Lock = Lock()

    def __new__(cls) -> 'TemplateRegistry':
        """Singleton pattern implementation."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the registry (only runs once due to singleton)."""
        if self._initialized:
            return

        self._templates: Dict[str, PromptTemplate] = {}
        self._libraries: Dict[str, TemplateLibraryEntry] = {}
        self._custom_templates: Dict[str, PromptTemplate] = {}
        self._library_path = Path(__file__).parent / "library"
        self._initialized = True

        # Load built-in templates on initialization
        self._load_builtin_templates()

    def _load_builtin_templates(self) -> None:
        """Load all built-in templates from library YAML files."""
        if not self._library_path.exists():
            logger.warning(f"Library path does not exist: {self._library_path}")
            return

        for yaml_file in self._library_path.glob("*.yaml"):
            try:
                self._load_library_file(yaml_file)
            except Exception as e:
                logger.error(f"Failed to load library {yaml_file}: {e}")

    def _load_library_file(self, file_path: Path) -> None:
        """Load a single library YAML file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        if not data:
            return

        # Extract library metadata
        library_id = data.get('library_id', file_path.stem)
        library_entry = TemplateLibraryEntry(
            library_id=library_id,
            name=data.get('name', library_id),
            description=data.get('description', ''),
            agent_id=data.get('agent_id', 'all'),
            genesis_phase=data.get('genesis_phase'),
            category=data.get('category', 'general'),
            version=data.get('version', '1.0.0'),
            file_path=str(file_path),
            templates=[]
        )

        # Load templates from the file
        templates_data = data.get('templates', [])
        for template_data in templates_data:
            try:
                template = self._parse_template_data(template_data, library_entry)
                self._templates[template.template_id] = template
                library_entry.templates.append(template.template_id)
                logger.debug(f"Loaded template: {template.template_id}")
            except Exception as e:
                logger.error(f"Failed to parse template in {file_path}: {e}")

        self._libraries[library_id] = library_entry
        logger.info(f"Loaded library: {library_id} with {len(library_entry.templates)} templates")

    def _parse_template_data(
        self,
        data: Dict[str, Any],
        library: TemplateLibraryEntry
    ) -> PromptTemplate:
        """Parse template data from YAML into PromptTemplate model."""
        # Parse variables
        variables = []
        for var_data in data.get('variables', []):
            var = TemplateVariable(
                name=var_data.get('name'),
                description=var_data.get('description', ''),
                type_hint=var_data.get('type_hint', 'str'),
                required=var_data.get('required', True),
                default=var_data.get('default'),
                examples=var_data.get('examples'),
                validation_pattern=var_data.get('validation_pattern')
            )
            variables.append(var)

        # Build tags (include library genesis phase if not already present)
        tags = data.get('tags', [])
        if library.genesis_phase and library.genesis_phase not in tags:
            tags.append(library.genesis_phase)

        # Create template
        template = PromptTemplate(
            template_id=data.get('template_id'),
            name=data.get('name'),
            agent_id=data.get('agent_id', library.agent_id),
            content=data.get('content', ''),
            variables=variables,
            version=data.get('version', '1.0.0'),
            category=data.get('category', library.category),
            tags=tags,
            changelog=data.get('changelog', []),
            description=data.get('description'),
            author=data.get('author'),
            compatible_providers=data.get('compatible_providers', [
                "gemini", "openai", "anthropic", "groq", "mistral", "ollama", "mock"
            ]),
            min_context_length=data.get('min_context_length', 4096),
            recommended_temperature=data.get('recommended_temperature', 0.7),
            recommended_max_tokens=data.get('recommended_max_tokens', 4096)
        )

        return template

    def get_template(self, template_id: str) -> Optional[PromptTemplate]:
        """
        Get a template by ID.

        Args:
            template_id: Unique template identifier

        Returns:
            PromptTemplate if found, None otherwise
        """
        # Check built-in templates first
        if template_id in self._templates:
            return self._templates[template_id]

        # Check custom templates
        if template_id in self._custom_templates:
            return self._custom_templates[template_id]

        return None

    def list_templates(
        self,
        agent_id: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        include_custom: bool = True
    ) -> List[PromptTemplate]:
        """
        List templates with optional filtering.

        Args:
            agent_id: Filter by agent (X, Z, CS, all)
            category: Filter by category
            tags: Filter by tags (must have ALL specified tags)
            include_custom: Include user-defined templates

        Returns:
            List of matching templates
        """
        # Start with all templates
        all_templates = list(self._templates.values())
        if include_custom:
            all_templates.extend(self._custom_templates.values())

        # Filter by agent_id
        if agent_id:
            agent_id_upper = agent_id.upper()
            all_templates = [
                t for t in all_templates
                if t.agent_id == agent_id_upper or t.agent_id == 'ALL'
            ]

        # Filter by category
        if category:
            all_templates = [
                t for t in all_templates
                if t.category.lower() == category.lower()
            ]

        # Filter by tags (must have ALL specified tags)
        if tags:
            tags_lower = [tag.lower() for tag in tags]
            all_templates = [
                t for t in all_templates
                if all(tag.lower() in [tt.lower() for tt in t.tags] for tag in tags_lower)
            ]

        return all_templates

    def list_libraries(self) -> List[TemplateLibraryEntry]:
        """Get all registered template libraries."""
        return list(self._libraries.values())

    def get_library(self, library_id: str) -> Optional[TemplateLibraryEntry]:
        """
        Get a library by ID.

        Args:
            library_id: Unique library identifier

        Returns:
            TemplateLibraryEntry if found, None otherwise
        """
        return self._libraries.get(library_id)

    def get_library_templates(self, library_id: str) -> List[PromptTemplate]:
        """
        Get all templates from a specific library.

        Args:
            library_id: Library identifier

        Returns:
            List of templates in the library
        """
        library = self.get_library(library_id)
        if not library:
            return []

        templates = []
        for template_id in library.templates:
            template = self.get_template(template_id)
            if template:
                templates.append(template)

        return templates

    def register_custom_template(
        self,
        name: str,
        agent_id: str,
        content: str,
        variables: Optional[List[Dict[str, Any]]] = None,
        category: str = "custom",
        tags: Optional[List[str]] = None,
        description: Optional[str] = None,
        template_id: Optional[str] = None
    ) -> PromptTemplate:
        """
        Register a new custom template.

        Args:
            name: Template display name
            agent_id: Target agent (X, Z, CS, all)
            content: Template content with {variable} placeholders
            variables: List of variable definitions
            category: Template category
            tags: Template tags
            description: Template description
            template_id: Custom template ID (auto-generated if not provided)

        Returns:
            The registered PromptTemplate

        Raises:
            ValueError: If template_id already exists
        """
        # Generate template_id if not provided
        if not template_id:
            import hashlib
            import time
            hash_input = f"{name}-{agent_id}-{time.time()}"
            template_id = f"custom-{hashlib.sha256(hash_input.encode()).hexdigest()[:12]}"

        # Check for duplicate
        if template_id in self._templates or template_id in self._custom_templates:
            raise ValueError(f"Template ID already exists: {template_id}")

        # Parse variables
        parsed_vars = []
        if variables:
            for var_data in variables:
                var = TemplateVariable(
                    name=var_data.get('name'),
                    description=var_data.get('description', ''),
                    type_hint=var_data.get('type_hint', 'str'),
                    required=var_data.get('required', True),
                    default=var_data.get('default'),
                    examples=var_data.get('examples')
                )
                parsed_vars.append(var)

        # Create template
        template = PromptTemplate(
            template_id=template_id,
            name=name,
            agent_id=agent_id,
            content=content,
            variables=parsed_vars,
            category=category,
            tags=tags or ["custom"],
            description=description,
            changelog=[f"v1.0.0 - Initial version"]
        )

        # Register
        self._custom_templates[template_id] = template
        logger.info(f"Registered custom template: {template_id}")

        return template

    def unregister_custom_template(self, template_id: str) -> bool:
        """
        Unregister a custom template.

        Args:
            template_id: Template to unregister

        Returns:
            True if template was removed, False if not found
        """
        if template_id in self._custom_templates:
            del self._custom_templates[template_id]
            logger.info(f"Unregistered custom template: {template_id}")
            return True
        return False

    def get_templates_by_genesis_phase(
        self,
        phase: GenesisPhase
    ) -> List[PromptTemplate]:
        """
        Get templates aligned with a specific Genesis phase.

        Args:
            phase: Genesis methodology phase

        Returns:
            List of templates for that phase
        """
        return self.list_templates(tags=[phase.value])

    def get_agent_default_template(self, agent_id: str) -> Optional[PromptTemplate]:
        """
        Get the default template for an agent.

        Args:
            agent_id: Agent identifier (X, Z, CS)

        Returns:
            Default template for the agent, or None
        """
        # Look for templates with 'default' tag for this agent
        templates = self.list_templates(agent_id=agent_id, tags=['default'])
        if templates:
            return templates[0]

        # Fall back to first template for this agent
        templates = self.list_templates(agent_id=agent_id)
        return templates[0] if templates else None

    def reload_libraries(self) -> None:
        """Reload all library templates from YAML files."""
        self._templates.clear()
        self._libraries.clear()
        self._load_builtin_templates()
        logger.info("Reloaded all library templates")

    def get_statistics(self) -> Dict[str, Any]:
        """Get registry statistics."""
        return {
            "total_templates": len(self._templates) + len(self._custom_templates),
            "builtin_templates": len(self._templates),
            "custom_templates": len(self._custom_templates),
            "libraries": len(self._libraries),
            "templates_by_agent": {
                "X": len(self.list_templates(agent_id="X", include_custom=False)),
                "Z": len(self.list_templates(agent_id="Z", include_custom=False)),
                "CS": len(self.list_templates(agent_id="CS", include_custom=False)),
                "all": len(self.list_templates(agent_id="all", include_custom=False)),
            },
            "templates_by_phase": {
                phase.value: len(self.get_templates_by_genesis_phase(phase))
                for phase in GenesisPhase
            }
        }


# Global singleton instance
_registry: Optional[TemplateRegistry] = None


def get_registry() -> TemplateRegistry:
    """Get the global template registry instance."""
    global _registry
    if _registry is None:
        _registry = TemplateRegistry()
    return _registry
