# Asteroids

Prosta gra w stylu Asteroids napisana w Pythonie 3.13 i pygame 2.6.1.

## Uruchomienie lokalne

```bash
uv venv
source .venv/bin/activate
uv sync
uv run main.py
```

## Build Docker

Obraz kompiluje grę do WebAssembly (pygbag) i serwuje ją przez nginx na porcie 80.

```bash
docker build -t asteroids-web .
docker run --rm -p 8080:80 asteroids-web
```

Gra jest dostępna pod adresem http://localhost:8080. Kliknij w okno, żeby ją uruchomić.

Osadzenie gry w innej stronie:

```html
<iframe src="https://<adres-aplikacji>/" width="1280" height="720"></iframe>
```

## Wdrożenie na Azure App Service

```bash
az group create --name asteroids-rg --location westeurope
az acr create --resource-group asteroids-rg --name <nazwa-acr> --sku Basic --admin-enabled true
az acr build --registry <nazwa-acr> --image asteroids-web:latest .

az appservice plan create --resource-group asteroids-rg --name asteroids-plan --is-linux --sku B1
az webapp create --resource-group asteroids-rg --plan asteroids-plan --name <nazwa-aplikacji> \
    --deployment-container-image-name <nazwa-acr>.azurecr.io/asteroids-web:latest
az webapp config appsettings set --resource-group asteroids-rg --name <nazwa-aplikacji> \
    --settings WEBSITES_PORT=80
```
