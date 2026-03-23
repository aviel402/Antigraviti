# maps9.py
def generate_maps():
    maps = {}
    themes =[
        {"bg": "#050B14", "floor": "#0F2027", "neon": "#00f3ff", "name": "CYBER FOREST"},
        {"bg": "#140A05", "floor": "#2C150A", "neon": "#ff5e00", "name": "WASTELAND"},
        {"bg": "#020A14", "floor": "#0A2540", "neon": "#009dff", "name": "FROST MATRIX"},
        {"bg": "#1A0000", "floor": "#330000", "neon": "#ff003c", "name": "CORE INFERNO"}
    ]
    
    for stage in range(1, 21):
        theme_index = (stage - 1) // 5
        is_boss = (stage % 5 == 0)
        platforms = []
        walls = [] 

        # חישוב אורך המפה הנוכחית (גדל ב-500 כל שלב. שלב 1: 4000)
        current_map_length = 4000 + ((stage - 1) * 500)

        # פריסת פלטפורמות ומכשולים לאורך המפה הדינמית
        if not is_boss:
            for offset in range(800, current_map_length - 1000, 700):
                platforms.append({"x": offset, "y_offset": 120 + (offset % 100), "w": 250, "h": 20})
            
            for offset in range(1200, current_map_length - 1500, 1500):
                walls.append({"x": offset, "h": 150, "w": 40}) 
        else:
            # זירת בוס - הפלטפורמות תואמות לאורך המפה הנוכחי
            for offset in range(1000, current_map_length - 1000, 1000):
                platforms.append({"x": offset, "y_offset": 160, "w": 300, "h": 20})
                platforms.append({"x": offset+400, "y_offset": 280, "w": 200, "h": 20})

        # הוספת כל סוגי האויבים בהדרגה (הקוסם/summoner הוסר)
        allowed_enemies = ["melee"]
        if stage >= 2: allowed_enemies.append("jumper")
        if stage >= 3: allowed_enemies.append("flyer")     
        if stage >= 5: allowed_enemies.append("shooter")   
        if stage >= 7: allowed_enemies.append("bomber")    
        if stage >= 9: allowed_enemies.append("tank")      
        if stage >= 12: allowed_enemies.append("ninja")    
        if stage >= 14: allowed_enemies.append("shield")   

        # בחירת בוס ייחודי לפי העולמות!
        boss_type = "boss_forest" # ברירת מחדל
        if stage == 10: boss_type = "boss_desert"
        if stage == 15: boss_type = "boss_ice"
        if stage == 20: boss_type = "boss_core"

        maps[stage] = {
            "name": f"SYSTEM OVERLORD" if is_boss else f"{themes[theme_index]['name']} - SECTOR {stage % 5 if stage % 5 != 0 else 5}",
            "bg": themes[theme_index]["bg"],
            "floor": themes[theme_index]["floor"],
            "neon": themes[theme_index]["neon"],
            "platforms": platforms,
            "walls": walls,
            "is_boss": is_boss,
            "boss_type": boss_type,
            "map_length": current_map_length, # שומרים את האורך ל-JS
            "enemies": allowed_enemies
        }
    return maps
