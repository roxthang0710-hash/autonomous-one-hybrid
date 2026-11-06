"""Owner-approved dohay_dilam image creative brief builder.

This produces IMAGE BRIEFS, not rendered images and not social posts.
It is the source of truth for Enna illustration prompts until a compatible
graphic-generation integration exists. The obsolete hard-coded card renderer
must not be treated as interchangeable with this style.
"""
import argparse
import json
from pathlib import Path

STYLE_FILE = Path(__file__).resolve().parents[1] / "config" / "dohay_dilam_visual_identity.json"
ACTIVE_STYLE = "dohay_roundhead_doodle_v4"


def load_contract(path=STYLE_FILE):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if (
        data.get("brand") != "Đồ Hay Đi Làm"
        or data.get("handle") != "@dohay_dilam"
        or data.get("visual_style_id") != ACTIVE_STYLE
        or data.get("status") != "owner_selected_primary"
        or data.get("delivery", {}).get("automatic_social_publish_on_creation") is not False
    ):
        raise ValueError("visual-identity-contract-unapproved")
    required = ("recurring_character", "linework", "paper", "composition", "typography", "humor")
    if any(not data.get("style_contract", {}).get(k) for k in required):
        raise ValueError("missing-visual-identity-requirement")
    if len(data.get("negative_prompt", [])) < 5:
        raise ValueError("visual-identity-negative-constraints-missing")
    if data.get("style_revision") != "v4.1_clean_chat_balance":
        raise ValueError("visual-composition-revision-missing")
    modes = data.get("approved_composition_modes") or {}
    if set(modes) != {"scene_doodle", "clean_chat", "practical_ui_tip"}:
        raise ValueError("visual-layout-modes-invalid")
    if not data.get("visual_rules", {}).get("no_repeated_frame"):
        raise ValueError("visual-decoration-guard-missing")
    return data


def build_image_brief(scene, setup, payoff, *, composition, character_emotion,
                      layout_mode="scene_doodle", path=STYLE_FILE):
    data = load_contract(path)
    values = [scene, setup, payoff, composition, character_emotion]
    if any(not isinstance(s, str) or not s.strip() or len(s) > 360 for s in values):
        raise ValueError("invalid-meme-creative-brief")
    if layout_mode not in data["approved_composition_modes"]:
        raise ValueError("unsupported-approved-visual-layout")
    profile = data["style_contract"]
    mode = data["approved_composition_modes"][layout_mode]
    instructions = [
        f"Draw an ORIGINAL Vietnamese social meme for '{data['brand']}', "
        f"style_id='{ACTIVE_STYLE}'.",
        f"Recurring mascot: {profile['recurring_character']}",
        f"Lines and surfaces: {profile['linework']} {profile['paper']}",
        f"Color usage: {profile['colors']}",
        f"Composition: {profile['composition']}",
        f"OWNER-APPROVED layout mode: {layout_mode}",
        f"Layout instructions: {mode['layout']}",
        f"Border/decor restraint: {mode['decorative_border_limit']}",
        f"Safety and quality: {data['visual_rules']['chat_safety']} {data['visual_rules']['practical_accuracy']}",
        f"Avoid repeated layouts: {data['visual_rules']['no_repeated_frame']}",
        f"Writing and typography: {profile['typography']}",
        f"Comedy mechanism: {profile['humor']}",
        f"New unique scene: {scene.strip()}",
        f"Specific layout/staging (must differ from recent posts): {composition.strip()}",
        f"Character's emotional reaction: {character_emotion.strip()}",
        f"Vietnamese SETUP, spell it correctly and exactly: {setup.strip()}",
        f"Vietnamese PAYOFF, spell it correctly and exactly: {payoff.strip()}",
        "Keep the artwork scene-led, with uneven hand-drawn doodles. "
        "The visuals themselves must carry part of the joke.",
        "Avoid: " + "; ".join(data["negative_prompt"]),
        f"Deliver an original portrait illustration "
        f"{data['delivery']['width']}x{data['delivery']['height']}, "
        "without watermarks or copied existing memes.",
        "Do not schedule or publish. Owner visual review required; "
        "an old stock-photo/card renderer is NOT compliant."
    ]
    return {
        "brand": data["brand"],
        "visual_style_id": ACTIVE_STYLE,
        "style_revision": data["style_revision"],
        "layout_mode": layout_mode,
        "kind": "creative_brief_not_rendered_asset",
        "requires_human_visual_review": True,
        "social_published": False,
        "prompt": "\n".join(instructions),
        "exception": profile["photo_exception"],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scene", required=True)
    parser.add_argument("--setup", required=True)
    parser.add_argument("--payoff", required=True)
    parser.add_argument("--composition", required=True)
    parser.add_argument("--emotion", required=True)
    parser.add_argument("--layout", choices=("scene_doodle", "clean_chat", "practical_ui_tip"), default="scene_doodle")
    args = parser.parse_args()
    brief = build_image_brief(
        args.scene, args.setup, args.payoff,
        composition=args.composition, character_emotion=args.emotion,
        layout_mode=args.layout
    )
    print(json.dumps(brief, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
