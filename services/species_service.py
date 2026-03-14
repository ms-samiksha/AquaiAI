"""
Species identification service for marine ecosystem intelligence.
Handles fish, coral, and all marine creatures with health/disease assessment.
"""

import base64
import json
import logging
import re
from typing import Dict, Any, Optional

import boto3

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

MODEL_ID = "arn:aws:bedrock:us-east-1:452031276818:application-inference-profile/8wimphg6jjvj"
CONFIDENCE_THRESHOLD = 0.6

client = boto3.client("bedrock-runtime", region_name="us-east-1")


def _detect_image_format(image_bytes: bytes) -> str:
    """Detect image format from magic bytes."""
    if image_bytes[:8] == b'\x89PNG\r\n\x1a\n':
        return "png"
    if image_bytes[:4] == b'RIFF' and image_bytes[8:12] == b'WEBP':
        return "webp"
    if image_bytes[:3] == b'GIF':
        return "gif"
    return "jpeg"


def _call_nova(prompt: str, image_bytes: Optional[bytes] = None) -> Dict[str, Any]:
    """Call Nova with image FIRST then prompt for best identification accuracy."""
    content = []

    # ✅ Always put image first — massively improves identification
    if image_bytes:
        fmt = _detect_image_format(image_bytes)
        content.append({
            "image": {
                "format": fmt,
                "source": {"bytes": image_bytes}
            }
        })

    content.append({"text": prompt})

    response = client.converse(
        modelId=MODEL_ID,
        messages=[{"role": "user", "content": content}],
        inferenceConfig={"maxTokens": 1200, "temperature": 0.1},
    )

    output_text = response["output"]["message"]["content"][0]["text"]
    logger.info("[Species] Raw response: %s", output_text[:600])

    cleaned = output_text.strip().replace("```json", "").replace("```", "").strip()
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if not match:
        raise ValueError("No JSON found in response")
    return json.loads(match.group(0))


def identify_species(
    visual_features: Dict[str, Any],
    analysis_type: str = "fish",
    image_bytes: Optional[bytes] = None,
) -> Dict[str, Any]:

    logger.info("[Species] Identifying species (mode=%s)", analysis_type)

    if analysis_type == "coral":
        return _identify_coral(visual_features, image_bytes)
    elif analysis_type == "marine":
        return _identify_marine(visual_features, image_bytes)
    else:
        return _identify_fish(visual_features, image_bytes)


# ─────────────────────────────────────────────
# FISH
# ─────────────────────────────────────────────
def _identify_fish(visual_features: Dict[str, Any], image_bytes: Optional[bytes]) -> Dict[str, Any]:
    health_obs   = visual_features.get("health_observations", [])
    features_str = json.dumps(visual_features, indent=2)

    prompt = f"""You are a world-class marine ichthyologist. Look at this fish image and identify the exact species.

Use the image as your PRIMARY source. These visual features were also extracted:
{features_str}

CRITICAL identification rules — use the image directly:
- Vivid BLUE oval body + YELLOW tail fin = Paracanthurus hepatus (Blue Tang / Palette Surgeonfish)
- Orange body + bright WHITE vertical stripes = Amphiprion ocellaris (Clownfish)
- Fan-like venomous spines + red/white stripes = Pterois volitans (Lionfish)
- Flat disc body + long snout + bold stripes = Butterflyfish (Chaetodontidae)
- Beak-like fused teeth + bright green/blue/pink = Parrotfish (Scaridae)
- Bright yellow body + long dorsal filament = Moorish Idol (Zanclus cornutus)
- Elongated body + eel-like = Moray Eel
- Blue body + BLACK oval spot on side = Paracanthurus hepatus (Blue Tang)

DO NOT guess based on text features alone — look at the actual image colors and shape.

Health observations from image: {health_obs}

Return STRICT JSON only (no markdown, no preamble):
{{
  "species_name": "Genus species",
  "confidence": 0.90,
  "common_names": ["Primary common name", "Alternative name"],
  "description": "2-3 vivid sentences about this specific species appearance and biology",
  "natural_habitat": "specific reef zone, depth range, geographic distribution",
  "ecosystem_role": "specific role — herbivore/carnivore/cleaner, reef impact",
  "rarity_level": "common/uncommon/rare — with one sentence of context",
  "reef_dependency": "high/medium/low — explain relationship with coral reefs",
  "health_status": "healthy/stressed/injured/diseased/unknown",
  "observed_conditions": [],
  "health_notes": "Describe fin condition, any parasites, lesions, discoloration, wounds visible. Say 'No abnormalities observed' if healthy.",
  "interesting_facts": [
    "Specific surprising fact about this species",
    "Fact about its diet or feeding behavior",
    "Fact about reproduction or lifespan",
    "Fact about defense or unique adaptation",
    "Fact about conservation status or threats"
  ]
}}"""

    try:
        res = _call_nova(prompt, image_bytes)
    except Exception as e:
        logger.error("[Species] Fish ID failed: %s", str(e))
        return _fish_fallback()

    return _finalize(res, "fish")


