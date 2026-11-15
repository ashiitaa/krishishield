import requests

def get_soil_texture(lat: float, lon: float) -> dict:
    """Fetches clay/sand % from ISRIC SoilGrids (0-5cm) with safe regional fallback."""
    url = "https://rest.isric.org/soilgrids/v2.0/properties/query"
    params = {
        "lon": lon,
        "lat": lat,
        "property": ["clay", "sand"],
        "depth": "0-5cm",
        "value": "mean"
    }
    try:
        resp = requests.get(url, params=params, timeout=4)
        resp.raise_for_status()
        layers = resp.json()["properties"]["layers"]
        clay = next(l["depths"][0]["values"]["mean"] for l in layers if l["name"] == "clay") / 10.0
        sand = next(l["depths"][0]["values"]["mean"] for l in layers if l["name"] == "sand") / 10.0
        
        if clay >= 35:
            return {"type": "Clay / Black Cotton Soil", "hsg": "D", "cn_base": 84}
        elif sand >= 65:
            return {"type": "Sandy Loam", "hsg": "A", "cn_base": 65}
        else:
            return {"type": "Clay Loam", "hsg": "C", "cn_base": 79}
    except Exception:
        # Fallback for Central India (e.g., Jabalpur / MP) if SoilGrids beta API is slow
        return {"type": "Clay Loam (Regional Default)", "hsg": "C", "cn_base": 79}

def get_weather_and_moisture(lat: float, lon: float) -> dict:
    """Fetches 7-day hourly rain and live top-layer soil moisture from Open-Meteo."""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "precipitation,soil_moisture_0_to_1cm",
        "forecast_days": 7,
        "timezone": "auto"
    }
    resp = requests.get(url, params=params, timeout=8)
    resp.raise_for_status()
    return resp.json()["hourly"]

def calculate_runoff_verdict(lat: float, lon: float, area_ha: float = 1.0, urea_kg: float = 65.0) -> dict:
    soil = get_soil_texture(lat, lon)
    hourly = get_weather_and_moisture(lat, lon)

    times = hourly["time"]
    rain_mm = hourly["precipitation"]
    moisture = hourly["soil_moisture_0_to_1cm"]

    # Current top-layer soil moisture (m3/m3 -> %)
    current_moisture = moisture[0] if moisture[0] is not None else 0.25
    saturation_pct = min(100, round((current_moisture / 0.45) * 100))

    # Adjust SCS Curve Number for Antecedent Moisture Condition (AMC I, II, III)
    cn = soil["cn_base"]
    if current_moisture > 0.32:      # Wet soil (AMC III)
        cn = min(98, round(cn * 1.12))
    elif current_moisture < 0.15:    # Dry soil (AMC I)
        cn = max(40, round(cn * 0.85))

    # SCS Curve Number Hydrology Equations: S = (25400 / CN) - 254, Ia = 0.2 * S
    s_mm = (25400.0 / cn) - 254.0
    ia_mm = 0.2 * s_mm  # Initial abstraction (how much rain soil absorbs before runoff starts)

    # Check next 36 hours for dangerous rain events
    next_36h_rain = sum(r for r in rain_mm[:36] if r is not None)
    runoff_mm = 0.0
    if next_36h_rain > ia_mm:
        runoff_mm = ((next_36h_rain - ia_mm) ** 2) / (next_36h_rain - ia_mm + s_mm)

    # Estimate wash-off loss %
    washoff_pct = min(75, round((runoff_mm / max(1.0, next_36h_rain)) * 100)) if runoff_mm > 0 else 0
    verdict = "HOLD" if (runoff_mm > 2.0 or washoff_pct >= 20) else "SAFE"

    # Build 7-day calendar summary (24h blocks)
    calendar_7d = []
    safe_window = "Today, 7:00 AM"
    found_safe = (verdict == "SAFE")

    for day in range(7):
        start, end = day * 24, (day + 1) * 24
        day_rain = round(sum(r for r in rain_mm[start:end] if r is not None), 1)
        day_date = times[start].split("T")[0]
        if day_rain > ia_mm:
            status = "RED"
        elif day_rain > (ia_mm * 0.5):
            status = "YELLOW"
        else:
            status = "GREEN"
            if not found_safe and day > 0:
                safe_window = f"{day_date} at 7:00 AM"
                found_safe = True
        calendar_7d.append({"date": day_date, "rain_mm": day_rain, "status": status})

    # Measurable environmental & financial savings
    nitrogen_saved_kg = round(urea_kg * 0.46 * (washoff_pct / 100.0), 1) if verdict == "HOLD" else round(urea_kg * 0.46 * 0.15, 1)
    rupees_saved = round((urea_kg * (washoff_pct / 100.0) * 6.0) + 450)  # Subsidized Urea ₹6/kg + avoided re-application labor

    return {
        "verdict": verdict,
        "safe_window": safe_window,
        "soil_type": soil["type"],
        "curve_number": cn,
        "saturation_pct": saturation_pct,
        "next_36h_rain_mm": round(next_36h_rain, 1),
        "predicted_runoff_mm": round(runoff_mm, 1),
        "washoff_risk_pct": washoff_pct,
        "nitrogen_saved_kg": nitrogen_saved_kg,
        "rupees_saved": rupees_saved,
        "calendar_7d": calendar_7d
    }