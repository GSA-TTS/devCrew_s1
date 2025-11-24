"""
Template Engine for Communication Platform.

Manages notification templates with Jinja2 rendering, versioning, validation,
and channel-specific formatting. Supports Slack blocks, HTML email, and custom
channels with PostgreSQL-backed template storage.

Key Features:
    - Jinja2 template rendering with variable substitution
    - Template versioning (v1.0, v1.1, etc.)
    - Template validation (syntax, required variables)
    - Channel-specific formatting (Slack, Email, Teams)
    - PostgreSQL template storage
    - Built-in templates for common scenarios
    - Template catalog with search and preview

Built-in Templates:
    - deployment_complete: Deployment success/failure notifications
    - incident_alert: Critical incident notifications
    - pr_notification: Pull request lifecycle notifications
    - sprint_update: Sprint progress updates
    - postmortem_complete: Postmortem completion notifications
"""

import json
import logging
import re
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import psycopg2
from jinja2 import TemplateSyntaxError, meta
from jinja2.sandbox import SandboxedEnvironment
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class TemplateCategory(str, Enum):
    """Template category enumeration."""

    DEPLOYMENT = "deployment"
    INCIDENT = "incident"
    PR = "pr"
    SPRINT_UPDATE = "sprint_update"
    POSTMORTEM = "postmortem"


class TemplateVersion(BaseModel):
    """Template version model."""

    version: str = Field(..., description="Version string (e.g., v1.0)")
    content: Dict[str, Any] = Field(..., description="Template content by channel")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(default="system")
    change_notes: Optional[str] = Field(None, description="Version change notes")

    @field_validator("version")
    @classmethod
    def validate_version(cls, v: str) -> str:
        """Validate version format."""
        if not re.match(r"^v\d+\.\d+$", v):
            raise ValueError("Version must be in format v1.0, v1.1, etc.")
        return v


class Template(BaseModel):
    """Template model."""

    template_id: str = Field(..., description="Unique template identifier")
    name: str = Field(..., description="Template display name")
    description: str = Field(..., description="Template description")
    category: TemplateCategory = Field(..., description="Template category")
    content: Dict[str, Any] = Field(..., description="Template content by channel")
    variables: List[str] = Field(
        default_factory=list, description="Required template variables"
    )
    versions: List[TemplateVersion] = Field(
        default_factory=list, description="Template version history"
    )
    current_version: str = Field(default="v1.0", description="Current version")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True, description="Template active status")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )

    @field_validator("template_id")
    @classmethod
    def validate_template_id(cls, v: str) -> str:
        """Validate template ID format."""
        if not re.match(r"^[a-z0-9_]+$", v):
            raise ValueError(
                "Template ID must contain only lowercase letters, "
                "numbers, and underscores"
            )
        return v