# ─────────────────────────────────────────────
# MARINE (lobsters, crabs, turtles, octopus…)
# ─────────────────────────────────────────────
def _identify_marine(visual_features: Dict[str, Any], image_bytes: Optional[bytes]) -> Dict[str, Any]:
    features_str   = json.dumps(visual_features, indent=2)
    creature_class = visual_features.get("creature_class", "unknown")
    appendages     = visual_features.get("appendages", "")
    notable        = visual_features.get("notable_features", "")
    health_obs     = visual_features.get("health_observations", [])

    prompt = f"""You are a marine biologist with deep expertise in ALL ocean creatures.

Look at this image carefully and identify the exact species.

Visual analysis already extracted:
{features_str}

Creature class: {creature_class}
Notable features: {notable}
Appendages: {appendages}
Health observations: {health_obs}

IDENTIFICATION GUIDE:
- Large spiny lobster with long antennae = Panulirus argus (Caribbean Spiny Lobster) or Panulirus ornatus
- Smaller clawed lobster = Homarus americanus (American Lobster)
- Crab with wide flat shell = likely Portunus or Callinectes
- Octopus with 8 arms = Octopus vulgaris or similar
- Sea turtle with flippers = Chelonia mydas (Green) or Caretta caretta (Loggerhead)
- Starfish = Asterias or Pisaster species
- Sea urchin with spines = Diadema or Strongylocentrotus

HEALTH ASSESSMENT — look at the image carefully:
- Barnacles on shell/carapace — describe coverage and density
- Missing claws or limbs — note which ones
- Shell damage or cracks
- Wounds or lesions on body
- Parasites or unusual growths
- Whether conditions are normal or concerning

Return STRICT JSON only (no markdown, no preamble):
{{
  "species_name": "Genus species",
  "confidence": 0.85,
  "common_names": ["Primary name", "Alternative name"],
  "description": "2-3 vivid sentences about appearance, behavior and biology of this specific creature",
  "natural_habitat": "specific depth, geography, substrate — where exactly this creature lives",
  "ecosystem_role": "specific role — what it eats, what eats it, ecosystem function",
  "rarity_level": "common/uncommon/rare — with context sentence",
  "reef_dependency": "high/medium/low — explain ocean habitat relationship",
  "health_status": "healthy/stressed/injured/parasitized/unknown",
  "observed_conditions": [
    "Each condition as separate string e.g. 'Heavy barnacle coverage on carapace and legs'"
  ],
  "health_notes": "Detailed health paragraph. Describe barnacle coverage location and density, missing limbs, wounds, parasites. State if normal or concerning for this species.",
  "interesting_facts": [
    "Surprising specific fact about this species",
    "Fact about diet or hunting strategy",
    "Fact about reproduction or lifespan",
    "Fact about unique defense or adaptation",
    "Fact about commercial importance or conservation"
  ]
}}"""

    try:
        res = _call_nova(prompt, image_bytes)
        res["analysis_type"] = "marine"
    except Exception as e:
        logger.error("[Species] Marine ID failed: %s", str(e))
        return _marine_fallback()

    return _finalize(res, "marine")


