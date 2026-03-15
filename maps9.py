# maps9.py
def generate_maps():
    full_world = []
    themes = [
        {"bg": "#0B1D28", "floor": "#1A3644", "name": "Forest Path"},
        {"bg": "#311C0C", "floor": "#6B431D", "name": "Desert Pass"},
        {"bg": "#082138", "floor": "#40769D", "name": "Ice Cavern"},
        {"bg": "#2F0909", "floor": "#4F1414", "name": "Volcanic Core"}
    ]
    
    # נייצר את המפה לכל 20 השלבים כמקטעים
    for s in range(1, 21):
        x_offset = (s - 1) * 3500
        theme = themes[(s - 1) // 5]
        
        # בניית פלטפורמות ספציפיות לאזור
        platforms = []
        if s % 2 == 0:
            platforms.append({"x": x_offset + 500, "y_offset": 150, "w": 400})
            platforms.append({"x": x_offset + 1200, "y_offset": 250, "w": 300})
        else:
            platforms.append({"x": x_offset + 800, "y_offset": 200, "w": 500})
            platforms.append({"x": x_offset + 2000, "y_offset": 120, "w": 400})

        # הגדרת סוגי אויבים באזור
        enemies_in_stage = ["melee"]
        if s >= 3: enemies_in_stage.append("jumper")
        if s >= 6: enemies_in_stage.append("shooter")
        if s >= 10: enemies_in_stage.append("tank")
        if s >= 14: enemies_in_stage.append("ninja")

        full_world.append({
            "stage": s,
            "name": theme["name"],
            "bg": theme["bg"],
            "floor": theme["floor"],
            "x_start": x_offset,
            "x_end": x_offset + 3500,
            "platforms": platforms,
            "enemies": enemies_in_stage,
            "is_boss": (s % 5 == 0)
        })
        
    return full_world
