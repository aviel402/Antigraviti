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
        
        # אורך השלב משתנה! שלב 1 = 3000. כל שלב +500.
        stage_length = 3000 + (stage * 500)

        if not is_boss:
            # פלטפורמות קופצות עד סוף השלב הדינמי
            for offset in range(800, stage_length - 500, 700):
                platforms.append({"x": offset, "y_offset": 120 + (offset % 100), "w": 250, "h": 20})
            
            # קירות לחסימה אסטרטגית
            for offset in range(1200, stage_length - 1000, 1500):
                walls.append({"x": offset, "h": 150, "w": 40}) 
        else:
            # זירת בוס מרווחת בסוף השלב (אורך השלב של בוס יהיה תמיד 4000)
            stage_length = 4000
            for offset in range(1000, 3000, 800):
                platforms.append({"x": offset, "y_offset": 160, "w": 300, "h": 20})
                platforms.append({"x": offset+400, "y_offset": 280, "w": 200, "h": 20})

        allowed_enemies = ["melee"]
        if stage >= 2: allowed_enemies.append("jumper")
        if stage >= 3: allowed_enemies.append("flyer")     
        if stage >= 5: allowed_enemies.append("shooter")   
        if stage >= 7: allowed_enemies.append("bomber")    
        if stage >= 9: allowed_enemies.append("tank")      
        if stage >= 12: allowed_enemies.append("ninja")    
        if stage >= 14: allowed_enemies.append("shield")   
        # הערה: Summoner (קוסם) נמחק לחלוטין מכאן

        maps[stage] = {
            "name": f"SYSTEM OVERLORD" if is_boss else f"{themes[theme_index]['name']} - SECTOR {stage % 5 if stage % 5 != 0 else 5}",
            "bg": themes[theme_index]["bg"],
            "floor": themes[theme_index]["floor"],
            "neon": themes[theme_index]["neon"],
            "platforms": platforms,
            "walls": walls,
            "is_boss": is_boss,
            "boss_type": theme_index + 1 if is_boss else 0, # איזה בוס זה 1 עד 4
            "enemies": allowed_enemies,
            "length": stage_length # אורך מפה לסקריפט הראשי!
        }
    return maps
