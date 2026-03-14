"""
Species identification service for marine ecosystem intelligence.
"""

import json
import logging
import re
from typing import Dict, Any, Optional

import boto3

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

MODEL_ID = "arn:aws:bedrock:us-east-1:452031276818:application-inference-profile/8wimphg6jjvj"
CONFIDENCE_THRESHOLD = 0.5

client = boto3.client("bedrock-runtime", region_name="us-east-1")


def _detect_format(image_bytes: bytes) -> str:
    if image_bytes[:8] == b'\x89PNG\r\n\x1a\n':
        return "png"
    if image_bytes[:4] == b'RIFF' and image_bytes[8:12] == b'WEBP':
        return "webp"
    if image_bytes[:3] == b'GIF':
        return "gif"
    return "jpeg"


def _call_nova(prompt: str, image_bytes: Optional[bytes] = None) -> Dict[str, Any]:
    content = []
    if image_bytes:
        fmt = _detect_format(image_bytes)
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

    prompt = f"""You are a world-class marine biologist and fish taxonomist.

Look at this fish image. Identify the EXACT species based on what you actually see.

Visual features already extracted by vision model:
{features_str}

Health observations: {health_obs}

IDENTIFICATION INSTRUCTIONS:
- Look at the image directly — do NOT force a species if it doesn't match
- If the fish has red wounds or injuries, factor those into health assessment
- If the fish looks like a freshwater species (cichlid, tilapia, etc.) say so
- If you cannot identify confidently, give your best guess with lower confidence
- NEVER force "Blue Tang" or any species unless the image actually matches

Common species guide (use ONLY if image matches):
- Vivid blue disc-shaped body + black marking + yellow tail = Blue Tang (Paracanthurus hepatus)
- Orange/white vertical stripes = Clownfish (Amphiprion ocellaris)  
- Fan spines + red/white stripes = Lionfish (Pterois volitans)
- Flat disc + bold black/white stripes + long snout = Butterflyfish
- Deep-bodied with iridescent scales + beak = Parrotfish
- Dark body + bright red/pink wound patches = injured fish, identify from body shape

HEALTH ASSESSMENT:
Based on health_observations and what you see in the image:
- Red patches = likely wound or bacterial infection
- White spots = ich (parasites)
- Torn fins = fin rot or injury
- Bloating = internal infection
- Be specific about what you observe

Return STRICT JSON only (no markdown):
{{
  "species_name": "Genus species",
  "confidence": 0.85,
  "common_names": ["Primary name", "Alternative"],
  "description": "2-3 sentences about THIS species actual appearance and biology",
  "natural_habitat": "specific habitat, depth, geography",
  "ecosystem_role": "specific ecological role",
  "rarity_level": "common/uncommon/rare with context",
  "reef_dependency": "high/medium/low with explanation",
  "health_status": "healthy/stressed/injured/diseased/unknown",
  "observed_conditions": ["each condition separately"],
  "health_notes": "Detailed health description — red patches, wounds, fin damage, parasites, or 'No abnormalities observed'",
  "interesting_facts": [
    "Fact 1 specific to this species",
    "Fact 2 about diet or behavior",
    "Fact 3 about reproduction",
    "Fact 4 about defense or adaptation",
    "Fact 5 about conservation"
  ]
}}"""

    try:
        res = _call_nova(prompt, image_bytes)
    except Exception as e:
        logger.error("[Species] Fish ID failed: %s", str(e))
        return _fish_fallback()

    return _finalize(res, "fish")


