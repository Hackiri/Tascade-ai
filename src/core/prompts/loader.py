"""
Prompt Template Loader for Tascade AI.
This module provides functions for loading and rendering prompt templates.
"""

import os
import string
from typing import Dict, Any, Optional
import pkg_resources

# Base directory for templates
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), 'templates')

def load_template(template_name: str) -> str:
    """
    Load a prompt template from the templates directory.
    
    Args:
        template_name: Name of the template file (without extension)
        
    Returns:
        The template content as a string
        
    Raises:
        FileNotFoundError: If the template file doesn't exist
    """
    template_path = os.path.join(TEMPLATES_DIR, f"{template_name}.md")
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        # Try to load from package resources as fallback
        try:
            template_resource = f"templates/{template_name}.md"
            return pkg_resources.resource_string(__name__, template_resource).decode('utf-8')
        except (pkg_resources.DistributionNotFound, FileNotFoundError):
            raise FileNotFoundError(f"Template '{template_name}' not found")

def render_template(template: str, variables: Dict[str, Any]) -> str:
    """
    Render a template with the given variables.
    
    Args:
        template: The template string
        variables: Dictionary of variables to substitute
        
    Returns:
        The rendered template
    """
    # Use string.Template for simple variable substitution
    template_obj = string.Template(template)
    return template_obj.safe_substitute(variables)

def load_prompt(prompt_name: str, variables: Optional[Dict[str, Any]] = None) -> str:
    """
    Load and render a prompt template.
    
    Args:
        prompt_name: Name of the prompt template
        variables: Optional dictionary of variables to substitute
        
    Returns:
        The rendered prompt
    """
    template = load_template(prompt_name)
    
    if variables:
        return render_template(template, variables)
    
    return template
