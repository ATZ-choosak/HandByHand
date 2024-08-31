# Project Setup Guide

This guide will walk you through the steps to set up your Python environment, install dependencies, and initialize the database for your project.

## 1. Creating a Python Virtual Environment

To ensure that your project's dependencies are isolated, it's recommended to create a Python virtual environment.

### Step 1: Create the Virtual Environment

Open your terminal and run the following command:

```bash
python -m venv venv
```

### Step 2: Activate Virtual Environment
* Windows
```bash
venv\Scripts\activate
```
* Mac / Linux
```bash
source venv\bin\activate
```

## 2. Install python poetry

### Step 1: Install Poetry

```bash
pip install poetry
```

### Step 2: Install Poetry dependencies

```bash
poetry install
```

## 3. Inital Database
```bash
poetry run python initial-db.py
```

## 4. Run server
* Windows
```bash
poetry run uvicorn backend.main:create_app --reload --factory
```