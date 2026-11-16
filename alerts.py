def dispatch_keypad_alert(phone_number: str, farmer_name: str, verdict: str, safe_window: str, dose_text: str, lang: str = "en") -> dict:
    name = farmer_name.strip() if farmer_name else "Farmer"
    if lang == "hi":
        script = (
            f"नमस्ते {name}, KrishiShield सलाह: स्थिति {verdict}। "
            f"सुरक्षित समय: {safe_window}। मात्रा: {dose_text}।"
        )
    else:
        script = (
            f"Namaste {name}, KrishiShield Alert: Status is {verdict}. "
            f"Safe window: {safe_window}. Recommended dose: {dose_text}."
        )

    return {
        "status": f"SMS & IVR keypad alert queued for {phone_number}",
        "script": script
    }
