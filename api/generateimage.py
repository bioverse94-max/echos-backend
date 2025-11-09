from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import base64
import requests
from pathlib import Path

# ---------------------------
# FastAPI App
# ---------------------------
app = FastAPI(title="Image Generation API")

# ---------------------------
# Request Model
# ---------------------------
class GenerateImageRequest(BaseModel):
    prompt: str
    category: str  # ancient, modern, patterns, icons, backgrounds

# ---------------------------
# Endpoint
# ---------------------------
@app.post("/api/generate-image")
async def generate_image(req: GenerateImageRequest):
    try:
        # ---------------------------
        # Validate category
        # ---------------------------
        allowed_categories = ["ancient", "modern", "patterns", "icons", "backgrounds"]
        if req.category not in allowed_categories:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid category '{req.category}'. Allowed: {allowed_categories}"
            )

        # ---------------------------
        # Banana API call
        # ---------------------------
        banana_api_key = os.environ.get("BANANA_API_KEY")
        banana_model_key = os.environ.get("BANANA_MODEL_KEY")
        if not banana_api_key or not banana_model_key:
            raise HTTPException(
                status_code=500,
                detail="Banana API keys are not configured in environment variables"
            )

        response = requests.post(
            "https://api.banana.dev/start/v4/",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {banana_api_key}"
            },
            json={
                "modelKey": banana_model_key,
                "modelInputs": {"prompt": req.prompt}
            },
            timeout=60  # timeout in seconds
        )
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Banana API error: {response.text}")

        data = response.json()
        base64_img = data.get("modelOutputs", [{}])[0].get("image_base64")
        if not base64_img:
            raise HTTPException(status_code=500, detail="No image returned from Banana API")

        # ---------------------------
        # Save image to public folder
        # ---------------------------
        safe_name = "".join(c if c.isalnum() else "-" for c in req.prompt.lower())
        folder = Path("public") / "images" / req.category
        folder.mkdir(parents=True, exist_ok=True)  # create folder if not exists
        file_path = folder / f"{safe_name}.png"

        # Avoid overwriting existing file
        counter = 1
        original_file_path = file_path
        while file_path.exists():
            file_path = folder / f"{safe_name}-{counter}.png"
            counter += 1

        with open(file_path, "wb") as f:
            f.write(base64.b64decode(base64_img))

        # ---------------------------
        # Return public URL
        # ---------------------------
        public_url = f"/images/{req.category}/{file_path.name}"
        return {"imageUrl": public_url}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))