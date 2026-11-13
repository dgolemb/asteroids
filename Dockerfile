FROM python:3.13-slim AS build

COPY --from=ghcr.io/astral-sh/uv:0.13.8 /uv /bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --only-dev --no-install-project

COPY *.py asteroids/
COPY textures asteroids/textures
RUN uv run --no-sync pygbag --build asteroids


FROM nginx:1.27-alpine AS runtime

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/asteroids/build/web /usr/share/nginx/html

EXPOSE 80
