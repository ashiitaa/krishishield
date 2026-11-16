from typing import Optional
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from hydrology import calculate_runoff_verdict
from fertilizer_plan import compute_fertilizer_dose, extract_soil_card_nutrients
from alerts import dispatch_keypad_alert

app = FastAPI(title="KrishiShield API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AlertRequest(BaseModel):
    phone_number: str
    farmer_name: Optional[str] = ""
    verdict: Optional[str] = "Pending"
    safe_window: Optional[str] = ""
    dose_text: Optional[str] = ""
    lang: Optional[str] = "en"


@app.get("/")
def serve_frontend():
    return FileResponse("index.html")


@app.get("/api/analyze")
def analyze_farm(
    lat: float = 23.1815,
    lon: float = 79.9864,
    area_ha: float = 1.0,
    crop: str = "wheat",
    soil_n: Optional[float] = None,
    soil_p: Optional[float] = None
):
    dose = compute_fertilizer_dose(crop=crop, area_ha=area_ha, soil_n=soil_n, soil_p=soil_p)
    runoff = calculate_runoff_verdict(lat=lat, lon=lon, area_ha=area_ha, urea_kg=dose["urea_kg"])
    return {
        "runoff": runoff,
        "dose": dose
    }


@app.post("/api/scan-soil-card")
async def scan_soil_card(
    file: UploadFile = File(...),
    crop: str = Form("wheat"),
    area_ha: float = Form(1.0)
):
    raw_bytes = await file.read()
    nutrients = extract_soil_card_nutrients(raw_bytes, file.filename or "")
    dose = compute_fertilizer_dose(
        crop=crop,
        area_ha=area_ha,
        soil_n=nutrients["soil_n"],
        soil_p=nutrients["soil_p"]
    )
    return {
        "filename": file.filename,
        "extracted_nutrients": nutrients,
        "updated_dose": dose
    }


@app.post("/api/send-keypad-alert")
def send_keypad_alert(req: AlertRequest):
    return dispatch_keypad_alert(
        phone_number=req.phone_number,
        farmer_name=req.farmer_name or "",
        verdict=req.verdict or "Pending",
        safe_window=req.safe_window or "",
        dose_text=req.dose_text or "",
        lang=req.lang or "en"
    )
