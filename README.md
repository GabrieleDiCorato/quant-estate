# 🏡 QUANT ESTATE - HOUSING MARKET ANALYSIS

Your quantitative real estate agent.

---

## 📦 Project Features

Our flexible architecture allows the aggregation and analysis of a vast range of data pertaining the real estate business.
The core logics focus on selecting the best investment opportunities and evaluate fair prices.

We offer:
- Web scraping of italian real estate listings with detailed attributes;
- 

Our application is cleanly organized and easily extendable to extract best value from data and real estate.

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+

We use [uv](https://github.com/astral-sh/uv) for dependency management and to build the project. If you want to contribute, please follow the setup instructions.

### 🔧 Installing `uv`

See the [official documentation](https://docs.astral.sh/uv/getting-started/installation/) to install uv on your machine. There is a very clear [documentation](https://docs.astral.sh/uv/) available.

IDE extension are also available, like [UV Wingman](https://marketplace.visualstudio.com/items?itemName=DJSaunders1997.uv-wingman) for Visual Studio Code. 


### 📁 Setting Up the Environment

See [Working on Projects](https://docs.astral.sh/uv/guides/projects/#uvlock) to understand how to work uv project.

To complete your setup:

1. Install all dependencies declared by the project: `uv sync --all-groups`
2. With the previous step, you also installed [nb-clean](https://github.com/srstevenson/nb-clean), a utility to cleanup jupyther notebooks. To simplify collaborating on notebooks, they should be cleaned up before being committed into the project.\
You can setup git to automatically use a cleaned-up version of your notebook when you stage it. Open your `tmp/.git/config` file and append the following:
```bash
[filter "nb-clean"]
	clean = nb-clean clean --remove-empty-cells --remove-all-notebook-metadata
```

### 📓 Running Jupyter Notebooks

Read the [documentation](https://docs.astral.sh/uv/guides/integration/jupyter/).

If you are using the command line, just run:

```bash
uv run --with jupyter jupyter lab
```

If you are using Visual Studio Code, carefully read [Using Jupyter From VS Code](https://docs.astral.sh/uv/guides/integration/jupyter/#using-jupyter-from-vs-code).

### 📦 Building the Project

To build the project and create a distribution package:

```bash
uv build
```

This will create a distribution archive in the `dist` directory that can be installed using pip or uv:

```bash
# Using pip
pip install dist/quant_estate-0.1.0.tar.gz

# Using uv
uv pip install dist/quant_estate-0.1.0.tar.gz
```

---

## ⚙️ Usage



---

## 📝 Notes

* Avoid scraping too aggressively. Add realistic delays.
* Consider rotating headers or proxies if you're blocked.
* Always check the site's `robots.txt` for ethical scraping compliance.

---

## 📄 License

BSL 1.1 License. See `LICENSE` file for details.

---
