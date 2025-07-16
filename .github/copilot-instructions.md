# Copilot Instructions

## Project Context
This is a real estate data management application written in Python 3.12 using:
- **Database**: MongoDB for data storage
- **Architecture**: Connector pattern with scrapers, storage implementations, and data models
- **Key Libraries**: pymongo, requests, BeautifulSoup, pydantic/dataclasses

## Communication Style
- Provide direct, factual responses without unnecessary apologies or agreements
- Focus on practical solutions over explanations
- When I say you're wrong, evaluate the claim objectively and respond with facts
- Avoid emojis, exclamation marks, and hyperbolic language

## Task Approach
- **Always suggest the most efficient and modern approach** for any task
- **Ask for clarifications** before starting complex tasks
- **Break down complex requests** into smaller steps and confirm each step
- **Validate my prompts** and help me write more effective ones
- **Ask before writing tests** unless explicitly requested
- When writing tests, ask for framework preference (pytest/unittest) and test type (unit/integration)

## Scope and Boundaries
- **Stay within the explicit scope** of each request
- **Don't make improvements** outside the requested changes
- **Ask before expanding scope** - even for "obvious" improvements
- **Stop when the specific task is complete** - don't continue with related tasks
- **If you encounter errors that prevent completion**, explain what can/cannot be done

## Code Changes
- **Complete the specific task requested, nothing more**
- **Don't refactor code unless explicitly asked**
- **If you see related issues, mention them but don't fix them**
- **Ask before making any changes outside the stated scope**


## Python Coding Standards

### Core Principles
- **Pythonic code**: Write clean, efficient, maintainable code following Python idioms
- **Modern Python**: Use Python 3.12+ features and latest library versions
- **PEP 8 compliance**: Follow official Python style guidelines
- **Minimal scope changes**: When modifying files, only change what's necessary and remove unused imports
- **Priority hierarchy**: Correctness > Maintainability > Performance

### Code Style
- Use `f-strings` for string formatting
- Use `snake_case` for variables and functions
- Use `CamelCase` for class names
- Use `UPPER_CASE` for constants
- Use `logging` module instead of print statements
- Use module-level loggers: `logger = logging.getLogger(__name__)`

### Type Hints and Annotations
- **Always use type hints** for function parameters and return types
- **Use modern type hints**: `list`, `dict`, `set` instead of `List`, `Dict`, `Set`
- **Avoid `Any` and `Union` types**: Use specific types or Union types when needed
- **Help me understand and use** complex type annotations when they arise

### Documentation
- Include concise docstrings for classes and functions
- Add inline comments only when code intent isn't clear
- Avoid emojis and exclamation marks in all code and comments
- Comments start with a capital letter and do not end with a period

## Terminal Usage
- Prefer PowerShell syntax (Windows environment)
