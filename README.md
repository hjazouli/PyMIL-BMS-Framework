# PyXIL-BMS: Modular BMS Validation Framework

[![PyXIL-BMS MIL Campaign](https://github.com/hjazouli/PyMIL-BMS-Framework/actions/workflows/mil_campaign.yml/badge.svg)](https://github.com/hjazouli/PyMIL-BMS-Framework/actions/workflows/mil_campaign.yml)

Professional Python-based Model-in-the-Loop (MIL) and Hardware-in-the-Loop (HIL) automation for automotive software validation.

## Phase 1: Infrastructure Hardening (Complete)

- **Abstract Base Layer**: Decoupled test logic from execution interfaces (`framework/base/`).
- **MIL Implementation**: High-speed algorithmic verification core (`framework/mil/`).
- **Structured Logging**: JSON-line event logging for traceability.
- **Reproducible Setup**: formal `setup.py` and dependency tracking.
- **CI/CD**: Automated linting, type checking, and test campaign execution via GitHub Actions.

## 1. Installation

```bash
# Clone the repository
git clone https://github.com/hjazouli/PyMIL-BMS-Framework.git
cd PyMIL-BMS-Framework

# Install in editable mode with development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

## 2. Usage

### MIL Campaign execution

```bash
python run_campaign.py
```

### Running Framework Unit Tests

```bash
pytest tests/unit/
```

### Manual MIL Test (Legacy)

```bash
python run_mil.py
```

## 3. Architecture

- **`framework/base/`**: Abstract interfaces (Stimulator, Measurement, Verdict, etc.)
- **`framework/mil/`**: MIL-specific implementations using internal dictionary bus.
- **`framework/shared/`**: Shared utilities like the structured logger.
- **`mut/`**: The Model Under Test (BMS algorithmic model).
- **`test_cases/`**: Test cases that depend only on `framework.base`.

Refer to `docs/` for detailed design specifications.
