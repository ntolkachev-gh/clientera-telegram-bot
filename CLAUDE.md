# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Testing
```bash
# Run all tests
python test/run_tests.py

# Run specific test file
python test/run_tests.py test/test_openai_tools.py

# Run with verbose output
python test/run_tests.py -v

# Run with coverage
python test/run_tests.py --coverage

# Run only service tests
python test/run_tests.py --services

# Run only staff tests
python test/run_tests.py --staff
```

### Code Quality
```bash
# Format code
black .

# Lint code
flake8 .
```

### Local Development
```bash
# Quick start with Docker (PostgreSQL, Qdrant, PgAdmin)
cd local_development
./start_local.sh

# Run Telegram bot locally
python bot/main.py

# Run web admin interface
python -m uvicorn admin.main:app --reload --port 8000

# Run reminder system
python bot/remind.py

# Initialize database
python -c "from database.database import init_db; init_db()"

# Load knowledge base
python bot/embedding.py
```

### Heroku Deployment
```bash
# Deploy to production
./deploy_to_heroku.sh

# Initialize production database
heroku run python -c "from database.database import init_db; init_db()"

# Load production knowledge base
heroku run python bot/embedding.py
```

## Architecture Overview

This is a Telegram bot for a beauty salon that integrates with multiple external services to provide intelligent booking assistance.

### Core Components

**Bot Layer** (`bot/`):
- `main.py` - Primary Telegram bot entry point
- `simple_main.py` - Simplified bot for production (used in Procfile)
- `dialog_manager.py` - Manages conversation flow and context
- `embedding.py` - Knowledge base management using Qdrant vector search
- `youclients_api.py` - Integration with Youclients booking API
- `remind.py` - Automated reminder system for return visits

**Core Services** (`core/`):
- `openai_client.py` - OpenAI GPT integration with token usage tracking and parallel tool execution
- `openai_tools.py` - Tool definitions for Youclients API integration
- `yclients_client.py` - Low-level Youclients API client

**Database Layer** (`database/`):
- `models.py` - SQLAlchemy models for clients, sessions, messages, appointments, usage logs
- `database.py` - Database connection and initialization

**Admin Interface** (`admin/`):
- `main.py` - FastAPI web interface for client management and analytics
- `templates/` - Jinja2 HTML templates

### Key Integrations

**OpenAI GPT-5**: Powers natural language understanding and response generation. The bot uses function calling to integrate with external APIs seamlessly.

**Qdrant Cloud**: Vector database for knowledge base search. Markdown files in `knowledge_base/` are chunked and embedded for semantic search.

**Youclients API**: Third-party booking system integration for:
- Retrieving available services and staff
- Checking appointment availability
- Creating bookings
- Managing staff schedules

**PostgreSQL**: Persistent storage for:
- Client profiles and preferences
- Conversation sessions and message history
- OpenAI usage tracking and cost monitoring
- Appointment records

### Data Flow

1. **User Message** → Telegram → `DialogManager`
2. **Context Building** → Retrieves client history, active session, relevant knowledge base chunks
3. **AI Processing** → OpenAI GPT with tool functions for Youclients API calls
4. **Response Generation** → Natural language response with booking actions
5. **State Persistence** → Updates client preferences, session data, usage logs

### Environment Configuration

All configuration is managed through `config.py` using Pydantic settings. Required environment variables:
- `TELEGRAM_BOT_TOKEN` - Bot authentication
- `OPENAI_API_KEY` - GPT access
- `QDRANT_URL`, `QDRANT_API_KEY` - Vector database
- `DATABASE_URL` - PostgreSQL connection
- `YOUCLIENTS_API_KEY`, `YOUCLIENTS_COMPANY_ID` - Booking API
- Admin interface credentials and session settings

### Knowledge Base System

The bot uses a sophisticated knowledge base system:
- Markdown files in `knowledge_base/` contain service information, pricing, policies
- Files are chunked by H2 headers (`##`) during embedding process
- Semantic search finds relevant chunks for user queries
- Knowledge is integrated into GPT context for accurate responses

### Testing Strategy

Tests are organized by functionality:
- API integration tests for Youclients endpoints
- Embedding and search functionality tests
- OpenAI tools and parallel execution tests
- Database model and operation tests

Use `python test/run_tests.py` as the primary test runner with built-in dependency installation and flexible targeting options.