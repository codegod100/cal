# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Flask-based event calendar web application that allows users to create, manage, and export printable calendars. The app supports event scheduling with times, weekly recurring events, and PDF export functionality.

## Development Commands

**Environment Setup:**
- Dependencies managed with `uv` (configured via `mise.toml`)
- Install dependencies: `mise exec -- uv sync`
- Run application: `mise exec -- uv run python app.py` or `uv run python app.py`
- Development server runs on `http://localhost:5000` with debug mode enabled

**Database:**
- SQLite database auto-initializes on first run
- Database file: `calendar.db` (created automatically)
- Schema includes backward-compatible migrations for existing installations

## Architecture

**Core Components:**
- `app.py`: Flask application with routes for calendar views, event management, PDF export, and settings
- `database.py`: SQLite database operations with functions for events and settings management
- `templates/`: Jinja2 templates using Tailwind CSS via CDN for styling

**Key Routes:**
- `/` - Home page with month selection
- `/calendar/<year>/<month>` - Calendar view with event display
- `/add_event`, `/edit_event/<id>` - Event management forms
- `/export_pdf/<year>/<month>` - PDF generation using WeasyPrint
- `/settings` - Calendar title configuration

**Database Schema:**
- `events` table: id, title, date, time, description, is_recurring, recurring_type, created_at
- `settings` table: id (always 1), calendar_title

**Template Structure:**
- `base.html`: Common layout with Tailwind CSS
- `calendar.html`: Main calendar grid view with print-friendly styling
- `calendar_pdf.html`: PDF-optimized template for A4 landscape export
- Form templates use consistent styling and JavaScript for UI interactions

**Event Features:**
- Optional time fields with HTML5 time inputs
- Weekly recurring events create 52 instances (1 year)
- Visual indicators for recurring events (↻ symbol)
- Events sorted by date and time within each day

**PDF Export:**
- Uses WeasyPrint for HTML-to-PDF conversion
- A4 landscape orientation with print-specific styling
- Includes calendar title, events with times, and recurring indicators

**Configuration:**
- Calendar title stored in database and configurable via settings page
- Database auto-migration handles adding new columns to existing installations
- Print styles use CSS `@media print` and `.no-print` classes for selective display