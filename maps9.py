# maps9.py
def generate_maps():
    maps = {}
    themes =[
        {"bg": "#0B1D28", "floor": "#1A3644", "name": "World 1: Dark Forest"},
        {"bg": "#311C0C", "floor": "#6B431D", "name": "World 2: Dusty Canyon"},
        {"bg": "#082138", "floor": "#40769D", "name": "World 3: Glacier Peaks"},
        {"bg": "#2F0909", "floor": "#4F1414", "name": "World 4: Inferno Volcano"}
    ]
    
    for stage in range(1, 21):
        theme_index = (stage - 1) // 5
        is_boss = (stage % 5 == 0)
        platforms = []

        # בניית פלטפורמות
        if stage % 5 == 1:
            for offset in range(300, 2500, 600): platforms.append({"x": offset, "y_offset": 120, "w": 250, "h": 20})
        elif stage % 5 == 2:
            for offset in range(300, 2500, 800):
                platforms.append({"x": offset, "y_offset": 110, "w": 100, "h": 20})
                platforms.append({"x": offset+150, "y_offset": 180, "w": 100, "h": 20})
        elif stage % 5 == 3:
            for offset in range(400, 2500, 1000):
                platforms.append({"x": offset, "y_offset": 120, "w": 400, "h": 20})
                platforms.append({"x": offset+200, "y_offset": 220, "w": 400, "h": 20})
        elif stage % 5 == 4:
            for offset in range(300, 2500, 400):
                platforms.append({"x": offset, "y_offset": 140 if offset % 800 == 0 else 240, "w": 120, "h": 20})
        elif is_boss:
            platforms.append({"x": 400, "y_offset": 180, "w": 400, "h": 30})
            platforms.append({"x": 1000, "y_offset": 250, "w": 300, "h": 30})
            platforms.append({"x": 1600, "y_offset": 180, "w": 400, "h": 30})

        allowed_enemies = ["melee"]
        if stage >= 2: allowed_enemies.append("jumper")
        if stage >= 4: allowed_enemies.append("shooter")
        if stage >= 7: allowed_enemies.append("tank")      
        if stage >= 9: allowed_enemies.append("ninja")     
        if stage >= 11: allowed_enemies.append("summoner") 

        maps[stage] = {
            "name": f"{themes[theme_index]['name']} - Sector {stage % 5 if stage % 5 != 0 else 5}",
            "bg": themes[theme_index]["bg"],
            "floor": themes[theme_index]["floor"],
            "platforms": platforms,
            "is_boss": is_boss,
            "enemies": allowed_enemies
        }
    return maps
