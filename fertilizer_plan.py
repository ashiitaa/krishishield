import re

CROP_STANDARDS = {
    "wheat": {"n": 120, "p": 60, "k": 40},
    "rice": {"n": 100, "p": 50, "k": 50},
    "soybean": {"n": 30, "p": 60, "k": 40},
    "maize": {"n": 120, "p": 60, "k": 40}
}

def calculate_fertilizer_dose(crop: str, area_ha: float, soil_n: float = None, soil_p: float = None) -> dict:
    """Calculates exact Urea & DAP bags/kg using Soil Health Card N & P values."""
    req = CROP_STANDARDS.get(crop.lower(), CROP_STANDARDS["wheat"])
    
    # Reduce recommended dose if Soil Health Card shows medium/high existing nutrients
    n_needed = req["n"] * 0.80 if (soil_n and soil_n > 280) else req["n"]
    p_needed = req["p"] * 0.80 if (soil_p and soil_p > 22) else req["p"]

    # DAP supplies 46% P2O5 and 18% N; Urea supplies 46% N
    dap_kg = round((p_needed / 0.46) * area_ha, 1)
    n_from_dap = dap_kg * 0.18
    remaining_n = max(0.0, (n_needed * area_ha) - n_from_dap)
    urea_kg = round(remaining_n / 0.46, 1)

    habit_urea = round((req["n"] / 0.46) * area_ha * 1.15, 1)  # Farmers typically over-apply by ~15%
    urea_reduced = max(0.0, round(habit_urea - urea_kg, 1))

    return {
        "crop": crop.capitalize(),
        "area_ha": area_ha,
        "urea_kg": urea_kg,
        "dap_kg": dap_kg,
        "urea_reduced_vs_habit_kg": urea_reduced,
        "summary_text": f"Apply {urea_kg} kg Urea + {dap_kg} kg DAP ({urea_reduced} kg less Urea than standard habit)"
    }

def parse_soil_card_text(raw_text: str) -> dict:
    """Extracts Nitrogen (N) and Phosphorus (P) numbers from OCR text."""
    n_match = re.search(r"(?:Nitrogen|N)\D{0,15}(\d{2,3}(?:\.\d+)?)", raw_text, re.IGNORECASE)
    p_match = re.search(r"(?:Phosphorus|P)\D{0,15}(\d{1,3}(?:\.\d+)?)", raw_text, re.IGNORECASE)
    return {
        "soil_n": float(n_match.group(1)) if n_match else 310.0,  # Demo fallback if image is blurry
        "soil_p": float(p_match.group(1)) if p_match else 24.5
    }