# ─────────────────────────────────────────────
# MARINE
# ─────────────────────────────────────────────
def _identify_marine(visual_features: Dict[str, Any], image_bytes: Optional[bytes]) -> Dict[str, Any]:
    features_str   = json.dumps(visual_features, indent=2)
    creature_class = visual_features.get("creature_class", "unknown")
    appendages     = visual_features.get("appendages", "")
    notable        = visual_features.get("notable_features", "")
    health_obs     = visual_features.get("health_observations", [])

    prompt = f"""You are a marine biologist expert in ALL ocean creatures.

Look at this image carefully. Identify the exact species.

Extracted visual features:
{features_str}

Creature class: {creature_class}
Notable features: {notable}  
Appendages: {appendages}
Health observations: {health_obs}

IDENTIFY based on what you actually see:
- Spiny lobster with long whip antennae, no claws = Panulirus species
- Clawed lobster with large crusher claw = Homarus americanus
- Crab with wide shell and claws = Portunus or Callinectes
- 8 arms, soft body, color-changing = Octopus
- Sea turtle with hard shell and flippers = Chelonia or Caretta
- Spiny spherical = Sea urchin
- 5 arms radiating from center = Starfish

HEALTH — describe EVERYTHING you see:
- Barnacles: where exactly, how dense, covering what %
- Missing limbs: which ones
- Shell cracks or damage
- Wounds or unusual coloration
- Whether conditions are normal for this species

Return STRICT JSON only (no markdown):
{{
  "species_name": "Genus species",
  "confidence": 0.85,
  "common_names": ["Primary name", "Alternative"],
  "description": "2-3 vivid sentences about this creature",
  "natural_habitat": "specific depth, geography, substrate",
  "ecosystem_role": "diet, predators, ecosystem function",
  "rarity_level": "common/uncommon/rare with context",
  "reef_dependency": "high/medium/low with explanation",
  "health_status": "healthy/stressed/injured/parasitized/unknown",
  "observed_conditions": ["condition 1", "condition 2"],
  "health_notes": "Detailed health paragraph — barnacles, missing limbs, wounds. Note if normal or concerning.",
  "interesting_facts": [
    "Surprising fact 1",
    "Diet or hunting fact",
    "Reproduction or lifespan fact",
    "Defense or adaptation fact",
    "Conservation or human interaction fact"
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

    # Derive danger level — locked, Nova cannot change
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

    logger.info("[Species] Coral health=%s danger=%s (severity=%s pct=%s)",
                derived_health, derived_danger, bleaching_severity, bleaching_pct)

    prompt = f"""You are a coral taxonomist. Look at this coral image and identify the species.

Visual features:
{features_str}

PRE-ASSESSED health values — use EXACTLY as given, do NOT change:
  coral_health_status = "{derived_health}"
  danger_level = "{derived_danger}"

Identify the coral species from what you see.
Provide reef role, bleaching causes, recovery actions, and facts.

Return STRICT JSON only (no markdown):
{{
  "species_name": "Genus species",
  "confidence": 0.80,
  "common_names": ["name1", "name2"],
  "description": "2-3 vivid sentences about this coral",
  "reef_role": "specific ecological role",
  "coral_health_status": "{derived_health}",
  "danger_level": "{derived_danger}",
  "possible_bleaching_causes": ["cause1", "cause2", "cause3"],
  "recommended_actions": ["action1", "action2", "action3"],
  "health_notes": "Describe bleaching extent, algae, tissue damage, disease signs visible in image.",
  "interesting_facts": ["fact1", "fact2", "fact3", "fact4", "fact5"],
  "natural_habitat": "reef zone, depth, geography",
  "ecosystem_role": "role in marine ecosystem",
  "rarity_level": "common/uncommon/rare"
}}"""

    try:
        res = _call_nova(prompt, image_bytes)
    except Exception as e:
        logger.error("[Species] Coral ID failed: %s", str(e))
        res = {"species_name": "Unknown Coral", "confidence": 0.0,
               "common_names": [], "interesting_facts": []}

    # Force — Nova cannot override these
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
        logger.warning("[Species] Low confidence %.2f for %s",
                       res["confidence"], res.get("species_name"))
    return res


def _fish_fallback() -> Dict[str, Any]:
    return {
        "species_name": "Unknown Fish", "confidence": 0.0, "common_names": [],
        "description": "Unable to identify species.", "natural_habitat": "unknown",
        "ecosystem_role": "unknown", "rarity_level": "unknown", "reef_dependency": "unknown",
        "health_status": "unknown", "observed_conditions": [], "health_notes": "",
        "interesting_facts": [],
    }


def _marine_fallback() -> Dict[str, Any]:
    return {
        "species_name": "Unknown Marine Creature", "confidence": 0.0, "common_names": [],
        "description": "Unable to identify species.", "natural_habitat": "unknown",
        "ecosystem_role": "unknown", "rarity_level": "unknown", "reef_dependency": "unknown",
        "health_status": "unknown", "observed_conditions": [], "health_notes": "",
        "interesting_facts": [], "analysis_type": "marine",
    }