#!/usr/bin/env python3
"""
Build a Gemini 3.1 Flash generateContent request with auto-injected icons.

Usage:
    python3 build-request.py <prompt_text_file> <output_json> [--icons name1 name2 ...]
    python3 build-request.py <prompt_text_file> <output_json> --base-image overview.png

If --icons is omitted, scans the prompt for any system names matching the
icon registry and injects all matches automatically.

If --icons is provided, only injects the named icons (matched case-insensitively
against registry name or aliases).

If --base-image is provided, the image is embedded as the FIRST part of the
request (before the prompt text), telling Gemini to use it as a reference
layout. Use this for multi-view diagram sets where path-highlight views
must match the overview's exact layout.

The prompt text should reference the icons like:
    "I have provided reference icon images. Use these EXACT icons..."
If no such instruction is found, the script appends a standard icon instruction
block to the prompt automatically.
"""

import argparse
import base64
import json
import os
import sys

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICONS_DIR = os.path.join(SKILL_DIR, "icons")
REGISTRY_FILE = os.path.join(ICONS_DIR, "registry.json")

# Map provider names to icon file path prefixes
PROVIDER_PREFIXES = {
    "gcp": "gcp/",
    "google": "gcp/",
    "azure": "azure/",
    "aws": "aws/",
}

# Universal fallback prefixes always included with any provider filter
FALLBACK_PREFIXES = ["google/material/", "vendor/"]


def load_registry(provider=None):
    """Load icon registry, optionally filtered to a single cloud provider."""
    with open(REGISTRY_FILE) as f:
        icons = json.load(f)["icons"]

    if provider:
        prefix = PROVIDER_PREFIXES.get(provider.lower())
        if not prefix:
            valid = ", ".join(PROVIDER_PREFIXES.keys())
            print(f"WARNING: Unknown provider '{provider}'. Valid: {valid}", file=sys.stderr)
            return icons
        # Also include universal fallback icons (Material Design, vendor)
        icons = [e for e in icons if e["file"].startswith(prefix) or any(e["file"].startswith(fb) for fb in FALLBACK_PREFIXES)]
        print(f"Filtered to provider '{provider}': {len(icons)} icons available")

    return icons


def match_icons(prompt_text, registry, explicit_names=None):
    """Return list of registry entries that match the prompt or explicit names."""
    matched = []
    prompt_lower = prompt_text.lower()

    for entry in registry:
        if explicit_names is not None:
            # Match against explicit --icons list
            all_names = [entry["name"].lower()] + [a.lower() for a in entry.get("aliases", [])]
            if any(n in [x.lower() for x in explicit_names] for n in all_names):
                matched.append(entry)
        else:
            # Auto-detect: check if any name/alias appears in the prompt
            all_names = [entry["name"]] + entry.get("aliases", [])
            if any(name.lower() in prompt_lower for name in all_names):
                matched.append(entry)

    return matched


def build_icon_instruction(matched_icons):
    """Build the instruction text telling Gemini which icons to use."""
    lines = [
        "",
        "IMPORTANT — REFERENCE ICONS:",
        "I have provided reference icon images below. Use these EXACT icons on the corresponding cards.",
        "Reproduce them faithfully — do not substitute with generic icons.",
        ""
    ]
    for i, entry in enumerate(matched_icons, 1):
        lines.append(f"- Image {i} ({entry['description']}): Use as the {entry['name']} icon")

    return "\n".join(lines)


def build_request(prompt_text, matched_icons, aspect_ratio="16:9", image_size=None, base_image_path=None):
    """Build the multi-part Gemini request with text + icon images."""
    parts = []

    # If a base image is provided, embed it first as the reference layout
    if base_image_path:
        with open(base_image_path, "rb") as f:
            base_b64 = base64.b64encode(f.read()).decode()
        parts.append({"text": "REFERENCE DIAGRAM — reproduce this exact layout, positions, card sizes, icons, and labels. Only make the changes described in the prompt below:"})
        parts.append({
            "inlineData": {
                "mimeType": "image/png",
                "data": base_b64
            }
        })

    # Add the prompt text
    parts.append({"text": prompt_text})

    # Add icon images
    for entry in matched_icons:
        icon_path = os.path.join(ICONS_DIR, entry["file"])
        if not os.path.exists(icon_path):
            print(f"WARNING: Icon file not found: {icon_path}", file=sys.stderr)
            continue

        with open(icon_path, "rb") as f:
            icon_b64 = base64.b64encode(f.read()).decode()

        # Add label + image
        parts.append({"text": f"Reference Icon — {entry['name']} ({entry['description']}):"})
        parts.append({
            "inlineData": {
                "mimeType": "image/png",
                "data": icon_b64
            }
        })

    image_config = {"aspectRatio": aspect_ratio}
    if image_size:
        image_config["imageSize"] = image_size

    return {
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": {
            "responseModalities": ["TEXT", "IMAGE"],
            "imageConfig": image_config
        }
    }


def main():
    parser = argparse.ArgumentParser(description="Build Gemini diagram request with auto-injected icons")
    parser.add_argument("prompt_file", help="Path to text file containing the diagram prompt")
    parser.add_argument("output_json", help="Path to write the output JSON request")
    parser.add_argument("--icons", nargs="*", help="Explicit icon names to inject (default: auto-detect from prompt)")
    parser.add_argument("--provider", help="Filter icons to a cloud provider: gcp, azure, aws (prevents cross-provider contamination)")
    parser.add_argument("--aspect-ratio", default="16:9", help="Image aspect ratio (default: 16:9)")
    parser.add_argument("--image-size", choices=("1K", "2K", "4K"), help="Optional image size; Flash Lite roughs use 1K")
    parser.add_argument("--base-image", help="Path to a base diagram PNG to use as layout reference (for multi-view sets)")
    args = parser.parse_args()

    # Read prompt
    with open(args.prompt_file) as f:
        prompt_text = f.read()

    # Load registry (filtered by provider if specified) and match icons
    registry = load_registry(args.provider)
    matched = match_icons(prompt_text, registry, args.icons)

    if matched:
        print(f"Matched {len(matched)} icon(s): {', '.join(e['name'] for e in matched)}")

        # Append icon instruction if not already in prompt
        if "reference icon" not in prompt_text.lower() and "provided reference" not in prompt_text.lower():
            prompt_text += build_icon_instruction(matched)
            print("Auto-appended icon instruction block to prompt")
    else:
        print("No matching icons found in registry")

    # Check base image
    if args.base_image:
        if not os.path.exists(args.base_image):
            print(f"ERROR: Base image not found: {args.base_image}", file=sys.stderr)
            sys.exit(1)
        print(f"Base image: {args.base_image}")

    # Build and write request
    request = build_request(prompt_text, matched, args.aspect_ratio, args.image_size, args.base_image)

    with open(args.output_json, "w") as f:
        json.dump(request, f)

    print(f"Request written to {args.output_json}")
    base_info = f", base image embedded" if args.base_image else ""
    print(f"Prompt length: {len(prompt_text)} chars, {len(matched)} icon(s) embedded{base_info}")


if __name__ == "__main__":
    main()
