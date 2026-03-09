def generate_maps():
    maps = {}
    
    themes =[
        {"bg": "#0B1D28", "floor": "#1A3644", "name": "Dark Forest", "decor": "forest"},     # 1-5
        {"bg": "#311C0C", "floor": "#6B431D", "name": "Dusty Canyon", "decor": "desert"},      # 6-10
        {"bg": "#082138", "floor": "#40769D", "name": "Glacier Peaks", "decor": "ice"},         # 11-15
        {"bg": "#2F0909", "floor": "#4F1414", "name": "Inferno Volcano", "decor": "magma"}       # 16-20
    ]
    
    for i in range(1, 21):
        theme_index = (i - 1) // 5
        is_boss = (i % 5 == 0)
        
        platforms = []
        if not is_boss and i > 2:
            platforms =[
                {"x": 300, "y_offset": 120, "w": 200, "h": 20},
                {"x": 650, "y_offset": 220, "w": 150, "h": 20},
                {"x": 1000, "y_offset": 100, "w": 280, "h": 20}
            ]
        
        # בניית רשימת סוגי אויבים לפי השלב כדי לייצר עלילת התפתחות הקושי:
        allowed_enemies = ["melee"]
        if i >= 2: allowed_enemies.append("jumper")
        if i >= 4: allowed_enemies.append("shooter")
        if i >= 7: allowed_enemies.append("tank")      # טנק אגרסיבי מתחיל משלב 7
        if i >= 9: allowed_enemies.append("ninja")     # מפלצות דאש מהירות ממש מופיעות ב 9
        if i >= 11: allowed_enemies.append("summoner") # השחקנים החכמים מאחור מתחילים מ 11

        maps[i] = {
            "name": "BOSS CHAMBER" if is_boss else f"{themes[theme_index]['name']} - Sector {i}",
            "bg": themes[theme_index]["bg"],
            "floor": themes[theme_index]["floor"],
            "platforms": platforms,
            "is_boss": is_boss,
            "enemies": allowed_enemies
        }
        
    return maps
