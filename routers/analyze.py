"""Analyze router: handles /analyze endpoint."""

from fastapi import APIRouter, File, UploadFile, HTTPException, Form
import logging
from io import BytesIO
from PIL import Image

from schemas import AnalyzeResponse, VisualFeatures, SpeciesResult
from services.s3_service import upload_image
from services.vision_service import extract_visual_features
from services.species_service import identify_species

logger = logging.getLogger(__name__)
router = APIRouter()


def _validate_image_bytes(image_bytes: bytes, max_size_mb: int = 10) -> None:
    size_mb = len(image_bytes) / (1024 * 1024)
    if size_mb > max_size_mb:
        raise ValueError(f"Image too large: {size_mb:.1f}MB (max {max_size_mb}MB)")
    try:
        img = Image.open(BytesIO(image_bytes))
        img.verify()  # ✅ just verify, don't convert or modify
    except Exception as e:
        raise ValueError(f"Invalid image: {str(e)}")


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_image(
    file: UploadFile = File(...),
    analysis_type: str = Form("fish")
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    analysis_type = analysis_type.lower().strip()

    # ✅ NOW ACCEPTS fish, coral, marine
    if analysis_type not in ["fish", "coral", "marine"]:
        raise HTTPException(
            status_code=400,
            detail="analysis_type must be 'fish', 'coral', or 'marine'"
        )

    image_bytes = await file.read()

    try:
        _validate_image_bytes(image_bytes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    file_extension = file.filename.split(".")[-1].lower() or "jpg"

    logger.info("Analyzing image: %s (%d bytes) [mode=%s]", file.filename, len(image_bytes), analysis_type)

    try:
        s3_key, presigned = upload_image(image_bytes, file_extension)

        features = extract_visual_features(image_bytes, analysis_type)
        visual = VisualFeatures(**features)

        species_data = identify_species(features, analysis_type, image_bytes)
        species = SpeciesResult(**species_data)

        logger.info("Analysis complete: %s (mode=%s)", species.species_name, analysis_type)

        return AnalyzeResponse(
            image_url=presigned,
            s3_key=s3_key,
            visual_features=visual,
            species=species,
            analysis_type=analysis_type,
        )

    except Exception as e:
        logger.error("Error during analysis: %s", str(e))
        raise HTTPException(status_code=500, detail="Image analysis failed")