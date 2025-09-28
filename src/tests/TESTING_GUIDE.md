# Testing the Enhanced Reply Drafting Workflow

This guide will help you test the new redrafting capabilities that have been added to your customer support triage agent.

## What Was Added

The reply agent system now supports both:
1. **Initial Drafting**: Original workflow using `reply_drafter` → `refiner` agents
2. **Redrafting with Feedback**: New workflow using `feedback_analyzer` → `reply_drafter` → `refiner` agents

## Key Features

- ✅ **Intelligent Feedback Analysis**: The `feedback_analyzer` agent understands human feedback and translates it into specific improvement instructions
- ✅ **Structured Redrafting**: Creates new drafts based on original context + previous draft + feedback analysis
- ✅ **Preserved Quality**: The `refiner` agent still polishes all drafts (initial and redrafts)
- ✅ **State Management**: Proper handling of redraft counters and feedback clearing
- ✅ **Backward Compatibility**: Existing `reply_agent()` calls work unchanged

## Files Modified

1. **`src/agents/reply_agent/config/agents.yaml`**: Added `feedback_analyzer` agent
2. **`src/agents/reply_agent/config/tasks.yaml`**: Added `analyze_feedback_task` and `redraft_task`
3. **`src/agents/reply_agent/crew.py`**: Enhanced crew with mode selection and new function
4. **`src/main.py`**: Updated `draft_reply()` function to use redrafting workflow

## How to Test

### Option 1: Interactive Testing (Recommended)
```bash
cd d:\Projects\customer-support-triage-agent
python interactive_test.py
```

This allows you to:
- Select from sample tickets
- Generate initial drafts
- Provide custom feedback
- See the redrafting process in action
- Test multiple redraft rounds

### Option 2: Automated Testing
```bash
cd d:\Projects\customer-support-triage-agent
python test_redrafting_workflow.py
```

This runs predefined scenarios to test:
- Initial drafting workflow
- Single redraft with feedback
- Multiple redraft rounds
- Max redraft limit handling

## Testing Scenarios

### Scenario 1: Initial Draft
1. System generates initial reply using existing workflow
2. Uses `reply_drafter` → `refiner` agents
3. No feedback processing involved

### Scenario 2: Single Redraft
1. Human provides feedback like: "Make it more friendly and less technical"
2. System runs `feedback_analyzer` → `reply_drafter` → `refiner`
3. Creates improved reply addressing the feedback

### Scenario 3: Multiple Redrafts
1. Multiple rounds of feedback and redrafting
2. Each redraft considers all previous context
3. System respects MAX_REDRAFTS limit (currently 2)

## Example Workflow

```python
# Initial drafting
state.reply_draft = ""  # No previous draft
result = draft_reply(state)  # Creates initial draft

# Redrafting
state.human_feedback = "Make it more empathetic"
result = draft_reply(state)  # Creates redraft based on feedback
```

## What to Look For

When testing, observe:

1. **Initial Draft Quality**: Should be professional and address the ticket
2. **Feedback Understanding**: The system should properly interpret your feedback
3. **Redraft Improvements**: New draft should address feedback while maintaining quality
4. **State Management**: Feedback should be cleared after processing
5. **Counter Management**: Redraft count should increment properly

## Troubleshooting

If you encounter issues:

1. **Import Errors**: Make sure you're in the project directory and have all dependencies
2. **Model Errors**: Check that your language model (ollama/qwen2.5:7b) is available
3. **CrewAI Errors**: Ensure CrewAI is properly configured and agents.yaml/tasks.yaml are valid

## Next Steps

After testing, you can integrate this into your full LangGraph workflow where:
- Human reviewers can provide feedback through your HITL system
- The workflow automatically redrafts based on that feedback
- The process continues until approved or max redrafts reached

Happy testing! 🚀