"""
Configuration management utility for the customer support triage agent.
"""

import json
import os
from typing import Dict, Any


class Config:
    """Configuration manager for the triage agent."""
    
    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), 
                'config', 
                'config.json'
            )
        
        self.config_path = config_path
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in configuration file: {e}")
    
    def reload(self):
        """Reload configuration from file."""
        self._config = self._load_config()
    
    def get(self, key: str, default=None):
        """Get configuration value by dot notation key (e.g., 'system.max_retries')."""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """Set configuration value by dot notation key."""
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def save(self):
        """Save current configuration to file."""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self._config, f, indent=2)
    
    # System configuration
    @property
    def max_redrafts(self) -> int:
        return self.get('system.max_redrafts', 2)
    
    @property
    def max_retries(self) -> int:
        return self.get('system.max_retries', 2)
    
    @property
    def default_language(self) -> str:
        return self.get('system.default_language', 'en')
    
    @property
    def default_urgency(self) -> str:
        return self.get('system.default_urgency', 'medium')
    
    @property
    def default_category(self) -> str:
        return self.get('system.default_category', 'general')
    
    # Model configurations
    @property
    def triage_model(self) -> str:
        return self.get('models.triage_model', 'gemini/gemini-2.5-flash')
    
    @property
    def kb_model(self) -> str:
        return self.get('models.kb_model', 'gemini/gemini-2.5-flash')
    
    @property
    def reply_model(self) -> str:
        return self.get('models.reply_model', 'gemini/gemini-2.5-flash')
    
    @property
    def action_suggester_model(self) -> str:
        return self.get('models.action_suggester_model', 'gemini/gemini-2.5-flash')
    
    # Action configurations
    @property
    def risky_actions(self) -> set:
        return set(self.get('actions.risky_actions', ['refund', 'credit_note', 'account_cancel']))
    
    @property
    def non_risky_autosafe(self) -> set:
        return set(self.get('actions.non_risky_autosafe', ['label', 'assign_queue', 'create_jira']))
    
    @property
    def auto_approval_confidence_threshold(self) -> float:
        return self.get('actions.auto_approval_confidence_threshold', 0.8)
    
    # Confidence thresholds
    @property
    def high_confidence(self) -> float:
        return self.get('confidence_thresholds.high_confidence', 0.8)
    
    @property
    def medium_confidence(self) -> float:
        return self.get('confidence_thresholds.medium_confidence', 0.6)
    
    @property
    def low_confidence(self) -> float:
        return self.get('confidence_thresholds.low_confidence', 0.4)
    
    # Category and urgency mappings
    @property
    def category_mapping(self) -> Dict[str, str]:
        return self.get('categories.mapping', {})
    
    @property
    def urgency_mapping(self) -> Dict[str, str]:
        return self.get('urgency.mapping', {})
    
    # Workflow configurations
    @property
    def force_human_review(self) -> bool:
        return self.get('workflow.force_human_review', True)
    
    @property
    def enable_auto_approval(self) -> bool:
        return self.get('workflow.enable_auto_approval', False)
    
    @property
    def max_ticket_preview_length(self) -> int:
        return self.get('workflow.max_ticket_preview_length', 200)
    
    # UI configurations
    @property
    def separator_length(self) -> int:
        return self.get('ui.separator_length', 60)
    
    @property
    def action_separator_length(self) -> int:
        return self.get('ui.action_separator_length', 50)
    
    @property
    def display_confidence_decimals(self) -> int:
        return self.get('ui.display_confidence_decimals', 2)


# Global config instance
config = Config()