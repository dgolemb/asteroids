FROM python:3.13-slim AS build

COPY --from=ghcr.io/astral-sh/uv:0.13.8 /uv /bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --only-dev --no-install-project

COPY web/fetch_runtime.py web/
RUN uv run --no-sync python web/fetch_runtime.py /app/www

COPY web/asteroids.tmpl web/
COPY *.py asteroids/
COPY textures asteroids/textures
RUN PYGBAG_VERSION=$(uv run --no-sync python -c "from importlib.metadata import version; print(version('pygbag'))") \
    && uv run --no-sync pygbag --build \
        --cdn /cdn/${PYGBAG_VERSION}/ \
        --template web/asteroids.tmpl \
        --icon /app/www/cdn/${PYGBAG_VERSION}/favicon.png \
        asteroids \
    && cp -r asteroids/build/web/. /app/www/


FROM nginx:1.30-alpine AS runtime

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/www /usr/share/nginx/html

EXPOSE 80
