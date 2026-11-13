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

## Self-hosting runtime pygbag

Obraz nie korzysta z CDN `pygame-web.github.io` w trakcie działania. Podczas budowania `web/fetch_runtime.py` pobiera runtime przeglądarkowy (CPython 3.12 w WebAssembly, loader, terminal xterm) oraz wheel pygame-ce do katalogu `/cdn/`, który serwuje nginx. Szablon `web/asteroids.tmpl` (kopia `default.tmpl` z pygbag) w `custom_onload` dopisuje `PYGPI=<adres strony>/cdn/` do `orig_argv`, więc indeks i pakiety zawsze pobierane są z tego samego serwera. Musi to nastąpić w JavaScript, zanim wystartuje Python: runtime ustala repozytorium pakietów jeszcze przed wykonaniem kodu Pythona z szablonu. Wartość można nadpisać parametrem `?PYGPI=...` w adresie strony.

W konsoli przeglądarki oczekiwane i nieszkodliwe są: `PyMain: BrowserFS not found` (loader pygbag nie używa już BrowserFS) oraz 404 dla plików `.map` przy otwartych DevTools.

W przeglądarce gra działa na CPython 3.12 i pygame-ce, a nie na Pythonie 3.13 i pygame 2.6.1 używanych lokalnie.

Aktualizacja pygbag:

1. `uv add --dev pygbag==<wersja>`
2. Pobrać `https://pygame-web.github.io/cdn/<wersja>/default.tmpl`, nanieść na niego zmiany z `web/asteroids.tmpl` (blok `PYGPI` na początku `custom_onload`, brak `browserfs.min.js`) i zapisać jako `web/asteroids.tmpl`.
3. Przebudować obraz. `fetch_runtime.py` sam dobiera ścieżki do zainstalowanej wersji pygbag.

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
