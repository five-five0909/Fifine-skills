#!/usr/bin/env python3
import argparse
import json
import re
import sys
from pathlib import Path

REGISTRY_PATH = Path(__file__).resolve().parent.parent / "references" / "figure-registry.json"
ROUTES = {"nature-figure", "academic-figure-skill", "scientific-figure-making", "stem-illustration", "tech-diagrams", "generative-ui", "baoyu-image-gen"}
BACKENDS = {"r", "r-complexheatmap", "python", "graphviz-svg", "either", "not_applicable"}
STYLES = {"NMI_PASTEL", "NATURE_CLASSIC", "CNS_RESTRAINED", "NATURE_IMAGING", "NATURE_MATERIAL", "NATURE_CLINICAL", "NATURE_GENOMICS", "NATURE_SYSTEMS"}
REQUIRED_FIELDS = {"id", "category_id", "name", "aliases", "scientific_questions", "evidence_roles", "data_requirements", "statistical_requirements", "best_when", "avoid_when", "required_encodings", "panel_roles", "recommended_backend", "fallback_backend", "default_spec_owner", "style_profiles", "integrity_checks", "output_formats", "related_figure_ids"}


def load_registry(path=REGISTRY_PATH):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def normalize(text):
    return re.sub(r"[^a-z0-9@]+", " ", str(text).lower()).strip()


def tokens(text):
    return {token for token in normalize(text).split() if len(token) > 1}


def validate_registry(data):
    errors = []
    categories = data.get("categories", [])
    figures = data.get("figure_types", [])
    if data.get("category_count") != 18 or len(categories) != 18:
        errors.append("registry must contain exactly 18 categories")
    if data.get("figure_type_count") != 180 or len(figures) != 180:
        errors.append("registry must contain exactly 180 figure types")
    category_ids = [item.get("id") for item in categories]
    figure_ids = [item.get("id") for item in figures]
    if len(set(category_ids)) != len(category_ids):
        errors.append("category IDs must be unique")
    if len(set(figure_ids)) != len(figure_ids):
        errors.append("figure IDs must be unique")
    category_set = set(category_ids)
    figure_set = set(figure_ids)
    for category in categories:
        missing = {"id", "name", "description", "figure_type_ids"} - set(category)
        if missing:
            errors.append(f"category {category.get('id')} missing {sorted(missing)}")
        for figure_id in category.get("figure_type_ids", []):
            if figure_id not in figure_set:
                errors.append(f"category {category.get('id')} references unknown {figure_id}")
    for figure in figures:
        figure_id = figure.get("id", "<unknown>")
        missing = REQUIRED_FIELDS - set(figure)
        if missing:
            errors.append(f"{figure_id} missing {sorted(missing)}")
        if figure.get("category_id") not in category_set:
            errors.append(f"{figure_id} references unknown category")
        if figure.get("default_spec_owner") not in ROUTES:
            errors.append(f"{figure_id} has invalid spec owner")
        if figure.get("recommended_backend") not in BACKENDS or figure.get("fallback_backend") not in BACKENDS:
            errors.append(f"{figure_id} has invalid backend")
        if not set(figure.get("style_profiles", [])).issubset(STYLES):
            errors.append(f"{figure_id} has invalid style profile")
        if not figure.get("best_when") or not figure.get("avoid_when"):
            errors.append(f"{figure_id} requires best_when and avoid_when")
        if not figure.get("integrity_checks"):
            errors.append(f"{figure_id} requires integrity checks")
        for related in figure.get("related_figure_ids", []):
            if related not in figure_set:
                errors.append(f"{figure_id} references unknown related figure {related}")
        serialized = json.dumps(figure, ensure_ascii=False).lower()
        if "magpie-image" in serialized and any(word in serialized for word in ("command", "endpoint", "payload", "model_id")):
            errors.append(f"{figure_id} must not define a magpie-image API schema")
    return errors


def haystack(figure):
    parts = [figure["id"], figure["name"], figure["category_id"], figure["default_spec_owner"], figure["recommended_backend"]]
    for key in ("aliases", "scientific_questions", "evidence_roles", "best_when", "avoid_when", "style_profiles"):
        parts.extend(figure.get(key, []))
    parts.append(json.dumps(figure.get("data_requirements", {}), ensure_ascii=False))
    return normalize(" ".join(map(str, parts)))


def search_figures(data, query="", category=None, evidence_role=None, data_feature=None, route=None, backend=None, limit=20):
    query_tokens = tokens(query)
    matches = []
    for figure in data["figure_types"]:
        if category and figure["category_id"] != category:
            continue
        if evidence_role and evidence_role not in figure["evidence_roles"]:
            continue
        if data_feature and not figure["data_requirements"].get(data_feature):
            continue
        if route and figure["default_spec_owner"] != route:
            continue
        if backend and figure["recommended_backend"] != backend and figure["fallback_backend"] != backend:
            continue
        text = haystack(figure)
        score = sum(1 for token in query_tokens if token in text)
        if query_tokens and score == 0:
            continue
        matches.append((score, figure["id"], figure))
    matches.sort(key=lambda item: (-item[0], item[1]))
    return [item[2] | {"search_score": item[0]} for item in matches[:limit]]