class TemplateEngine:
    """
    Main template management class.

    Provides template creation, rendering, validation, versioning, and
    storage management with PostgreSQL backend and Jinja2 rendering.
    """

    def __init__(self, db_config: Dict[str, Any]):
        """
        Initialize template engine.

        Args:
            db_config: PostgreSQL database configuration
        """
        self.db_config = db_config
        self.env = SandboxedEnvironment(
            autoescape=True, trim_blocks=True, lstrip_blocks=True
        )
        self._init_database()
        self._load_builtin_templates()
        logger.info("TemplateEngine initialized successfully")

    def _init_database(self) -> None:
        """Initialize database schema for template storage."""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()

            # Create templates table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS templates (
                    template_id VARCHAR(255) PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    category VARCHAR(50) NOT NULL,
                    content JSONB NOT NULL,
                    variables JSONB DEFAULT '[]',
                    versions JSONB DEFAULT '[]',
                    current_version VARCHAR(20) DEFAULT 'v1.0',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT true,
                    metadata JSONB DEFAULT '{}'
                )
            """
            )

            # Create indexes for efficient querying
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_templates_category
                ON templates(category)
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_templates_active
                ON templates(is_active)
                """
            )

            conn.commit()
            cursor.close()
            conn.close()
            logger.info("Database schema initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    def create_template(
        self, template_id: str, content: Dict[str, Any], category: str, **kwargs
    ) -> str:
        """
        Create a new template.

        Args:
            template_id: Unique template identifier
            content: Template content by channel
                (e.g., {"slack": "...", "email": "..."})
            category: Template category
            **kwargs: Additional template fields
                (name, description, variables, metadata)

        Returns:
            Created template version string

        Raises:
            ValueError: If template validation fails
            psycopg2.Error: If database operation fails
        """
        try:
            # Validate template content
            for channel, template_content in content.items():
                is_valid, errors = self.validate_template(template_content)
                if not is_valid:
                    raise ValueError(
                        f"Template validation failed for {channel}: {errors}"
                    )

            # Extract variables from templates
            all_variables = set()
            for channel, template_content in content.items():
                variables = self._extract_variables(template_content)
                all_variables.update(variables)

            # Create template object
            template = Template(
                template_id=template_id,
                name=kwargs.get("name", template_id.replace("_", " ").title()),
                description=kwargs.get("description", ""),
                category=TemplateCategory(category),
                content=content,
                variables=list(all_variables),
                current_version="v1.0",
            )

            if "metadata" in kwargs:
                template.metadata = kwargs["metadata"]

            # Create initial version
            version = TemplateVersion(
                version="v1.0",
                content=content,
                created_by=kwargs.get("created_by", "system"),
                change_notes="Initial template creation",
            )
            template.versions.append(version)

            # Store in database
            self._store_template(template)

            logger.info(f"Template created: {template_id} v1.0")
            return "v1.0"

        except Exception as e:
            logger.error(f"Failed to create template {template_id}: {e}")
            raise

    def render_template(
        self, template_id: str, data: Dict[str, Any], channel: str
    ) -> str:
        """
        Render template with provided data for specific channel.

        Args:
            template_id: Template identifier
            data: Template variables and values
            channel: Target channel (slack, email, teams, etc.)

        Returns:
            Rendered template string

        Raises:
            ValueError: If template not found or rendering fails
        """
        try:
            # Get template
            template = self.get_template(template_id)
            if not template:
                raise ValueError(f"Template not found: {template_id}")

            if not template.is_active:
                raise ValueError(f"Template is inactive: {template_id}")

            # Get channel-specific content
            if channel not in template.content:
                raise ValueError(
                    f"Channel '{channel}' not supported for template {template_id}"
                )

            template_content = template.content[channel]

            # Validate required variables
            missing_vars = set(template.variables) - set(data.keys())
            if missing_vars:
                logger.warning(
                    f"Missing variables for {template_id}: {missing_vars}, "
                    f"using empty strings"
                )
                # Fill missing variables with empty strings
                for var in missing_vars:
                    data[var] = ""

            # Render template
            jinja_template = self.env.from_string(template_content)
            rendered = jinja_template.render(**data)

            logger.info(f"Template rendered: {template_id} for channel {channel}")
            return rendered

        except TemplateSyntaxError as e:
            logger.error(f"Template syntax error for {template_id}: {e}")
            raise ValueError(f"Template syntax error: {e}")
        except Exception as e:
            logger.error(f"Failed to render template {template_id}: {e}")
            raise

    def validate_template(self, content: str) -> Tuple[bool, List[str]]:
        """
        Validate Jinja2 template syntax.

        Args:
            content: Template content string

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        try:
            # Parse template
            self.env.parse(content)

            # Check for undefined variables (basic check)
            template = self.env.from_string(content)
            # Render with empty dict to catch obvious issues
            template.render()

        except TemplateSyntaxError as e:
            errors.append(f"Syntax error at line {e.lineno}: {e.message}")
        except Exception as e:
            errors.append(f"Template error: {str(e)}")

        is_valid = len(errors) == 0
        return is_valid, errors

    def get_template(
        self, template_id: str, version: Optional[str] = None
    ) -> Optional[Template]:
        """
        Get template by ID and optional version.

        Args:
            template_id: Template identifier
            version: Template version (defaults to current version)

        Returns:
            Template object or None if not found
        """
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT template_id, name, description, category, content,
                       variables, versions, current_version, created_at,
                       updated_at, is_active, metadata
                FROM templates
                WHERE template_id = %s
            """,
                (template_id,),
            )

            row = cursor.fetchone()
            cursor.close()
            conn.close()

            if not row:
                return None

            # Construct template object
            template = Template(
                template_id=row[0],
                name=row[1],
                description=row[2],
                category=TemplateCategory(row[3]),
                content=row[4],
                variables=row[5],
                versions=[TemplateVersion(**v) for v in row[6]],
                current_version=row[7],
                created_at=row[8],
                updated_at=row[9],
                is_active=row[10],
                metadata=row[11],
            )

            # If specific version requested, update content
            if version and version != template.current_version:
                for v in template.versions:
                    if v.version == version:
                        template.content = v.content
                        break

            return template

        except Exception as e:
            logger.error(f"Failed to get template {template_id}: {e}")
            return None

    def list_templates(
        self, category: Optional[str] = None, active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        List templates with optional filtering.

        Args:
            category: Filter by category (optional)
            active_only: Only return active templates

        Returns:
            List of template summaries
        """
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()

            query = """
                SELECT template_id, name, description, category, current_version,
                       created_at, updated_at, is_active,
                       jsonb_array_length(versions) as version_count
                FROM templates
                WHERE 1=1
            """
            params = []

            if category:
                query += " AND category = %s"
                params.append(category)

            if active_only:
                query += " AND is_active = true"

            query += " ORDER BY category, name"

            cursor.execute(query, params)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()

            templates = []
            for row in rows:
                templates.append(
                    {
                        "template_id": row[0],
                        "name": row[1],
                        "description": row[2],
                        "category": row[3],
                        "current_version": row[4],
                        "created_at": row[5].isoformat(),
                        "updated_at": row[6].isoformat(),
                        "is_active": row[7],
                        "version_count": row[8],
                    }
                )

            return templates

        except Exception as e:
            logger.error(f"Failed to list templates: {e}")
            return []

    def preview_template(
        self, template_id: str, sample_data: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Preview template rendering with sample data for all channels.

        Args:
            template_id: Template identifier
            sample_data: Sample data for template variables

        Returns:
            Dictionary mapping channels to rendered content

        Raises:
            ValueError: If template not found
        """
        try:
            template = self.get_template(template_id)
            if not template:
                raise ValueError(f"Template not found: {template_id}")

            previews = {}
            for channel in template.content.keys():
                try:
                    rendered = self.render_template(template_id, sample_data, channel)
                    previews[channel] = rendered
                except Exception as e:
                    previews[channel] = f"Error rendering: {str(e)}"

            return previews

        except Exception as e:
            logger.error(f"Failed to preview template {template_id}: {e}")
            raise

    def update_template(
        self,
        template_id: str,
        content: Dict[str, Any],
        change_notes: str,
        created_by: str = "system",
    ) -> str:
        """
        Update template and create new version.

        Args:
            template_id: Template identifier
            content: New template content
            change_notes: Description of changes
            created_by: User making the change

        Returns:
            New version string

        Raises:
            ValueError: If template not found or validation fails
        """
        try:
            template = self.get_template(template_id)
            if not template:
                raise ValueError(f"Template not found: {template_id}")

            # Validate new content
            for channel, template_content in content.items():
                is_valid, errors = self.validate_template(template_content)
                if not is_valid:
                    raise ValueError(
                        f"Template validation failed for {channel}: {errors}"
                    )

            # Generate new version number
            current_major, current_minor = template.current_version[1:].split(".")
            new_version = f"v{current_major}.{int(current_minor) + 1}"

            # Create new version
            version = TemplateVersion(
                version=new_version,
                content=content,
                created_by=created_by,
                change_notes=change_notes,
            )
            template.versions.append(version)
            template.current_version = new_version
            template.content = content
            template.updated_at = datetime.utcnow()

            # Update variables
            all_variables = set()
            for channel, template_content in content.items():
                variables = self._extract_variables(template_content)
                all_variables.update(variables)
            template.variables = list(all_variables)

            # Store updated template
            self._store_template(template)

            logger.info(f"Template updated: {template_id} -> {new_version}")
            return new_version

        except Exception as e:
            logger.error(f"Failed to update template {template_id}: {e}")
            raise

    def delete_template(self, template_id: str, soft_delete: bool = True) -> bool:
        """
        Delete template (soft or hard delete).

        Args:
            template_id: Template identifier
            soft_delete: If True, mark as inactive; if False, delete from database

        Returns:
            True if successful, False otherwise
        """
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()

            if soft_delete:
                cursor.execute(
                    """
                    UPDATE templates
                    SET is_active = false, updated_at = CURRENT_TIMESTAMP
                    WHERE template_id = %s
                """,
                    (template_id,),
                )
            else:
                cursor.execute(
                    "DELETE FROM templates WHERE template_id = %s", (template_id,)
                )

            conn.commit()
            affected = cursor.rowcount > 0
            cursor.close()
            conn.close()

            if affected:
                logger.info(
                    f"Template {'deactivated' if soft_delete else 'deleted'}: "
                    f"{template_id}"
                )
            return affected

        except Exception as e:
            logger.error(f"Failed to delete template {template_id}: {e}")
            return False

    def _extract_variables(self, template_content: str) -> List[str]:
        """
        Extract variable names from template content.

        Args:
            template_content: Jinja2 template string

        Returns:
            List of variable names
        """
        try:
            ast = self.env.parse(template_content)
            variables = meta.find_undeclared_variables(ast)
            return list(variables)
        except Exception as e:
            logger.warning(f"Failed to extract variables: {e}")
            return []

    def _store_template(self, template: Template) -> None:
        """
        Store template in database (insert or update).

        Args:
            template: Template object to store
        """
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO templates (
                    template_id, name, description, category, content,
                    variables, versions, current_version, created_at,
                    updated_at, is_active, metadata
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (template_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    category = EXCLUDED.category,
                    content = EXCLUDED.content,
                    variables = EXCLUDED.variables,
                    versions = EXCLUDED.versions,
                    current_version = EXCLUDED.current_version,
                    updated_at = EXCLUDED.updated_at,
                    is_active = EXCLUDED.is_active,
                    metadata = EXCLUDED.metadata
            """,
                (
                    template.template_id,
                    template.name,
                    template.description,
                    template.category.value,
                    json.dumps(template.content),
                    json.dumps(template.variables),
                    json.dumps([v.model_dump(mode="json") for v in template.versions]),
                    template.current_version,
                    template.created_at,
                    template.updated_at,
                    template.is_active,
                    json.dumps(template.metadata),
                ),
            )

            conn.commit()
            cursor.close()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to store template {template.template_id}: {e}")
            raise

    def _load_builtin_templates(self) -> None:
        """Load built-in templates into the database."""
        builtin_templates = [
            self._create_deployment_template(),
            self._create_incident_template(),
            self._create_pr_template(),
            self._create_sprint_update_template(),
            self._create_postmortem_template(),
        ]

        for template_data in builtin_templates:
            try:
                # Check if template already exists
                existing = self.get_template(template_data["template_id"])
                if not existing:
                    self.create_template(**template_data)
                    logger.info(
                        f"Loaded built-in template: {template_data['template_id']}"
                    )
            except Exception as e:
                logger.warning(
                    f"Failed to load built-in template "
                    f"{template_data['template_id']}: {e}"
                )

    @staticmethod
    def _create_deployment_template() -> Dict[str, Any]:
        """Create deployment complete template."""
        return {
            "template_id": "deployment_complete",
            "category": "deployment",
            "name": "Deployment Complete",
            "description": "Notification for deployment success or failure",
            "content": {
                "slack": json.dumps(
                    [
                        {
                            "type": "header",
                            "text": {
                                "type": "plain_text",
                                "text": "🚀 Deployment {{ status | upper }}",
                            },
                        },
                        {"type": "divider"},
                        {
                            "type": "section",
                            "fields": [
                                {
                                    "type": "mrkdwn",
                                    "text": "*Environment:*\n{{ environment }}",
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": "*Version:*\n{{ version }}",
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": "*Deployed By:*\n{{ deployed_by }}",
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": "*Duration:*\n{{ duration }}",
                                },
                            ],
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": "*Status:* {{ message }}",
                            },
                        },
                        {
                            "type": "context",
                            "elements": [
                                {
                                    "type": "mrkdwn",
                                    "text": "Deployment ID: {{ deployment_id }} | "
                                    "Timestamp: {{ timestamp }}",
                                }
                            ],
                        },
                    ]
                ),
                "email": """
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <h2 style="color: {% if status == 'success' %}#28a745{% else %}#dc3545{% endif %};">
        🚀 Deployment {{ status | upper }}
    </h2>
    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px;">
        <p><strong>Environment:</strong> {{ environment }}</p>
        <p><strong>Version:</strong> {{ version }}</p>
        <p><strong>Deployed By:</strong> {{ deployed_by }}</p>
        <p><strong>Duration:</strong> {{ duration }}</p>
        <p><strong>Status:</strong> {{ message }}</p>
    </div>
    <p style="color: #6c757d; font-size: 12px; margin-top: 20px;">
        Deployment ID: {{ deployment_id }} | Timestamp: {{ timestamp }}
    </p>
</body>
</html>
                """,
            },
        }

    @staticmethod
    def _create_incident_template() -> Dict[str, Any]:
        """Create incident alert template."""
        return {
            "template_id": "incident_alert",
            "category": "incident",
            "name": "Incident Alert",
            "description": "Critical incident notification",
            "content": {
                "slack": json.dumps(
                    [
                        {
                            "type": "header",
                            "text": {
                                "type": "plain_text",
                                "text": "🚨 INCIDENT: {{ title }}",
                            },
                        },
                        {"type": "divider"},
                        {
                            "type": "section",
                            "fields": [
                                {
                                    "type": "mrkdwn",
                                    "text": "*Severity:*\n{{ severity }}",
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": "*Status:*\n{{ status }}",
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": "*Affected Services:*\n{{ services }}",
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": "*Incident Commander:*\n{{ commander }}",
                                },
                            ],
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": "*Description:*\n{{ description }}",
                            },
                        },
                        {
                            "type": "actions",
                            "elements": [
                                {
                                    "type": "button",
                                    "text": {
                                        "type": "plain_text",
                                        "text": "View Details",
                                    },
                                    "url": "{{ incident_url }}",
                                    "style": "danger",
                                }
                            ],
                        },
                        {
                            "type": "context",
                            "elements": [
                                {
                                    "type": "mrkdwn",
                                    "text": "Incident ID: {{ incident_id }} | "
                                    "Started: {{ start_time }}",
                                }
                            ],
                        },
                    ]
                ),
                "email": """
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; \
margin: 0 auto;">
    <h2 style="color: #dc3545;">🚨 INCIDENT: {{ title }}</h2>
    <div style="background-color: #fff3cd; padding: 15px; \
border-left: 4px solid #ffc107;">
        <p><strong>Severity:</strong> {{ severity }}</p>
        <p><strong>Status:</strong> {{ status }}</p>
        <p><strong>Affected Services:</strong> {{ services }}</p>
        <p><strong>Incident Commander:</strong> {{ commander }}</p>
        <p><strong>Description:</strong></p>
        <p>{{ description }}</p>
    </div>
    <p style="margin-top: 20px;">
        <a href="{{ incident_url }}"
           style="background-color: #dc3545; color: white; \
padding: 10px 20px; text-decoration: none; border-radius: 5px;">
            View Incident Details
        </a>
    </p>
    <p style="color: #6c757d; font-size: 12px; margin-top: 20px;">
        Incident ID: {{ incident_id }} | Started: {{ start_time }}
    </p>
</body>
</html>
                """,
            },
        }

    @staticmethod
    def _create_pr_template() -> Dict[str, Any]:
        """Create pull request notification template."""
        return {
            "template_id": "pr_notification",
            "category": "pr",
            "name": "Pull Request Notification",
            "description": "Pull request lifecycle notifications",
            "content": {
                "slack": json.dumps(
                    [
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": "*{{ action | upper }}: "
                                "Pull Request #{{ pr_number }}*\n{{ pr_title }}",
                            },
                        },
                        {
                            "type": "section",
                            "fields": [
                                {
                                    "type": "mrkdwn",
                                    "text": "*Author:*\n{{ author }}",
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": "*Repository:*\n{{ repository }}",
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": "*Branch:*\n"
                                    "{{ source_branch }} → {{ target_branch }}",
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": "*Changes:*\n"
                                    "+{{ additions }} / -{{ deletions }}",
                                },
                            ],
                        },
                        {
                            "type": "actions",
                            "elements": [
                                {
                                    "type": "button",
                                    "text": {"type": "plain_text", "text": "View PR"},
                                    "url": "{{ pr_url }}",
                                }
                            ],
                        },
                    ]
                ),
                "email": """
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; \
margin: 0 auto;">
    <h2>{{ action | upper }}: Pull Request #{{ pr_number }}</h2>
    <h3>{{ pr_title }}</h3>
    <div style="background-color: #f8f9fa; padding: 15px; \
border-radius: 5px;">
        <p><strong>Author:</strong> {{ author }}</p>
        <p><strong>Repository:</strong> {{ repository }}</p>
        <p><strong>Branch:</strong> {{ source_branch }} → \
{{ target_branch }}</p>
        <p><strong>Changes:</strong> +{{ additions }} / \
-{{ deletions }} lines</p>
    </div>
    <p style="margin-top: 20px;">
        <a href="{{ pr_url }}"
           style="background-color: #007bff; color: white; \
padding: 10px 20px; text-decoration: none; border-radius: 5px;">
            View Pull Request
        </a>
    </p>
</body>
</html>
                """,
            },
        }

    @staticmethod
    def _create_sprint_update_template() -> Dict[str, Any]:
        """Create sprint update template."""
        return {
            "template_id": "sprint_update",
            "category": "sprint_update",
            "name": "Sprint Update",
            "description": "Sprint progress update notification",
            "content": {
                "slack": json.dumps(
                    [
                        {
                            "type": "header",
                            "text": {
                                "type": "plain_text",
                                "text": "📊 Sprint {{ sprint_name }} - "
                                "{{ update_type }}",
                            },
                        },
                        {"type": "divider"},
                        {
                            "type": "section",
                            "fields": [
                                {
                                    "type": "mrkdwn",
                                    "text": "*Progress:*\n"
                                    "{{ completed }}/{{ total }} tasks "
                                    "({{ progress_percent }}%)",
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": "*Days Remaining:*\n{{ days_remaining }}",
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": "*Story Points:*\n"
                                    "{{ completed_points }}/{{ total_points }}",
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": "*Velocity:*\n{{ velocity }}",
                                },
                            ],
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": "*Highlights:*\n{{ highlights }}",
                            },
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": "*Blockers:*\n{{ blockers }}",
                            },
                        },
                    ]
                ),
                "email": """
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; \
margin: 0 auto;">
    <h2>📊 Sprint {{ sprint_name }} - {{ update_type }}</h2>
    <div style="background-color: #e7f3ff; padding: 15px; \
border-radius: 5px; margin-bottom: 15px;">
        <h3>Progress</h3>
        <div style="background-color: #007bff; height: 20px; \
border-radius: 10px; width: {{ progress_percent }}%;">
        </div>
        <p>{{ completed }}/{{ total }} tasks completed \
({{ progress_percent }}%)</p>
        <p><strong>Story Points:</strong> \
{{ completed_points }}/{{ total_points }}</p>
        <p><strong>Velocity:</strong> {{ velocity }}</p>
        <p><strong>Days Remaining:</strong> {{ days_remaining }}</p>
    </div>
    <div style="margin-bottom: 15px;">
        <h3>Highlights</h3>
        <p>{{ highlights }}</p>
    </div>
    <div style="background-color: #fff3cd; padding: 15px; \
border-radius: 5px;">
        <h3>Blockers</h3>
        <p>{{ blockers }}</p>
    </div>
</body>
</html>
                """,
            },
        }

    @staticmethod
    def _create_postmortem_template() -> Dict[str, Any]:
        """Create postmortem complete template."""
        return {
            "template_id": "postmortem_complete",
            "category": "postmortem",
            "name": "Postmortem Complete",
            "description": "Postmortem completion notification",
            "content": {
                "slack": json.dumps(
                    [
                        {
                            "type": "header",
                            "text": {
                                "type": "plain_text",
                                "text": "📋 Postmortem Complete: {{ title }}",
                            },
                        },
                        {"type": "divider"},
                        {
                            "type": "section",
                            "fields": [
                                {
                                    "type": "mrkdwn",
                                    "text": "*Incident Date:*\n{{ incident_date }}",
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": "*Duration:*\n{{ duration }}",
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": "*Impact:*\n{{ impact }}",
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": "*Participants:*\n{{ participants }}",
                                },
                            ],
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": "*Root Cause:*\n{{ root_cause }}",
                            },
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": "*Action Items:*\n{{ action_items }}",
                            },
                        },
                        {
                            "type": "actions",
                            "elements": [
                                {
                                    "type": "button",
                                    "text": {
                                        "type": "plain_text",
                                        "text": "View Full Postmortem",
                                    },
                                    "url": "{{ postmortem_url }}",
                                }
                            ],
                        },
                    ]
                ),
                "email": """
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; \
margin: 0 auto;">
    <h2>📋 Postmortem Complete: {{ title }}</h2>
    <div style="background-color: #f8f9fa; padding: 15px; \
border-radius: 5px; margin-bottom: 15px;">
        <p><strong>Incident Date:</strong> {{ incident_date }}</p>
        <p><strong>Duration:</strong> {{ duration }}</p>
        <p><strong>Impact:</strong> {{ impact }}</p>
        <p><strong>Participants:</strong> {{ participants }}</p>
    </div>
    <div style="margin-bottom: 15px;">
        <h3>Root Cause</h3>
        <p>{{ root_cause }}</p>
    </div>
    <div style="margin-bottom: 15px;">
        <h3>Action Items</h3>
        <p>{{ action_items }}</p>
    </div>
    <p style="margin-top: 20px;">
        <a href="{{ postmortem_url }}"
           style="background-color: #28a745; color: white; \
padding: 10px 20px; text-decoration: none; border-radius: 5px;">
            View Full Postmortem
        </a>
    </p>
</body>
</html>
                """,
            },
        }
