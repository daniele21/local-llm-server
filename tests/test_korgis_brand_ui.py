from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "src" / "local_llm_server" / "static"
DESIGN_LOGOS = ROOT / "design" / "brand" / "logo"


def test_runtime_korgis_assets_match_canonical_brand_sources() -> None:
    pairs = {
        "korgis-mark.png": "korgis-mark.png",
        "korgis-app-icon.png": "korgis-app-icon.png",
        "korgis-horizontal.png": "korgis-horizontal.png",
        "korgis-reversed-dark.png": "korgis-reversed-dark.png",
    }

    for runtime_name, source_name in pairs.items():
        assert (STATIC / runtime_name).read_bytes() == (DESIGN_LOGOS / source_name).read_bytes()


def test_korgis_brand_bootstraps_before_i18n_and_control_plane() -> None:
    index = (STATIC / "index.html").read_text(encoding="utf-8")
    config = (STATIC / "config.js").read_text(encoding="utf-8")
    i18n = (STATIC / "i18n.js").read_text(encoding="utf-8")
    shell = (STATIC / "control-plane-shell.js").read_text(encoding="utf-8")

    assert index.index('/static/config.js') < index.index('/static/i18n.js')
    assert "applyKorgisRuntimeBrand" in config
    assert "document.title = 'Korgis'" in config
    assert "favicon.href = '/static/korgis-app-icon.png'" in config
    assert "logo.src = '/static/korgis-mark.png'" in config
    assert "brandName.textContent = 'Korgis'" in config
    assert "descriptor.textContent = 'Local AI control plane'" in config
    assert '"title": "Korgis"' in i18n
    assert '".sidebar-brand-text h1": "Korgis"' in i18n
    assert "Local LLM Studio" not in i18n
    assert "document.title = `Korgis · ${item.label}`" in shell


def test_korgis_visual_layer_uses_shared_tokens_and_retires_decorative_glow() -> None:
    config = (STATIC / "config.js").read_text(encoding="utf-8")
    css = (STATIC / "brand.css").read_text(encoding="utf-8")

    assert "['data-korgis-brand', '/static/brand.css']" in config
    assert "--color-primary: var(--ds-electric-blue)" in css
    assert "--color-accent: var(--ds-teal)" in css
    assert "--bg-app: var(--ds-bg)" in css
    assert ".glow-bg" in css
    assert "display: none !important" in css
    assert "box-shadow: none !important" in css


def test_brand_contract_records_browser_rollout_and_technical_boundary() -> None:
    brand = json.loads((ROOT / "design" / "brand-kit.json").read_text(encoding="utf-8"))
    implementation = brand["implementation"]

    assert brand["product_name"] == "Korgis"
    assert brand["positioning"]["technical_repository_name"] == "Local LLM Server"
    assert implementation["runtime_rollout_status"] == "implemented"
    assert implementation["current_runtime_surface_name"] == "Korgis"
    assert implementation["current_runtime_logo"].endswith("/korgis-mark.png")
    assert implementation["current_runtime_favicon"].endswith("/korgis-app-icon.png")
    assert "non-canonical parser fallback" in implementation["legacy_bootstrap_markup"]


def test_legacy_index_brand_literals_are_explicitly_noncanonical_fallback() -> None:
    index = (STATIC / "index.html").read_text(encoding="utf-8")
    brand = json.loads((ROOT / "design" / "brand-kit.json").read_text(encoding="utf-8"))

    assert "Local LLM Studio" in index
    assert "pre-rollout literals" in brand["implementation"]["legacy_bootstrap_markup"]
    assert index.index('class="sidebar-brand"') < index.index('/static/config.js')
