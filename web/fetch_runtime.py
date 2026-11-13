import http.client
import json
import sys
import urllib.error
import urllib.request
from importlib.metadata import version
from pathlib import Path

CDN_URL = "https://pygame-web.github.io/cdn/"
PYTHON_BUILD = "312"
ABI_TAG = f"cp{PYTHON_BUILD}"
API_TAG = "wasm32_bi_emscripten"
PACKAGES = ["pygame"]
DOWNLOAD_ATTEMPTS = 3

pygbag_version = version("pygbag")

RUNTIME_FILES = [
    f"{pygbag_version}/pythons.js",
    f"{pygbag_version}/cpythonrc.py",
    f"{pygbag_version}/cpython{PYTHON_BUILD}/main.js",
    f"{pygbag_version}/cpython{PYTHON_BUILD}/main.wasm",
    f"{pygbag_version}/cpython{PYTHON_BUILD}/main.data",
    f"{pygbag_version}/default.tmpl",
    f"{pygbag_version}/empty.html",
    f"{pygbag_version}/empty.ogg",
    f"{pygbag_version}/favicon.png",
    "vt.js",
    "vtx.js",
    "vt/xterm.js",
    "vt/xterm.css",
    "vt/xterm-addon-image.js",
]


def read_url(url):
    for attempt in range(1, DOWNLOAD_ATTEMPTS + 1):
        try:
            with urllib.request.urlopen(url) as response:
                return response.read()
        except (http.client.IncompleteRead, urllib.error.URLError):
            if attempt == DOWNLOAD_ATTEMPTS:
                raise
            print(f"retry {attempt}: {url}")


def download(path, out_dir):
    target = out_dir / path
    target.parent.mkdir(parents=True, exist_ok=True)
    data = read_url(CDN_URL + path)
    target.write_bytes(data)
    print(f"{path} ({len(data)} B)")
    return data


def fetch_runtime(out_dir):
    for path in RUNTIME_FILES:
        download(path, out_dir)

    index_name = f"index-{pygbag_version}-{ABI_TAG}.json"
    index = json.loads(download(index_name, out_dir))
    for package in PACKAGES:
        wheel = index[package].replace("<abi>", ABI_TAG).replace("<api>", API_TAG)
        download(wheel, out_dir)

    index["-CDN-"] = "/cdn/"
    (out_dir / index_name).write_text(json.dumps(index, indent=4))


if __name__ == "__main__":
    fetch_runtime(Path(sys.argv[1]) / "cdn")
