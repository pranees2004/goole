"""
MailBot - Template Engine
Renders HTML email templates using Jinja2.
"""

import os
from jinja2 import Environment, FileSystemLoader, TemplateNotFoundError
from utils import setup_logger


class TemplateEngine:
    """Handles rendering of HTML email templates."""

    def __init__(self, template_dir=None):
        if template_dir is None:
            template_dir = os.path.join(os.path.dirname(__file__), "templates")

        self.template_dir = template_dir
        self.logger = setup_logger("mailbot.template")

        os.makedirs(self.template_dir, exist_ok=True)

        self.env = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=True,
        )

    def render(self, template_name, context=None):
        """
        Render an HTML template with the given context.

        Args:
            template_name (str): Template filename (without .html extension)
            context (dict): Variables to pass to the template

        Returns:
            str: Rendered HTML string
        """
        if context is None:
            context = {}

        try:
            template = self.env.get_template(f"{template_name}.html")
            rendered = template.render(**context)
            self.logger.debug(f"Rendered template: {template_name}")
            return rendered
        except TemplateNotFoundError:
            self.logger.error(f"Template not found: {template_name}.html")
            raise FileNotFoundError(
                f"Template '{template_name}.html' not found in {self.template_dir}"
            )

    def list_templates(self):
        """List all available templates."""
        templates = []
        for f in os.listdir(self.template_dir):
            if f.endswith(".html"):
                templates.append(f.replace(".html", ""))
        return templates

    def create_template(self, name, html_content):
        """
        Create a new email template.

        Args:
            name (str): Template name (without .html)
            html_content (str): HTML content
        """
        filepath = os.path.join(self.template_dir, f"{name}.html")
        with open(filepath, "w") as f:
            f.write(html_content)
        self.logger.info(f"Created template: {name}")
