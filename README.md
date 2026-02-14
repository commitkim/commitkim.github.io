# CommitKim Projects Hub

Welcome to my personal project monorepo. This repository houses my various development projects, accessible via the [Main Dashboard](https://commitkim.github.io).

## 📂 Projects

### 1. [Dashboard](./Dashboard)
The central hub for all my projects. It aggregates data from other services and provides a unified interface.
- **Tech**: Python (Builder), Jinja2, TailwindCSS

### 2. [Summariser](./Summariser)
An AI-powered news aggregator that collects "Morning Routine" videos from YouTube, summarizes them using Google Gemini, and sends a daily report via KakaoTalk.
- **Tech**: Python, YouTube API, Google Gemini, Kakao API

### 3. [Slot Machine](./Slot%20machine)
A simple web-based slot machine game.
- **Tech**: HTML, CSS, JavaScript

## 🚀 Deployment
This project is automatically deployed to GitHub Pages.
The `Dashboard` is built and published to the `docs/` folder, which is served as the static site.

### How to Deploy
Run the deployment script from the root directory:
```bash
deploy.bat
```
This will:
1. Build the Dashboard (aggregating latest data).
2. Commit all changes in the `Project` folder.
3. Push to GitHub.
