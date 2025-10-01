# Configuration Management

This document explains how to manage the hyperparameters and configuration settings for the Customer Support Triage Agent.

## Configuration File Location

The main configuration file is located at:
```
config/config.json
```

## Configuration Structure

The configuration is organized into several sections:

### System Configuration
```json
{
  "system": {
    "max_redrafts": 2,        // Maximum number of reply redrafts allowed
    "max_retries": 2,         // Maximum retries for tool/API calls
    "default_language": "en", // Default language for tickets
    "default_urgency": "medium", // Default urgency level
    "default_category": "general" // Default category
  }
}
```

### Model Configuration
```json
{
  "models": {
    "triage_model": "ollama/qwen2.5:7b",         // Model for ticket triage
    "kb_model": "gemini/gemini-2.5-flash",      // Model for knowledge base queries
    "reply_model": "ollama/qwen2.5:7b",         // Model for reply generation
    "action_suggester_model": "ollama/qwen2.5:7b" // Model for action suggestions
  }
}
```

### Action Configuration
```json
{
  "actions": {
    "risky_actions": ["refund", "credit_note", "account_cancel"], // Actions requiring human approval
    "non_risky_autosafe": ["label", "assign_queue", "create_jira"], // Safe auto-approval actions
    "auto_approval_confidence_threshold": 0.8 // Confidence threshold for auto-approval
  }
}
```

### Confidence Thresholds
```json
{
  "confidence_thresholds": {
    "high_confidence": 0.8,   // High confidence threshold
    "medium_confidence": 0.6, // Medium confidence threshold
    "low_confidence": 0.4     // Low confidence threshold
  }
}
```

### Category and Urgency Mappings
```json
{
  "categories": {
    "mapping": {
      "1": "billing",
      "2": "technical",
      "3": "account",
      "4": "product",
      "5": "feedback",
      "6": "orders",
      "7": "compliance",
      "8": "general"
    }
  },
  "urgency": {
    "mapping": {
      "1": "low",
      "2": "medium",
      "3": "high",
      "4": "critical"
    }
  }
}
```

### Workflow Configuration
```json
{
  "workflow": {
    "force_human_review": true,      // Always require human review
    "enable_auto_approval": false,   // Enable automatic action approval
    "max_ticket_preview_length": 200 // Maximum characters shown in ticket preview
  }
}
```

### UI Configuration
```json
{
  "ui": {
    "separator_length": 60,           // Length of separator lines in output
    "action_separator_length": 50,    // Length of action separator lines
    "display_confidence_decimals": 2  // Number of decimal places for confidence scores
  }
}
```

## Usage Examples

### Changing Models
To switch to different language models, update the `models` section:
```json
{
  "models": {
    "triage_model": "gpt-4",
    "kb_model": "gpt-3.5-turbo",
    "reply_model": "claude-3-sonnet",
    "action_suggester_model": "gpt-4"
  }
}
```

### Adjusting Confidence Thresholds
To make the system more or less conservative:
```json
{
  "confidence_thresholds": {
    "high_confidence": 0.9,   // More conservative
    "medium_confidence": 0.7,
    "low_confidence": 0.5
  }
}
```

### Enabling Auto-Approval
To enable automatic approval of safe actions:
```json
{
  "workflow": {
    "force_human_review": false,     // Don't force review for all tickets
    "enable_auto_approval": true,    // Enable auto-approval
    "max_ticket_preview_length": 200
  },
  "actions": {
    "auto_approval_confidence_threshold": 0.85 // Require high confidence
  }
}
```

### Adding New Action Types
To add new risky or safe actions:
```json
{
  "actions": {
    "risky_actions": ["refund", "credit_note", "account_cancel", "data_deletion"],
    "non_risky_autosafe": ["label", "assign_queue", "create_jira", "send_notification"]
  }
}
```

## Configuration Management in Code

The configuration is managed through the `Config` class in `src/utils/config.py`. This class provides:

1. **Property-based access**: Access configuration values through properties like `config.max_retries`
2. **Dot notation access**: Use `config.get('system.max_retries')` for nested values
3. **Default values**: Automatic fallback to sensible defaults if values are missing
4. **Runtime reloading**: Call `config.reload()` to reload configuration from file
5. **Dynamic updates**: Modify and save configuration at runtime

### Example Usage in Code

```python
from utils.config import config

# Access configuration values
max_retries = config.max_retries
triage_model = config.triage_model

# Check if auto-approval is enabled
if config.enable_auto_approval:
    # Auto-approve safe actions with high confidence
    pass

# Get nested values with dot notation
separator_length = config.get('ui.separator_length', 60)

# Reload configuration after external changes
config.reload()
```

## Best Practices

1. **Backup configurations**: Keep backups of working configurations before making changes
2. **Environment-specific configs**: Consider using different config files for development, staging, and production
3. **Validate changes**: Test configuration changes with sample tickets before deploying
4. **Document changes**: Keep track of configuration changes and their effects
5. **Version control**: Store configuration files in version control to track changes

## Troubleshooting

### Common Issues

1. **Invalid JSON**: Ensure the JSON syntax is valid (use a JSON validator)
2. **Missing values**: The system will use defaults for missing configuration values
3. **File permissions**: Ensure the config file is readable by the application
4. **Model availability**: Verify that specified models are available and accessible

### Validation

The configuration system includes basic validation and will:
- Use default values for missing configuration
- Raise errors for invalid JSON syntax
- Provide meaningful error messages for configuration issues

To validate your configuration, run the main application and check for any startup errors or warnings.