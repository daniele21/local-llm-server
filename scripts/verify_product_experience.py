#!/usr/bin/env python3
"""Zero-dependency validation for the optional product-ui experience contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

PLACEHOLDER_MARKERS = ("<REPLACE", "<PROJECT_")
REQUIRED_STATES = {"loading", "empty", "error", "disabled"}
REQUIRED_PRINCIPLES = {
    "user_task_model_over_internal_architecture",
    "progressive_disclosure",
    "sensible_defaults",
    "clear_primary_action_hierarchy",
    "platform_appropriate",
    "bounded_information_density",
    "actionable_error_recovery",
}
REQUIRED_DECISION_MODEL = {
    "user_outcome_first",
    "task_model_before_layout",
    "hierarchy_before_visual_polish",
    "states_before_motion",
    "motion_requires_purpose",
    "evidence_before_completion",
}
REQUIRED_ACCESSIBILITY = {
    "keyboard_when_applicable",
    "focus_visibility_order",
    "assistive_semantics",
    "text_scaling_when_applicable",
    "no_color_only_critical_meaning",
    "reduced_motion_when_applicable",
}
REQUIRED_MOTION_FLAGS = {
    "purpose_required",
    "frequent_interactions_are_restrained",
    "gesture_motion_tracks_input",
    "performance_over_decorative_complexity",
    "reduced_motion",
}
REQUIRED_MOTION_PURPOSES = {
    "feedback",
    "continuity",
    "spatial_relationship",
    "state_transition",
    "progress",
    "attention",
}
REQUIRED_GRAPHICS_FLAGS = {
    "functional_before_decorative",
    "ui_understandable_without_decorative_imagery",
}
REQUIRED_EVIDENCE = {
    "bounded_ci_retention",
    "identity_with_source_build_environment",
    "zero_residue_after_ui_e2e",
}
REQUIRED_COLORS = {
    "surface",
    "surface_elevated",
    "text_primary",
    "text_secondary",
    "primary",
    "success",
    "warning",
    "error",
    "border",
    "focus",
}
REQUIRED_STYLE = {"iconography", "motion", "imagery", "voice_microcopy"}
REQUIRED_DURATION_TOKENS = {"instant", "fast", "standard", "large"}
REQUIRED_EASING_TOKENS = {"enter", "exit", "move"}
REQUIRED_SPRING_TOKENS = {"default", "bounce"}
E2E_VALUES = {"required", "recommended", "n/a", "na"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--template-mode", action="store_true")
    return parser.parse_args()


def load_json(path: Path, errors: list[str], label: str) -> dict:
    if not path.is_file():
        errors.append(f"missing required file: {path.name if path.parent.name == 'design' else path}")
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        errors.append(f"invalid {label}: {exc}")
        return {}
    if not isinstance(data, dict):
        errors.append(f"{label} must be a JSON object")
        return {}
    return data


def unresolved(value: object) -> bool:
    if not isinstance(value, str):
        return False
    return any(marker in value for marker in PLACEHOLDER_MARKERS)


def find_placeholders(value: object, path: str = "") -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            found.extend(find_placeholders(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            child_path = f"{path}[{index}]"
            found.extend(find_placeholders(child, child_path))
    elif unresolved(value):
        found.append(path or "<root>")
    return found


def require_text(section: dict, key: str, errors: list[str], prefix: str, template_mode: bool) -> None:
    value = section.get(key)
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{prefix}.{key} must be a non-empty string")
    elif not template_mode and unresolved(value):
        errors.append(f"unresolved placeholder in {prefix}.{key}")


def require_true(section: dict, key: str, errors: list[str], prefix: str) -> None:
    if section.get(key) is not True:
        errors.append(f"{prefix}.{key} must be true")


def require_nonempty_list(section: dict, key: str, errors: list[str], prefix: str) -> list:
    value = section.get(key)
    if not isinstance(value, list) or not value:
        errors.append(f"{prefix}.{key} must be a non-empty list")
        return []
    return value


def require_text_map(
    section: dict,
    key: str,
    required_keys: set[str],
    errors: list[str],
    prefix: str,
    template_mode: bool,
) -> None:
    value = section.get(key)
    if not isinstance(value, dict):
        errors.append(f"{prefix}.{key} must be an object")
        return
    missing = sorted(required_keys - set(value))
    if missing:
        errors.append(f"{prefix}.{key} missing: " + ", ".join(missing))
    for child_key in sorted(required_keys & set(value)):
        require_text(value, child_key, errors, f"{prefix}.{key}", template_mode)


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    errors: list[str] = []
    warnings: list[str] = []

    baseline_path = root / ".engineering" / "baseline.json"
    baseline = load_json(baseline_path, errors, "baseline.json")
    profiles = baseline.get("profiles") if isinstance(baseline, dict) else []
    if not isinstance(profiles, list):
        profiles = []

    applicable = args.template_mode or "product-ui" in profiles

    print("Product experience contract check")
    print(f"root: {root}")

    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        print(f"RESULT: FAIL ({len(errors)} error(s))")
        return 1

    if not applicable:
        print("SKIP: product-ui profile not adopted")
        print("RESULT: PASS (not applicable)")
        return 0

    design_dir = root / "design"
    ux = load_json(design_dir / "ux-contract.json", errors, "design/ux-contract.json")
    brand = load_json(design_dir / "brand-kit.json", errors, "design/brand-kit.json")

    if ux:
        if ux.get("schema_version") != 1:
            errors.append("ux-contract.schema_version must be 1")
        require_text(ux, "contract_version", errors, "ux-contract", args.template_mode)
        if ux.get("applicable") is not True:
            errors.append("ux-contract.applicable must be true when product-ui is adopted")

        source = ux.get("design_source_of_truth")
        if not isinstance(source, dict):
            errors.append("ux-contract.design_source_of_truth must be an object")
        else:
            require_text(source, "type", errors, "design_source_of_truth", args.template_mode)
            require_text(source, "location", errors, "design_source_of_truth", args.template_mode)

        context = ux.get("experience_context")
        if not isinstance(context, dict):
            errors.append("ux-contract.experience_context must be an object")
        else:
            for key in ("primary_users", "primary_jobs", "primary_surfaces"):
                require_nonempty_list(context, key, errors, "experience_context")

        decision_model = ux.get("decision_model")
        if not isinstance(decision_model, dict):
            errors.append("ux-contract.decision_model must be an object")
            decision_model = {}
        for key in sorted(REQUIRED_DECISION_MODEL):
            require_true(decision_model, key, errors, "decision_model")

        principles = ux.get("principles")
        if not isinstance(principles, dict):
            errors.append("ux-contract.principles must be an object")
            principles = {}
        for key in sorted(REQUIRED_PRINCIPLES):
            require_true(principles, key, errors, "principles")

        states = set(ux.get("critical_states") or [])
        missing_states = sorted(REQUIRED_STATES - states)
        if missing_states:
            errors.append("ux-contract.critical_states missing: " + ", ".join(missing_states))

        accessibility = ux.get("accessibility")
        if not isinstance(accessibility, dict):
            errors.append("ux-contract.accessibility must be an object")
            accessibility = {}
        require_text(accessibility, "target", errors, "accessibility", args.template_mode)
        for key in sorted(REQUIRED_ACCESSIBILITY):
            require_true(accessibility, key, errors, "accessibility")

        adaptive = ux.get("adaptive_layout")
        if not isinstance(adaptive, dict):
            errors.append("ux-contract.adaptive_layout must be an object")
        elif adaptive.get("applicable") is True:
            require_nonempty_list(adaptive, "supported_contexts", errors, "adaptive_layout")

        system = ux.get("design_system")
        if not isinstance(system, dict):
            errors.append("ux-contract.design_system must be an object")
        else:
            require_text(system, "component_source", errors, "design_system", args.template_mode)
            require_text(system, "brand_tokens", errors, "design_system", args.template_mode)
            require_true(system, "reuse_existing_semantic_component_first", errors, "design_system")

        motion = ux.get("motion")
        if not isinstance(motion, dict):
            errors.append("ux-contract.motion must be an object")
            motion = {}
        for key in sorted(REQUIRED_MOTION_FLAGS):
            require_true(motion, key, errors, "motion")
        purposes = set(motion.get("supported_purposes") or [])
        missing_purposes = sorted(REQUIRED_MOTION_PURPOSES - purposes)
        if missing_purposes:
            errors.append("ux-contract.motion.supported_purposes missing: " + ", ".join(missing_purposes))

        graphics = ux.get("graphics")
        if not isinstance(graphics, dict):
            errors.append("ux-contract.graphics must be an object")
            graphics = {}
        for key in sorted(REQUIRED_GRAPHICS_FLAGS):
            require_true(graphics, key, errors, "graphics")
        require_nonempty_list(graphics, "supported_roles", errors, "graphics")

        journeys = ux.get("critical_journeys")
        if not isinstance(journeys, list) or not journeys:
            errors.append("ux-contract.critical_journeys must contain at least one journey")
        else:
            for index, journey in enumerate(journeys):
                if not isinstance(journey, dict):
                    errors.append(f"critical_journeys[{index}] must be an object")
                    continue
                require_text(journey, "id", errors, f"critical_journeys[{index}]", args.template_mode)
                require_text(journey, "name", errors, f"critical_journeys[{index}]", args.template_mode)
                e2e = journey.get("e2e")
                if isinstance(e2e, str) and not unresolved(e2e) and e2e.lower() not in E2E_VALUES:
                    errors.append(f"critical_journeys[{index}].e2e must be required, recommended or n/a")
                elif not isinstance(e2e, str):
                    errors.append(f"critical_journeys[{index}].e2e must be a string")

        views = ux.get("reference_views")
        if not isinstance(views, list) or not views:
            errors.append("ux-contract.reference_views must contain at least one key reference view")

        evidence = ux.get("evidence")
        if not isinstance(evidence, dict):
            errors.append("ux-contract.evidence must be an object")
            evidence = {}
        for key in sorted(REQUIRED_EVIDENCE):
            require_true(evidence, key, errors, "evidence")

    if brand:
        if brand.get("schema_version") != 1:
            errors.append("brand-kit.schema_version must be 1")
        require_text(brand, "contract_version", errors, "brand-kit", args.template_mode)
        require_text(brand, "product_name", errors, "brand-kit", args.template_mode)

        assets = brand.get("assets")
        if not isinstance(assets, dict):
            errors.append("brand-kit.assets must be an object")
        else:
            for key in ("logo_primary", "logo_compact", "logo_monochrome", "app_icon", "favicon"):
                require_text(assets, key, errors, "assets", args.template_mode)

        tokens = brand.get("tokens")
        if not isinstance(tokens, dict):
            errors.append("brand-kit.tokens must be an object")
            tokens = {}
        colors = tokens.get("colors") if isinstance(tokens, dict) else None
        if not isinstance(colors, dict):
            errors.append("brand-kit.tokens.colors must be an object")
            colors = {}
        missing_colors = sorted(REQUIRED_COLORS - set(colors))
        if missing_colors:
            errors.append("brand-kit.tokens.colors missing: " + ", ".join(missing_colors))
        require_text(tokens, "typography", errors, "tokens", args.template_mode)
        require_text(tokens, "spacing", errors, "tokens", args.template_mode)

        style = brand.get("style")
        if not isinstance(style, dict):
            errors.append("brand-kit.style must be an object")
            style = {}
        for key in sorted(REQUIRED_STYLE):
            require_text(style, key, errors, "style", args.template_mode)

        motion_tokens = brand.get("motion_tokens")
        if not isinstance(motion_tokens, dict):
            errors.append("brand-kit.motion_tokens must be an object")
            motion_tokens = {}
        require_text_map(
            motion_tokens,
            "durations",
            REQUIRED_DURATION_TOKENS,
            errors,
            "motion_tokens",
            args.template_mode,
        )
        require_text_map(
            motion_tokens,
            "easing",
            REQUIRED_EASING_TOKENS,
            errors,
            "motion_tokens",
            args.template_mode,
        )
        require_text_map(
            motion_tokens,
            "spring",
            REQUIRED_SPRING_TOKENS,
            errors,
            "motion_tokens",
            args.template_mode,
        )
        require_text(
            motion_tokens,
            "reduced_motion_strategy",
            errors,
            "motion_tokens",
            args.template_mode,
        )

    if not args.template_mode:
        for label, data in (("ux-contract", ux), ("brand-kit", brand)):
            for path in find_placeholders(data):
                errors.append(f"unresolved placeholder in {label}.{path}")

    for warning in warnings:
        print(f"WARN: {warning}")
    for error in errors:
        print(f"FAIL: {error}")
    if errors:
        print(f"RESULT: FAIL ({len(errors)} error(s), {len(warnings)} warning(s))")
        return 1
    print(f"RESULT: PASS ({len(warnings)} warning(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
