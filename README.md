# Asteroids

This repository contains the code of an Asteroids-style game, built on top of the guided project from boot.dev. The main goal of the project was to learn programming fundamentals, to build CI/CD pipelines, and to develop software following AI native workflow principles with Claude Code. The second goal was to end up with a playable, enjoyable and widely available game: it runs in a web browser, including on touch devices.

The game is hosted at https://app-asteroids-demo-dg.azurewebsites.net

## Dependencies

Local runtime:

- Python 3.13
- pygame 2.6.1

Development and build tools:

- pygbag 0.9.3 (dev dependency, compiles the game to WebAssembly)
- uv 0.13.8 (package and environment manager)
- unittest from the Python standard library (no additional test framework)

Browser runtime (provided by pygbag, used by the hosted version):

- CPython 3.12
- pygame-ce 2.5.7

Docker base images:

- python:3.13-slim
- ghcr.io/astral-sh/uv:0.13.8
- nginx:1.30-alpine

Infrastructure and CI:

- Terraform 1.15.6
- Terraform provider hashicorp/azurerm 5.15.0
- GitHub Actions: actions/checkout v4, actions/setup-python v5, azure/login v2, docker/setup-buildx-action v3, docker/build-push-action v6, hashicorp/setup-terraform v3

## Running, testing and building

Prepare the environment:

```bash
uv venv
source .venv/bin/activate
uv sync
```

Run the game locally:

```bash
uv run main.py
```

Run the unit tests:

```bash
python -m unittest
```

Build the Docker image and run it:

```bash
docker build -t asteroids-web .
docker run --rm -p 8080:80 asteroids-web
```

The image is built in two stages. The first stage compiles the game to WebAssembly with pygbag and downloads the browser runtime. The second stage serves the result with nginx on port 80. After starting the container the game is available at http://localhost:8080. Click the window to start it.

## Infrastructure

The game is hosted on a free (F1) Linux App Service plan in Azure. The infrastructure is described with Terraform in the `infra` directory and its state is stored in an Azure Storage account.

- The web app runs the `asteroids-web:latest` container image stored in Azure Container Registry.
- The web app pulls the image from the registry with a user-assigned managed identity.
- The web app accepts HTTPS traffic only and forwards it to port 80 of the container.

Two GitHub Actions workflows automate the process:

- `docker.yml` runs the unit tests on pull requests and pushes to `develop`. After a push to `develop` (or a manual run) it builds the image and pushes it to the registry, tagged with the commit SHA and `latest`.
- `terraform.yml` is started manually and runs either `terraform apply` or `terraform destroy`.

## How to play

### Controls

- W accelerates the ship forward and S brakes. When the ship is moving forward, S slows it down first and then starts reversing.
- A and D rotate the ship.
- The ship shoots automatically, there is no fire key.
- ESC pauses the game. In the pause menu use W and S to choose an option and ENTER to confirm.
- On the title screen press ENTER to start or ESC to exit.
- On touch devices the ship is steered with a virtual joystick, and menus are operated by tapping. A pause button is shown on the screen.

### Goal

Survive as long as possible and score as many points as you can. The ship and the asteroids wrap around the edges of the screen, while shots disappear when they leave it.

### Lives

- You start with 3 lives, shown as hearts in the top right corner.
- Colliding with an asteroid costs one life. The asteroid is not destroyed.
- After a hit the ship is invulnerable for 3 seconds and blinks. It cannot shoot during that time.
- When you lose the last life the game ends and the final score with game statistics is shown.

### Asteroids and scoring

- A large asteroid splits into two medium ones, and a medium asteroid splits into two small ones. Small asteroids are destroyed completely.
- Destroying a large asteroid gives 100 points, a medium one 250 points and a small one 500 points.
- Points are multiplied by the level bonus (see below).

### Levels

- Level 1 lasts 30 seconds. Every next level lasts 10 seconds longer than the previous one.
- Every level makes the asteroids 10% faster, shortens the spawn interval to 90% of its previous value, raises the limit of asteroids on screen by 10 (starting at 10, up to a maximum of 100) and adds 10% to the points for destroyed asteroids.

### Powerups

Powerups appear at random places on the screen. They disappear after 10 seconds and blink during the last 3 seconds.

- Shield: protects the ship for 30 seconds. Asteroids touching the shield are destroyed and give points. It does not appear again while a shield is active.
- Weapon: raises the weapon level, up to level 5. Every level increases the fire rate by 25% and enlarges the shots. Level 2 adds two side beams at 90 degrees and level 5 adds two more at 45 degrees. Every pickup restarts the 30 second timer. When the timer runs out the weapon level drops by one.
- Heart: restores one life. If you already have full lives it gives 10000 points instead. Hearts appear every 180 to 300 seconds, while shields and weapons appear every 10 to 25 seconds.