def compatible(figure, available):
    requirements = figure["data_requirements"]
    reasons = []
    mapping = {
        "probabilities": "probabilities",
        "labels": "labels",
        "embeddings": "embeddings",
        "gradients": "gradients",
        "images": "images",
        "timestamps": "timestamps",
        "pairing_required": "pairing_ids",
        "seeds_or_folds": "seeds_or_folds",
    }
    for requirement, supplied in mapping.items():
        if requirements.get(requirement) and not available.get(supplied, False):
            reasons.append(f"requires {supplied}")
    return reasons


def recommend(data, request, limit=3):
    question = request.get("scientific_question", "")
    evidence_roles = set(request.get("evidence_roles", []))
    available = request.get("available_data", {})
    target_venue = normalize(request.get("target_venue", ""))
    question_tokens = tokens(question)
    ranked = []
    rejected = []
    for figure in data["figure_types"]:
        incompatibilities = compatible(figure, available)
        if incompatibilities:
            rejected.append({"id": figure["id"], "name": figure["name"], "reasons": incompatibilities})
            continue
        text = haystack(figure)
        question_match = sum(4 for token in question_tokens if token in text)
        role_match = sum(6 for role in evidence_roles if role in figure["evidence_roles"] or normalize(role) in text)
        data_match = sum(2 for key, value in available.items() if value and normalize(key) in text)
        venue_fit = 3 if any(name in target_venue for name in ("nature", "neurips", "icml", "iclr", "acl", "cvpr", "aaai", "tpami", "jmlr")) else 0
        r_preference = 2 if figure["recommended_backend"].startswith("r") else 0
        style_fit = 2 if "NMI_PASTEL" in figure["style_profiles"] or "NATURE_CLASSIC" in figure["style_profiles"] else 0
        total = question_match + role_match + data_match + venue_fit + r_preference + style_fit
        ranked.append((total, figure["id"], {
            "id": figure["id"], "name": figure["name"], "category_id": figure["category_id"],
            "score": total,
            "score_breakdown": {"question_match": question_match, "evidence_role_match": role_match, "data_match": data_match, "venue_fit": venue_fit, "r_preference": r_preference, "style_fit": style_fit},
            "scientific_justification": figure["best_when"][0],
            "required_data": figure["data_requirements"],
            "avoid_when": figure["avoid_when"],
            "recommended_backend": figure["recommended_backend"],
            "fallback_backend": figure["fallback_backend"],
            "default_spec_owner": figure["default_spec_owner"],
            "style_profiles": figure["style_profiles"],
            "integrity_checks": figure["integrity_checks"],
        }))
    ranked.sort(key=lambda item: (-item[0], item[1]))
    return {"recommendations": [item[2] for item in ranked[:limit]], "rejected_count": len(rejected), "rejected_examples": rejected[:10]}


def print_json(value):
    print(json.dumps(value, ensure_ascii=False, indent=2))


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate and query the AI paper figure registry.")
    parser.add_argument("--registry", default=str(REGISTRY_PATH))
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("validate")
    subparsers.add_parser("categories")
    show = subparsers.add_parser("show")
    show.add_argument("figure_id")
    search = subparsers.add_parser("search")
    search.add_argument("--question", default="")
    search.add_argument("--category")
    search.add_argument("--evidence-role")
    search.add_argument("--data-feature")
    search.add_argument("--route", choices=sorted(ROUTES))
    search.add_argument("--backend", choices=sorted(BACKENDS))
    search.add_argument("--limit", type=int, default=20)
    recommend_parser = subparsers.add_parser("recommend")
    recommend_parser.add_argument("--input-json", required=True)
    recommend_parser.add_argument("--limit", type=int, default=3)
    args = parser.parse_args(argv)
    data = load_registry(args.registry)
    if args.command == "validate":
        errors = validate_registry(data)
        if errors:
            print_json({"status": "failed", "errors": errors})
            return 1
        print_json({"status": "ok", "categories": len(data["categories"]), "figure_types": len(data["figure_types"])})
        return 0
    if args.command == "categories":
        print_json(data["categories"])
        return 0
    if args.command == "show":
        figure = next((item for item in data["figure_types"] if item["id"] == args.figure_id), None)
        if not figure:
            print_json({"error": f"unknown figure ID: {args.figure_id}"})
            return 2
        print_json(figure)
        return 0
    if args.command == "search":
        print_json(search_figures(data, args.question, args.category, args.evidence_role, args.data_feature, args.route, args.backend, args.limit))
        return 0
    request = json.loads(Path(args.input_json).read_text(encoding="utf-8"))
    print_json(recommend(data, request, args.limit))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
