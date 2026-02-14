# Dashboard Migration & Project Integration Prompt

I am restructuring my development environment to manage multiple independent projects under a single `Project` root.
Please help me set up the new **Dashboard** project which will serve as the main hub.

## Current Structure (in `Desktop\Project\`)
- **Summariser/**: AI News Bot (Python). Currently handles everything including site generation.
- **Slot machine/**: Standalone web game.

## Goal: Create "Dashboard" Hub
I want to create a new **Dashboard** folder that will be the actual GitHub Pages repository (`commitkim.github.io`).

### Requirements:

1.  **Dashboard Architecture (Static Site)**
    - Create `Dashboard/` folder.
    - Implement a `builder.py` (Python) that:
        - Reads JSON data from `Dashboard/data/`.
        - Renders HTML using Jinja2 templates.
        - Outputs to `Dashboard/docs/`.
    - Create a `dashboard.html` template with a grid layout for widgets (News, Weather, Links).

2.  **Git Automation (Auto-Deploy)**
    - Initialize Git in `Dashboard/`.
    - Create a `deploy.bat` script that:
        - Runs `python builder.py`.
        - Adds all changes in `docs/`.
        - Commits with a timestamp message.
        - Pushes to the remote repository (main/gh-pages).
    - *Note*: Use the existing git credentials if possible.

3.  **Integration Plan**
    - **Summariser**: Will be modified to save JSON to `../Dashboard/data/news/`.
    - **Slot Machine**: Will be copied to `../Dashboard/static/slot-machine/`.

## Immediate Action
Please start by creating the **Dashboard** folder structure and the **builder.py** script.
Then, help me configure the `deploy.bat` for automatic pushing.
