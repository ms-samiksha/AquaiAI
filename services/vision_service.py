"""
Vision service using Amazon Nova via Bedrock Converse API.
"""

import boto3
import json
import logging
import re
from typing import Dict, Any

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

MODEL_ID = "arn:aws:bedrock:us-east-1:452031276818:application-inference-profile/8wimphg6jjvj"
client = boto3.client("bedrock-runtime", region_name="us-east-1")


def _extract_json(text: str) -> Dict[str, Any]:
    cleaned = text.strip().replace("```json", "").replace("```", "").strip()
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found")
    return json.loads(match.group(0))


def _detect_format(image_bytes: bytes) -> str:
    if image_bytes[:8] == b'\x89PNG\r\n\x1a\n':
        return "png"
    if image_bytes[:4] == b'RIFF' and image_bytes[8:12] == b'WEBP':
        return "webp"
    if image_bytes[:3] == b'GIF':
        return "gif"
    return "jpeg"


def extract_visual_features(image_bytes: bytes, analysis_type: str = "fish") -> Dict[str, Any]:
    logger.info("[Vision] Extracting visual features (type=%s)", analysis_type)
    fmt = _detect_format(image_bytes)

    if analysis_type == "coral":
        prompt = """You are a coral reef scientist. Analyze this coral image with extreme care.

STEP 1 — Look at the actual colors:
- Vibrant brown, green, purple, orange = HEALTHY
- Pale white or cream patches = BLEACHING
- Fully white skeleton exposed = SEVERE bleaching
- Green algae covering coral = STRESSED (algae overgrowth)

STEP 2 — Estimate what % of the coral surface is bleached/white:
- 0% = none
- 1-15% = mild  
- 16-40% = moderate
- >40% = severe

STEP 3 — List ALL visible stress signs you can see.

BE HONEST. Do NOT say "none" if you see ANY white patches.
Do NOT say "healthy" if there is algae overgrowth or discoloration.

Return STRICT JSON only:
{
  "organism_type": "coral",
  "coral_structure": "branching/massive/plate/encrusting/fan/other",
  "dominant_color": "exact color you see",
  "branching_pattern": "describe structure",
  "possible_bleaching": true or false,
  "bleaching_severity": "none/mild/moderate/severe",
  "bleaching_percentage": 0,
  "visual_stress_signs": ["each sign as separate string"],
  "health_observations": ["each observation as separate string"]
}"""

    elif analysis_type == "marine":
        prompt = """You are a marine biologist. Identify what creature is in this image.

Look at every detail:
1. Overall body type — shell, fins, legs, tentacles, flippers?
2. How many limbs/appendages?
3. Does it have a hard shell/carapace or soft body?
4. Exact colors and patterns
5. Any distinctive features — claws, antennae, beak, spines?
6. Size relative to surroundings

HEALTH — look carefully:
- Any barnacles attached to body/shell?
- Missing limbs or claws?
- Wounds, discoloration, unusual growths?
- Shell damage?
- Say exactly what you observe, don't just say healthy

Return STRICT JSON only:
{
  "organism_type": "marine",
  "creature_class": "crustacean/fish/cephalopod/echinoderm/mollusk/mammal/reptile/other",
  "body_shape": "detailed description",
  "dominant_color": "exact color",
  "pattern": "spots/stripes/solid/mottled/other",
  "distinctive_traits": ["trait1", "trait2"],
  "appendages": "detailed description of all limbs, claws, antennae, fins",
  "size_estimate": "small/medium/large",
  "notable_features": "describe everything notable",
  "possible_stress_signs": [],
  "health_observations": ["each observation separately"]
}"""

    else:  # fish
        prompt = """You are a marine biologist. Look at this fish image and describe EXACTLY what you see.

DO NOT assume the species — describe the actual visual features:
1. Body shape — is it disc-shaped, elongated, torpedo, flat?
2. Exact colors — what colors do you actually see?
3. Are there any wounds, red patches, injuries?
4. Pattern — stripes, spots, solid, bands?
5. Fin condition — are fins intact or damaged?
6. Any parasites, lesions, abnormal growths?
7. Tail color and shape
8. Any distinctive markings

Be completely honest about what you see in THIS image.
If there are red patches or wounds, report them in health_observations.

Return STRICT JSON only:
{
  "organism_type": "fish",
  "body_shape": "exact shape",
  "dominant_color": "exact primary color",
  "secondary_colors": ["color1", "color2"],
  "pattern": "exact pattern",
  "tail_color": "exact tail color",
  "distinctive_markings": ["each marking separately"],
  "fin_shape": "fin description",
  "possible_stress_signs": ["any stress signs"],
  "health_observations": ["EACH health observation as separate string — red patches, wounds, fin damage, parasites, or 'Appears healthy'"]
}"""

    try:
        response = client.converse(
            modelId=MODEL_ID,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "image": {
                            "format": fmt,
                            "source": {"bytes": image_bytes}
                        }
                    },
                    {"text": prompt},
                ],
            }],
            inferenceConfig={"maxTokens": 800, "temperature": 0.05},
        )
        output_text = response["output"]["message"]["content"][0]["text"]
        logger.info("[Vision] Raw output: %s", output_text)
        return _extract_json(output_text)

    except Exception as e:
        logger.error("[Vision] Failed: %s", str(e))
        if analysis_type == "coral":
            return {"organism_type": "coral", "coral_structure": "unknown", "dominant_color": "unknown",
                    "branching_pattern": "unknown", "possible_bleaching": False, "bleaching_severity": "none",
                    "bleaching_percentage": 0, "visual_stress_signs": [], "health_observations": []}
        elif analysis_type == "marine":
            return {"organism_type": "marine", "creature_class": "unknown", "body_shape": "unknown",
                    "dominant_color": "unknown", "pattern": "unknown", "distinctive_traits": [],
                    "appendages": "unknown", "size_estimate": "unknown", "notable_features": "unknown",
                    "possible_stress_signs": [], "health_observations": []}
        else:
            return {"organism_type": "fish", "body_shape": "unknown", "dominant_color": "unknown",
                    "pattern": "unknown", "distinctive_traits": [], "possible_stress_signs": [],
                    "health_observations": []}