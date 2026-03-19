# maps9.py
import random

def generate_maps():
    maps = {}
    themes =[
        {"bg": "#0B1D28", "floor": "#1A3644", "name": "Forest"},
        {"bg": "#311C0C", "floor": "#6B431D", "name": "Desert"},
        {"bg": "#082138", "floor": "#40769D", "name": "Ice"},
        {"bg": "#2F0909", "floor": "#4F1414", "name": "Volcano"}
    ]
    
    stage_len = 10000
    
    for stage in range(1, 21):
        theme_index = (stage - 1) // 5
        is_boss = (stage % 5 == 0)
        platforms = []
        walls = []
        pits = []
        coins = []

        if is_boss:
            stage_len = 3000 # שלבי בוס קצרים יותר
            platforms.append({"x": 400, "y_offset": 180, "w": 400, "h": 30})
            platforms.append({"x": 1000, "y_offset": 250, "w": 300, "h": 30})
        else:
            # יצירת מפה רנדומאלית-למחצה באורך 10,000 פיקסלים
            current_x = 500
            while current_x < stage_len - 1000:
                choice = random.randint(0, 4)
                
                if choice == 0 or choice == 1:
                    # פלטפורמות רגילות
                    y_off = random.choice([120, 180, 240])
                    w = random.choice([150, 250, 400])
                    platforms.append({"x": current_x, "y_offset": y_off, "w": w, "h": 20})
                    # סיכוי למטבעות על הפלטפורמה
                    if random.random() > 0.5:
                        for cx in range(0, w, 50):
                            coins.append({"x": current_x + cx + 10, "y_offset": y_off + 30})
                    current_x += w + random.randint(100, 300)
                    
                elif choice == 2:
                    # קיר חוסם
                    wall_h = random.choice([100, 150])
                    walls.append({"x": current_x, "h": wall_h})
                    current_x += 300
                    
                elif choice == 3:
                    # בור ברצפה (Pit)
                    pit_w = random.choice([150, 250])
                    pits.append({"x": current_x, "w": pit_w})
                    # שים פלטפורמה קטנה מעל או לפני הבור כדי שאפשר יהיה לעבור
                    platforms.append({"x": current_x - 50, "y_offset": 120, "w": pit_w + 100, "h": 20})
                    current_x += pit_w + 200
                    
                elif choice == 4:
                    # רק מטבעות
                    for cx in range(0, 300, 50):
                        coins.append({"x": current_x + cx, "y_offset": 50})
                    current_x += 400

        # סוגי אויבים
        allowed_enemies = ["melee", "shooter", "jumper"]
        if stage >= 3: allowed_enemies.append("flyer")
        if stage >= 5: allowed_enemies.append("bomber")
        if stage >= 7: allowed_enemies.append("tank")      
        if stage >= 9: allowed_enemies.append("ghost") # חדש!
        if stage >= 11: allowed_enemies.append("ninja")     
        if stage >= 13: allowed_enemies.append("thwomp") # חדש!
        if stage >= 15: allowed_enemies.append("summoner") 
        if stage >= 17: allowed_enemies.append("shield")

        maps[stage] = {
            "name": f"BOSS: {themes[theme_index]['name']}" if is_boss else f"{themes[theme_index]['name']} - {stage}",
            "bg": themes[theme_index]["bg"],
            "floor": themes[theme_index]["floor"],
            "length": stage_len,
            "platforms": platforms,
            "walls": walls,
            "pits": pits,
            "coins": coins,
            "is_boss": is_boss,
            "enemies": allowed_enemies
        }
    return maps
