# Fantasy Baseball In Season Analytics - Development Guide

## Build/Run Commands
- **Setup**: `python scripts/setup.py`
- **Find Team ID**: `python scripts/find_team_id.py`
- **Team Analysis**: `python scripts/team_analysis.py`
- **Player Analysis**: `python scripts/player_analysis.py [--position "SP"] [--team-id YOUR_TEAM_ID]`
- **Fantasy Insights**: `python scripts/fantasy_insights.py [--projections] [--waiver]`
- **Tests**: `pytest tests/` (run a specific test with `pytest tests/test_file.py::test_function`)

## Code Style Guidelines
- **Python Version**: Use Python 3.8+ features
- **Imports**: Group standard library, third-party, and local imports with a blank line between groups
- **Typing**: Use type hints for function parameters and return values
- **Error Handling**: Use try/except blocks with specific exceptions and informative error messages
- **Logging**: Use the Python logging module instead of print statements
- **Documentation**: Follow Google-style docstrings for classes and functions
- **Naming**: Use snake_case for variables/functions and PascalCase for classes
- **File Structure**: Group related functionality in appropriate modules under src/
- **API Client**: Handle ESPN API connectivity issues gracefully with proper error handling
- **Visualization**: Use matplotlib/seaborn for consistent charts with proper labels and titles