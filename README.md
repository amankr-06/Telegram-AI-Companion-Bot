<div align="center">

# Telegram AI Companion Bot - Reze

**An intelligent, persistent memory-enabled Telegram bot powered by Google Gemini and Supabase, built with Python and FastAPI.**

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Supabase-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://supabase.com/)
[![Google Gemini](https://img.shields.io/badge/Google%20Gemini-API-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev/)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](#license)

</div>

---

## Table of Contents
1. [Overview](#overview)
2. [Features](#features)
3. [Repository Layout](#repository-layout)
4. [Tech Stack](#tech-stack)
5. [Getting Started](#getting-started)
   - [Clone the Repository](#1-clone-the-repository)
   - [Set Up Virtual Environment](#2-set-up-virtual-environment)
   - [Install Dependencies](#3-install-dependencies)
   - [Configure Environment Variables](#4-configure-environment-variables)
   - [Create a Telegram Bot](#5-create-a-telegram-bot)
   - [Run Locally with Cloudflare Tunnel](#6-run-locally-with-cloudflare-tunnel)
   - [Testing](#Testing)
6. [License](#license)

---

## Overview

A conversational companion bot designed for Telegram. It features a persistent memory architecture backed by PostgreSQL, allowing it to maintain context and remember user details seamlessly across sessions. The persona engineering ensures the bot converses naturally like a real person rather than a standard artificial intelligence assistant.

---

## Features

* **Persistent Memory**: Automatically logs interactions and compresses user preferences over time.
* **Natural Conversational Intelligence**: Fine-tuned prompt architecture designed to provide fluid, lifelike dialogue responses.
* **Custom Persona Support**: Easily configure and integrate custom system instructions to define unique bot personalities and behavioral traits.
* **Database Integration**: Reliable structured storage running on Supabase PostgreSQL.
* **FastAPI Backend**: Clean asynchronous API handling lifespans and bot hooks.

---

## Repository Layout

```text
.
├── main.py                         # Application entry point and webhook routers
├── db.py                           # Database connection and persistence handlers
├── sys-instruct.txt           # Core system instruction and persona prompt
├── requirements.txt                # Python package dependencies
├── .env.example                    # Template for environment variables
├── LICENSE                         # Project license
└── README.md                       # Project documentation
```

---

## Tech Stack

* **Language**: Python 3.11+
* **Framework**: FastAPI / Uvicorn
* **Database**: PostgreSQL (Supabase)
* **AI Engine**: Google Gemini API

---

## Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/amankr-06/Telegram-AI-Companion-Bot.git
cd telegram-ai-companion
```

### 2. Set Up Virtual Environment
```bash
python -m venv .venv
# On Windows:
.venv\Scripts\activate.ps1
# On macOS/Linux:
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Rename `.env.example` to `.env` in the root directory and replace all placeholders with your credentials.

### 5. Create a Telegram Bot
Search for BotFather on Telegram, create a new bot from BotFather, name it and fill other required details, and copy the Bot Token into your `.env` file.

### 6. Run Locally with Cloudflare Tunnel
• Start your FastAPI server(preferably in a new terminal #terminal 1):
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
• Expose your local port for Telegram webhook testing(preferably in a new terminal #terminal 2):
```bash
cloudflared tunnel --url http://localhost:8000
```
• Copy the generated Cloudflare URL (e.g., `https://handled-registry-databases-symptoms.trycloudflare.com`) and register the webhook via your browser or terminal by pasting the url below.

Paste your bot token at placeholder `<YOUR_BOT_TOKEN>` and the url you obtain from cloudflare to `<YOUR_CLOUDFLARE_URL>`
```text
https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=<YOUR_CLOUDFLARE_URL>/webhook
```
• Verify the success response:
```json
{"ok":true,"result":true,"description":"Webhook was set"}
```
### 7. Testing
Run your telegram bot and chat with Reze.

---

## License

MIT License

Copyright (c) 2026 Aman Kumar

Permission is hereby granted, free of charge, to any person obtaining a copy of this software to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED.
