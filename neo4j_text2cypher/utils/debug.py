"""Debug logging utilities for Neo4j Text2Cypher components."""

import logging
import os
from typing import Optional

from .config import DebugConfig


def setup_debug_logging(debug_config: Optional[DebugConfig] = None):
    """
    Setup debug logging for Neo4j Text2Cypher components.
    
    Parameters
    ----------
    debug_config : Optional[DebugConfig]
        Debug configuration from app config. If None, only environment variables are used.
    """
    # Setup console handler for debug messages
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    
    # Create formatter for debug messages
    formatter = logging.Formatter('%(message)s')
    console_handler.setFormatter(formatter)
    
    # Configure validation logger
    validation_enabled = _is_debug_enabled('validation', debug_config)
    validation_logger = logging.getLogger('neo4j_text2cypher.validation')
    # Clear any existing handlers
    validation_logger.handlers.clear()
    validation_logger.propagate = False  # Prevent propagation to parent loggers
    
    if validation_enabled:
        validation_logger.setLevel(logging.DEBUG)
        validation_logger.addHandler(console_handler)
    else:
        validation_logger.setLevel(logging.CRITICAL)  # Effectively disable
    
    # Configure routing logger
    routing_enabled = _is_debug_enabled('routing', debug_config)
    routing_logger = logging.getLogger('neo4j_text2cypher.routing')
    # Clear any existing handlers
    routing_logger.handlers.clear()
    routing_logger.propagate = False  # Prevent propagation to parent loggers
    
    if routing_enabled:
        routing_logger.setLevel(logging.DEBUG)
        routing_logger.addHandler(console_handler)
    else:
        routing_logger.setLevel(logging.CRITICAL)  # Effectively disable
    
    # Configure planner logger
    planner_enabled = _is_debug_enabled('planner', debug_config)
    planner_logger = logging.getLogger('neo4j_text2cypher.planner')
    # Clear any existing handlers
    planner_logger.handlers.clear()
    planner_logger.propagate = False  # Prevent propagation to parent loggers
    
    if planner_enabled:
        planner_logger.setLevel(logging.DEBUG)
        planner_logger.addHandler(console_handler)
    else:
        planner_logger.setLevel(logging.CRITICAL)  # Effectively disable


def _is_debug_enabled(component: str, debug_config: Optional[DebugConfig] = None) -> bool:
    """
    Check if debug logging is enabled for a component.
    
    Environment variables override config file settings.
    
    Parameters
    ----------
    component : str
        Component name ('validation', 'routing', 'planner')
    debug_config : Optional[DebugConfig]
        Debug configuration from app config
        
    Returns
    -------
    bool
        True if debug logging is enabled for the component
    """
    # Environment variable names
    env_var_map = {
        'validation': 'DEBUG_VALIDATION',
        'routing': 'DEBUG_ROUTING', 
        'planner': 'DEBUG_PLANNER'
    }
    
    env_var = env_var_map.get(component)
    if env_var and env_var in os.environ:
        return os.getenv(env_var, 'false').lower() in ('true', '1', 'yes', 'on')
    
    # Fall back to config file setting
    if debug_config:
        return getattr(debug_config, component, False)
    
    return False


def get_validation_logger():
    """Get the validation debug logger."""
    return logging.getLogger('neo4j_text2cypher.validation')


def get_routing_logger():
    """Get the routing debug logger."""
    return logging.getLogger('neo4j_text2cypher.routing')


def get_planner_logger():
    """Get the planner debug logger."""
    return logging.getLogger('neo4j_text2cypher.planner')