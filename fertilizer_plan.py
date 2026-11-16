import re

CROP_NPK_TARGETS = {
    "wheat": {"n": 120.0, "p": 60.0, "habit_urea": 260.0},
    "rice": {"n": 100.0, "p": 50.0, "habit_urea": 220.0},
    "soybean": {"n": 30.0, "p": 60.0, "habit_urea": 65.0},
    "maize": {"n": 120.0, "p": 60.0, "habit_urea": 250.0},
}


def compute_fertilizer_dose(crop: str, area_ha: float, soil_n: float = None, soil_p: float = None) -> dict:
    crop_key = (crop or "wheat").strip().lower()
    target = CROP_NPK_TARGETS.get(crop_key, CROP_NPK_TARGETS["wheat"])

    # Soil Health Card adjustment (kg/ha available N and P)
    n_credit = 25.0 if (soil_n is not None and soil_n > 280) else (10.0 if soil_n is not None else 15.0)
    p_credit = 15.0 if (soil_p is not None and soil_p > 22) else (5.0 if soil_p is not None else 8.0)

    req_n_ha = max(15.0, target["n"] - n_credit)
    req_p_ha = max(10.0, target["p"] - p_credit)

    # DAP provides 46% P2O5 and 18% N; Urea provides 46% N
    dap_kg_ha = req_p_ha / 0.46
    n_from_dap = dap_kg_ha * 0.18
    remaining_n_ha = max(0.0, req_n_ha - n_from_dap)
    urea_kg_ha = remaining_n_ha / 0.46

    urea_kg = round(urea_kg_ha * area_ha, 1)
    dap_kg = round(dap_kg_ha * area_ha, 1)
    habit_urea_total = target["habit_urea"] * area_ha
    urea_reduced = max(0.0, round(habit_urea_total - urea_kg, 1))

    return {
        "crop": crop_key,
        "area_ha": area_ha,
        "urea_kg": urea_kg,
        "dap_kg": dap_kg,
        "urea_reduced_vs_habit_kg": urea_reduced
    }


def extract_soil_card_nutrients(raw_bytes: bytes, filename: str = "") -> dict:
    """Extracts Nitrogen (N) and Phosphorus (P) from uploaded Soil Health Card text/image."""
    text = raw_bytes.decode("utf-8", errors="ignore")
    n_match = re.search(r"(?:Nitrogen|Available\s*N|\bN\b)[^\d]{0,15}(\d{2,3}(?:\.\d+)?)", text, re.IGNORECASE)
    p_match = re.search(r"(?:Phosphorus|Available\s*P|\bP\b)[^\d]{0,15}(\d{1,3}(?:\.\d+)?)", text, re.IGNORECASE)

    soil_n = float(n_match.group(1)) if n_match else 245.0
    soil_p = float(p_match.group(1)) if p_match else 18.5
    return {"soil_n": soil_n, "soil_p": soil_p}
