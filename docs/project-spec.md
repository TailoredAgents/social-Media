# Enterprise AI Social Media Content Agent
## Technical Architecture Overview

**Document Version:** 1.1  
**Date:** July 22, 2025  
**Repository:** https://github.com/TailoredAgents/Social-media-agent.git

## Project Overview

Enterprise AI Social Media Content Agent is a modular, scalable SaaS application that autonomously generates, schedules, and optimizes social media content using CrewAI multi-agent orchestration. The system features a premium React/Tailwind dashboard and FastAPI backend deployed on Render.com.

## Architecture Components

### Frontend/Dashboard (React + Tailwind CSS)
- **Framework:** React v18 with Vite
- **Styling:** Tailwind CSS v3 for professional, enterprise-grade UI
- **Charts:** Chart.js v4 for interactive analytics
- **Auth:** Auth0 integration with JWT
- **State Management:** TanStack React Query + Context API
- **Routing:** React Router v6

### Multi-Agent System (CrewAI)
- **Research Sub-Agent:** Trend analysis using GPT-5 Mini + web scraping
- **Content Generation Sub-Agent:** Text/image creation with OpenAI APIs
- **Posting Sub-Agent:** Social platform integration and scheduling
- **Optimizer Sub-Agent:** Performance analysis and iteration

### Backend (FastAPI + CrewAI)
- **API Framework:** FastAPI v0.111 with Uvicorn
- **AI Orchestration:** CrewAI for multi-agent collaboration
- **Task Queue:** Celery v5 with Redis
- **Database:** PostgreSQL v16 with SQLAlchemy v2
- **Memory:** FAISS for vector embeddings

### Deployment (Render.com)
- **Web Service:** React dashboard (Node runtime)
- **Background Worker:** Python agents with Celery
- **Database:** Render-managed PostgreSQL
- **Cron Jobs:** Daily research triggers
- **Storage:** Persistent disks for FAISS indexes

## Key Features

1. **Content Calendar:** Drag-and-drop scheduling interface
2. **Analytics Hub:** Real-time performance metrics and insights
3. **Memory Explorer:** Searchable content history and trends
4. **Settings Panel:** Brand customization and preferences
5. **Alerts Feed:** Real-time notifications and updates

## Technology Stack

- **AI Models:** OpenAI GPT-5, GPT-5 Mini, gpt-image-1
- **Search:** Serper API, BeautifulSoup, Tweepy
- **Social APIs:** Twitter, , Instagram integration
- **Monitoring:** Render metrics, structured logging
- **Security:** HTTPS, environment variables, input validation

This specification serves as the foundation for implementing the complete social media content agent system.