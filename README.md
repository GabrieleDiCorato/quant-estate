# QUANT ESTATE - HOUSING MARKET ANALYSIS

Your quantitative real estate toolkit.

---

## Project Features

The architecture aggregates and analyzes real estate data with a focus on identifying opportunities and fair pricing.

- Selenium-based scrapers for Italian listings (Immobiliare.it) with detailed attributes
- Typed data models with Pydantic v2 (ListingId, ListingDetails, ListingRecord)
- Pluggable storage: MongoDB or CSV via a common Storage interface
- Environment-scoped configuration via .env files
- Dependency and build management with uv

---

## Getting Started

### Prerequisites

- Python 3.12+
- uv (package and environment manager)

We use uv for dependency management and builds. See the uv installation guide: https://docs.astral.sh/uv/getting-started/installation/

Optional VS Code extension: UV Wingman — https://marketplace.visualstudio.com/items?itemName=DJSaunders1997.uv-wingman

### Setup (Windows PowerShell)

1) Install dependencies (includes dev tools like ipykernel):

```powershell
uv sync --all-groups
```

2) Ensure a Python 3.12 runtime is available (only if missing):

```powershell
uv python install 3.12
```

3) Configure runtime environment (optional, defaults shown):

```powershell
$env:QE_ENV = "dev"; $env:QE_CONF_FOLDER = "sources/resources"
```

Expected config files (by environment):
- sources/resources/storage.dev.env
- sources/resources/scraper_imm_id.dev.env
- sources/resources/scraper_imm_listing.dev.env

---

## Running Jupyter Notebooks

From a terminal:

```powershell
uv run --with jupyter jupyter lab
```

In VS Code:
- Open a notebook in the `notebooks/` folder
- Select a Python kernel backed by the uv environment created by `uv sync`

Notebook hygiene (optional): clean before committing to reduce diffs.

```powershell
uv run nb-clean clean --remove-empty-cells --remove-all-notebook-metadata path\to\notebook.ipynb
```

See uv + Jupyter docs: https://docs.astral.sh/uv/guides/integration/jupyter/

---

## Build

Build a distribution:

```powershell
uv build
```

Install the produced archive from `dist/` using pip or uv:

```powershell
pip install dist/quant_estate-0.1.0.tar.gz
```

```powershell
uv pip install dist/quant_estate-0.1.0.tar.gz
```

---

## Notes

- Respect target sites: add realistic delays and avoid aggressive scraping
- Rotate user agents if blocked and check robots.txt

---

## License

BSL 1.1 License. See `LICENSE` for details.

---
