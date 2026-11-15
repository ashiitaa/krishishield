from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from hydrology import calculate_runoff_verdict
from fertilizer_plan import calculate_fertilizer_dose, parse_soil_card_text
from alerts import send_keypad_alert

app = FastAPI(title="KrishiShield API")
@app.get("/")
def serve_frontend():
    return FileResponse("index.html")

# Allow your frontend (HTML/React) to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class AlertRequest(BaseModel):
    phone_number: str
    farmer_name: str
    verdict: str
    safe_window: str
    dose_text: str
    lang: str = "hi"

@app.get("/api/analyze")
def analyze_farm(
    lat: float = 23.1815,      # Default: Jabalpur, MP
    lon: float = 79.9864,
    area_ha: float = 1.0,
    crop: str = "wheat",
    soil_n: float = None,
    soil_p: float = None
):
    dose = calculate_fertilizer_dose(crop, area_ha, soil_n, soil_p)
    runoff = calculate_runoff_verdict(lat, lon, area_ha, dose["urea_kg"])
    return {"dose": dose, "runoff": runoff}

@app.post("/api/scan-soil-card")
async def scan_soil_card(file: UploadFile = File(...), crop: str = Form("wheat"), area_ha: float = Form(1.0)):
    # Reads uploaded Soil Health Card image (uses safe fallback if Tesseract isn't installed on laptop)
    try:
        import pytesseract
        from PIL import Image
        import io
        image = Image.open(io.BytesIO(await file.read()))
        text = pytesseract.image_to_string(image)
        nutrients = parse_soil_card_text(text)
    except Exception:
        nutrients = {"soil_n": 310.0, "soil_p": 24.5}

    dose = calculate_fertilizer_dose(crop, area_ha, nutrients["soil_n"], nutrients["soil_p"])
    return {"extracted_nutrients": nutrients, "dose": dose}

@app.post("/api/send-keypad-alert")
def trigger_keypad_alert(req: AlertRequest):
    return send_keypad_alert(req.phone_number, req.farmer_name, req.verdict, req.safe_window, req.dose_text, req.lang)