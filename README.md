# TaskDock: Dockerized Flask Web App

A small task board built with **Flask** and **SQLite**, packaged as a **Docker**
image. Tasks survive container restarts because the database lives on a named
Docker volume.

## What it demonstrates

- A Flask application served by Gunicorn
- A multi-step, production-style Docker image with a non-root user
- SQLite persistence through a Docker named volume
- A built-in container health check at `/health`
- Docker Compose for one-command startup
- Unit tests that do not require Docker

## Features

- Add, complete, reopen, and delete tasks
- Responsive, accessible UI with no external dependencies
- Automatic database initialization on startup
- SQLite WAL mode and a busy timeout for safe concurrent reads
- Optional confirmation before deleting a task

## Quick start with Docker Compose

Docker Desktop (or Docker Engine with the Compose plugin) must be installed and
running.

```bash
cd dockerized-flask-app
docker compose up --build
```

Open <http://localhost:8000>.

To run in the background:

```bash
docker compose up --build -d
docker compose logs -f
```

Stop the app:

```bash
docker compose down
```

`docker compose down` keeps the `task-data` volume, so your tasks remain the next
time you start the app.

## Build and run with plain Docker

### 1. Build the image

```bash
docker build -t taskdock:local .
```

### 2. Start the container

```bash
docker run --rm --name taskdock \
  -p 8000:8000 \
  -v taskdock-data:/data \
  taskdock:local
```

Open <http://localhost:8000>. Press `Ctrl+C` to stop the container. The
`taskdock-data` volume keeps the database between runs.

### 3. Or run detached

```bash
docker run -d --name taskdock \
  -p 8000:8000 \
  -v taskdock-data:/data \
  --restart unless-stopped \
  taskdock:local
```

```bash
docker logs -f taskdock
docker stop taskdock
```

## How it works

| Piece | Purpose |
| --- | --- |
| `app.py` | Flask routes, SQLite access, and startup initialization |
| `templates/index.html` | Server-rendered task board |
| `static/` | Styling and delete confirmation |
| `Dockerfile` | Python 3.12 image, Gunicorn, non-root `app` user, health check |
| `compose.yaml` | Builds the image, maps port `8000`, mounts the data volume |
| `tests/` | Standard-library `unittest` coverage of the main routes |

The container writes SQLite data to `/data/tasks.db`. Compose mounts the named
volume `task-data` at `/data`, so the database is independent of the container
lifecycle.

The Docker health check calls `http://127.0.0.1:8000/health` every 30 seconds
inside the container. Check it from the host at <http://localhost:8000/health>.

## Configuration

| Variable | Default | Description |
| --- | --- | --- |
| `DATABASE_PATH` | `/data/tasks.db` in Docker | Location of the SQLite database |

To use a different host port, change the Compose port mapping or pass a
different `-p` value to `docker run`, for example `-p 9000:8000`.

## Data and cleanup

Inspect or back up the database:

```bash
docker compose exec web python -c "import sqlite3; print(sqlite3.connect('/data/tasks.db').execute('select * from tasks').fetchall())"
```

Remove the app and all stored tasks:

```bash
docker compose down -v
```

For a plain-Docker setup, remove the volume with:

```bash
docker volume rm taskdock-data
```

> The Compose volume is prefixed with the project name, so it is usually named
> `taskdock_task-data`. Confirm with `docker volume ls`.

## Local development without Docker

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

macOS / Linux:

```bash
source .venv/bin/activate
```

Install and run:

```bash
python -m pip install -r requirements.txt
python app.py
```

The development server runs at <http://localhost:8000>. To use a different port:

```powershell
$env:PORT = "5000"
python app.py
```

On macOS / Linux, use `PORT=5000 python app.py`.

## Run the tests

```bash
python -m unittest discover -s tests -v
```

The tests use a temporary database and do not modify `tasks.db`.

## Common commands

```bash
docker compose ps
docker compose logs -f web
docker compose restart web
docker compose build --no-cache
docker compose down -v
```

## Troubleshooting

- **Port 8000 is already in use:** stop the conflicting service or use
  `-p 9000:8000` with Docker / change the Compose port mapping.
- **Cannot connect to the Docker daemon:** start Docker Desktop and wait until
  the engine is ready.
- **The UI loads but tasks do not persist:** ensure the container has the
  `/data` volume mounted. Without it, the database belongs to the container and
  disappears when the container is removed.
- **Changes are missing after an edit:** rebuild with
  `docker compose up --build`. A plain restart reuses the existing image.
- **Permission errors on `/data`:** use the named volume shown above. A bind
  mount created by the host may be owned by a different user, while the
  container runs as the unprivileged `app` user.

## Project structure

```text
dockerized-flask-app/
|-- .dockerignore
|-- .gitignore
|-- Dockerfile
|-- README.md
|-- app.py
|-- compose.yaml
|-- requirements.txt
|-- static/
|   |-- app.js
|   `-- style.css
|-- templates/
|   `-- index.html
`-- tests/
    `-- test_app.py
```
