"""
Vision service using Amazon Nova via Bedrock Converse API.
Extracts visual features from uploaded images for fish, coral, and marine creatures.
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
    cleaned = text.strip()
    cleaned = cleaned.replace("```json", "").replace("```", "").strip()
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found")
    return json.loads(match.group(0))


def _detect_image_format(image_bytes: bytes) -> str:
    """Detect image format from magic bytes — fixes PNG/WEBP failures."""
    if image_bytes[:8] == b'\x89PNG\r\n\x1a\n':
        return "png"
    if image_bytes[:4] == b'RIFF' and image_bytes[8:12] == b'WEBP':
        return "webp"
    if image_bytes[:3] == b'GIF':
        return "gif"
    return "jpeg"  # default


def extract_visual_features(image_bytes: bytes, analysis_type: str = "fish") -> Dict[str, Any]:
    logger.info("[Vision] Extracting visual features (type=%s)", analysis_type)

    fmt = _detect_image_format(image_bytes)
    logger.info("[Vision] Detected image format: %s", fmt)

    if analysis_type == "coral":
        prompt = """You are a coral reef visual analyst and marine biologist.

Analyze this coral image VERY carefully. Do not guess.

Follow this strict reasoning process:
1) Identify coral morphology (branching, plate, boulder, encrusting, foliose, massive).
2) Note dominant color — brown/green = healthy, pale/white = bleached.
3) Detect bleaching signs: white skeleton exposure, loss of pigment, tissue loss.
4) Estimate bleaching severity based on % of coral affected:
   - "none"     → 0% bleaching, fully pigmented and healthy
   - "mild"     → 1-15% white patches, mostly healthy
   - "moderate" → 15-40% bleaching, significant stress visible
   - "severe"   → >40% white/dead tissue, skeleton exposed widely
5) List any visible stress signs (algae overgrowth, tissue loss, lesions, sediment).
6) Note any disease, physical damage, or unusual observations.

BE STRICT. If the coral looks mostly brown/healthy, say "none".
If it is mostly white and skeleton is exposed, say "severe".
DO NOT default to moderate. Look at the actual image.

Return STRICT JSON only (no markdown, no explanation):
{
  "organism_type": "coral",
  "coral_structure": "",
  "dominant_color": "",
  "branching_pattern": "",
  "possible_bleaching": false,
  "bleaching_severity": "none|mild|moderate|severe",
  "bleaching_percentage": 0,
  "visual_stress_signs": [],
  "health_observations": []
}"""

    elif analysis_type == "marine":
        prompt = """You are a marine biologist specializing in ALL ocean creatures — crustaceans, mollusks, echinoderms, cephalopods, marine reptiles, fish, and more.

Analyze every visible detail of this image carefully.

Pay special attention to:
1) What type of creature is this? (crustacean, fish, cephalopod, echinoderm, mollusk, reptile, mammal, other)
2) Body structure — shell, carapace, exoskeleton, scales, skin
3) Appendages — claws, legs, antennae, fins, tentacles, spines
4) Color and pattern
5) Size estimate
6) HEALTH OBSERVATIONS — look carefully for:
   - Barnacle coverage on shell or body
   - Parasites attached to body
   - Missing or damaged claws/limbs/fins
   - Wounds, lesions, or unusual growths
   - Shell damage or deformities
   - Discoloration suggesting disease
   - Any other abnormalities
   - Write "Appears healthy, no abnormalities observed" if nothing found

Return STRICT JSON only (no markdown, no explanation):
{
  "organism_type": "marine",
  "creature_class": "crustacean/fish/cephalopod/echinoderm/mollusk/mammal/reptile/other",
  "body_shape": "",
  "dominant_color": "",
  "pattern": "spots/stripes/solid/mottled/other",
  "distinctive_traits": [],
  "appendages": "describe claws, legs, antennae, fins, shell in detail",
  "size_estimate": "small/medium/large",
  "notable_features": "barnacles, spines, antennae, markings, shell texture, any striking features",
  "possible_stress_signs": [],
  "health_observations": [
    "Each specific health observation as a separate string."
  ]
}"""

    else:  # fish
        prompt = """You are a marine ichthyologist and expert in reef fish identification.

Look at this fish image carefully and identify the exact species.

Key identification rules:
- Blue oval body + yellow tail = Blue Tang (Paracanthurus hepatus)
- Orange/white stripes = Clownfish (Amphiprion ocellaris)
- Venomous fan-like spines + striped = Lionfish (Pterois volitans)
- Flat disc body + long snout = Butterflyfish
- Bright parrot-like beak + colorful = Parrotfish
- Yellow body, black eye stripe = Bannerfish or Moorish Idol

Extract visual traits AND identify species directly from the image.

Also check for health issues:
- Fin damage or rot
- Lesions or wounds  
- Parasites (white spots = ich)
- Unusual discoloration
- Bloating or deformities

Return STRICT JSON only (no markdown, no explanation):
{
  "organism_type": "fish",
  "body_shape": "oval/elongated/disc-shaped/torpedo-shaped/other",
  "dominant_color": "",
  "secondary_colors": [],
  "pattern": "stripes/bands/spots/gradient/solid/other",
  "tail_color": "",
  "distinctive_markings": [],
  "fin_shape": "",
  "possible_stress_signs": [],
  "health_observations": [
    "Each health observation as a separate string, or 'Appears healthy, no abnormalities observed'"
  ]
}"""

    try:
        response = client.converse(
            modelId=MODEL_ID,
            messages=[
                {
                    "role": "user",
                    "content": [
                        # ✅ IMAGE FIRST — Nova identifies better this way
                        {
                            "image": {
                                "format": fmt,
                                "source": {"bytes": image_bytes}
                            }
                        },
                        {"text": prompt},
                    ],
                }
            ],
            inferenceConfig={
                "maxTokens": 700,
                "temperature": 0.1,
            },
        )

        output_text = response["output"]["message"]["content"][0]["text"]
        logger.info("[Vision] Raw output: %s", output_text)
        return _extract_json(output_text)

    except Exception as e:
        logger.error("[Vision] Failed: %s", str(e))

        if analysis_type == "coral":
            return {
                "organism_type": "coral",
                "coral_structure": "unknown",
                "dominant_color": "unknown",
                "branching_pattern": "unknown",
                "possible_bleaching": False,
                "bleaching_severity": "none",
                "bleaching_percentage": 0,
                "visual_stress_signs": [],
                "health_observations": [],
            }
        elif analysis_type == "marine":
            return {
                "organism_type": "marine",
                "creature_class": "unknown",
                "body_shape": "unknown",
                "dominant_color": "unknown",
                "pattern": "unknown",
                "distinctive_traits": [],
                "appendages": "unknown",
                "size_estimate": "unknown",
                "notable_features": "unknown",
                "possible_stress_signs": [],
                "health_observations": [],
            }
        else:
            return {
                "organism_type": "fish",
                "body_shape": "unknown",
                "dominant_color": "unknown",
                "pattern": "unknown",
                "distinctive_traits": [],
                "possible_stress_signs": [],
                "health_observations": [],
            }