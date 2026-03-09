def generate_maps():
    maps = {}
    
    themes =[
        {"bg": "#0B1D28", "floor": "#1A3644", "name": "Dark Forest", "decor": "forest"}, # שלבים 1-5
        {"bg": "#311C0C", "floor": "#6B431D", "name": "Dusty Canyon", "decor": "desert"},  # שלבים 6-10
        {"bg": "#082138", "floor": "#40769D", "name": "Glacier Peaks", "decor": "ice"},     # שלבים 11-15
        {"bg": "#2F0909", "floor": "#4F1414", "name": "Inferno Volcano", "decor": "magma"}   # שלבים 16-20
    ]
    
    for i in range(1, 21):
        theme_index = (i - 1) // 5 # כל 5 שלבים נושא חדש
        is_boss = (i % 5 == 0)
        
        # בניית פלטפורמות רנדומליות-מוגדרות מראש לפי השלב
        platforms = []
        if not is_boss and i > 2:
            platforms =[
                {"x": 300, "y_offset": 120, "w": 200, "h": 20},
                {"x": 600, "y_offset": 200, "w": 150, "h": 20},
                {"x": 950, "y_offset": 100, "w": 300, "h": 20}
            ]
        
        # איזה סוגי אויבים להכניס למפה:
        allowed_enemies = ["melee"]
        if i >= 3: allowed_enemies.append("jumper")
        if i >= 6: allowed_enemies.append("shooter")

        maps[i] = {
            "name": "BOSS CHAMBER" if is_boss else f"{themes[theme_index]['name']} - Sector {i}",
            "bg": themes[theme_index]["bg"],
            "floor": themes[theme_index]["floor"],
            "platforms": platforms,
            "is_boss": is_boss,
            "enemies": allowed_enemies
        }
        
    return maps