# ─────────────────────────────────────────────
# CORAL
# ─────────────────────────────────────────────
def _identify_coral(visual_features: Dict[str, Any], image_bytes: Optional[bytes]) -> Dict[str, Any]:
    bleaching_severity = visual_features.get("bleaching_severity", "none")
    bleaching_pct      = visual_features.get("bleaching_percentage", 0)
    stress_signs       = visual_features.get("visual_stress_signs", [])
    possible_bleaching = visual_features.get("possible_bleaching", False)
    features_str       = json.dumps(visual_features, indent=2)

    # Derive danger level — Nova cannot override
    if bleaching_severity == "severe" or bleaching_pct > 40:
        derived_danger = "critical"
        derived_health = "severe bleaching"
    elif bleaching_severity == "moderate" or bleaching_pct > 15:
        derived_danger = "high"
        derived_health = "bleaching"
    elif bleaching_severity == "mild" or bleaching_pct > 0 or possible_bleaching:
        derived_danger = "moderate"
        derived_health = "partial bleaching"
    elif len(stress_signs) > 0:
        derived_danger = "low"
        derived_health = "stressed"
    else:
        derived_danger = "healthy"
        derived_health = "healthy"

    logger.info("[Species] Coral health=%s danger=%s", derived_health, derived_danger)

    prompt = f"""You are a coral taxonomist and reef ecologist. Look at this coral image.

Visual features extracted:
{features_str}

IMPORTANT — use these EXACT pre-assessed values, do NOT change them:
  coral_health_status = "{derived_health}"
  danger_level        = "{derived_danger}"

STEP 1: Identify coral species from the image (genus and species).
STEP 2: Describe appearance and reef ecological role.
STEP 3: List most likely bleaching/stress causes.
STEP 4: Suggest specific conservation and recovery actions.
STEP 5: Add interesting ecological facts.

Return STRICT JSON only (no markdown):
{{
  "species_name": "Genus species",
  "confidence": 0.80,
  "common_names": ["name1", "name2"],
  "description": "2-3 vivid sentences about coral appearance and biology",
  "reef_role": "specific ecological role on the reef",
  "coral_health_status": "{derived_health}",
  "danger_level": "{derived_danger}",
  "possible_bleaching_causes": ["cause1", "cause2", "cause3"],
  "recommended_actions": ["action1", "action2", "action3"],
  "health_notes": "Describe observed health: bleaching extent, algae overgrowth, tissue damage, disease signs.",
  "interesting_facts": [
    "Specific fact 1", "Specific fact 2", "Specific fact 3",
    "Specific fact 4", "Specific fact 5"
  ],
  "natural_habitat": "specific reef zone, depth, geography",
  "ecosystem_role": "role in broader marine ecosystem",
  "rarity_level": "common/uncommon/rare"
}}"""

    try:
        res = _call_nova(prompt, image_bytes)
    except Exception as e:
        logger.error("[Species] Coral ID failed: %s", str(e))
        res = {"species_name": "Unknown Coral", "confidence": 0.0, "common_names": [], "interesting_facts": []}

    # Force derived values
    res["coral_health_status"] = derived_health
    res["danger_level"]        = derived_danger

    return _finalize(res, "coral")


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def _finalize(res: Dict[str, Any], analysis_type: str) -> Dict[str, Any]:
    try:
        res["confidence"] = float(res.get("confidence", 0.0))
    except Exception:
        res["confidence"] = 0.0

    list_fields = [
        "common_names", "possible_bleaching_causes", "recommended_actions",
        "interesting_facts", "observed_conditions", "health_observations",
        "visual_stress_signs", "possible_stress_signs", "distinctive_traits",
    ]
    for f in list_fields:
        if not isinstance(res.get(f), list):
            res[f] = []

    string_defaults = {
        "species_name": "Unknown",
        "description": "",
        "health_status": "unknown",
        "health_notes": "",
    }
    for f, default in string_defaults.items():
        if not res.get(f):
            res[f] = default

    if res["confidence"] < CONFIDENCE_THRESHOLD:
        logger.warning("[Species] Low confidence %.2f for %s", res["confidence"], res.get("species_name"))

    return res


def _fish_fallback() -> Dict[str, Any]:
    return {
        "species_name": "Unknown Fish",
        "confidence": 0.0,
        "common_names": [],
        "description": "Unable to identify species.",
        "natural_habitat": "unknown",
        "ecosystem_role": "unknown",
        "rarity_level": "unknown",
        "reef_dependency": "unknown",
        "health_status": "unknown",
        "observed_conditions": [],
        "health_notes": "",
        "interesting_facts": [],
    }


def _marine_fallback() -> Dict[str, Any]:
    return {
        "species_name": "Unknown Marine Creature",
        "confidence": 0.0,
        "common_names": [],
        "description": "Unable to identify species.",
        "natural_habitat": "unknown",
        "ecosystem_role": "unknown",
        "rarity_level": "unknown",
        "reef_dependency": "unknown",
        "health_status": "unknown",
        "observed_conditions": [],
        "health_notes": "",
        "interesting_facts": [],
        "analysis_type": "marine",
    }