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

        # מערך עיצובי לפלטפורמות בשלב (מרחיב טווח עמוק לעד 3000 קואורדינאטות).
        if stage % 5 == 1:
            for offset in range(300, 2800, 600): platforms.append({"x": offset, "y_offset": 120, "w": 250, "h": 20})
        elif stage % 5 == 2:
            for offset in range(300, 2800, 800):
                platforms.append({"x": offset, "y_offset": 110, "w": 100, "h": 20})
                platforms.append({"x": offset+150, "y_offset": 180, "w": 100, "h": 20})
                platforms.append({"x": offset+300, "y_offset": 250, "w": 150, "h": 20})
        elif stage % 5 == 3:
            for offset in range(400, 2800, 900):
                platforms.append({"x": offset, "y_offset": 140, "w": 350, "h": 20})
                platforms.append({"x": offset+200, "y_offset": 280, "w": 350, "h": 20})
        elif stage % 5 == 4:
            for offset in range(300, 2800, 350):
                platforms.append({"x": offset, "y_offset": 150 if offset % 700 == 0 else 250, "w": 120, "h": 20})
        elif is_boss: # פלטפורמות סטטוס קרב עבור הבאסים
            platforms.append({"x": 300, "y_offset": 160, "w": 250, "h": 20})
            platforms.append({"x": 900, "y_offset": 250, "w": 800, "h": 30})
            platforms.append({"x": 1900, "y_offset": 160, "w": 250, "h": 20})

        # מבנה "איכות העצים" נחשפת בעצמי העכבות: מתחיל ממכות מגעות ודופקות מתעבה ליחס.
        allowed_enemies = ["melee"]
        if stage >= 2: allowed_enemies.append("jumper")
        if stage >= 4: allowed_enemies.append("flyer")     # מעופפים בשמים מצטלבים
        if stage >= 6: allowed_enemies.append("shooter")   
        if stage >= 8: allowed_enemies.append("bomber")    # סכנת הפציעות מתקרבת משלב 8. פליקים
        if stage >= 10: allowed_enemies.append("tank")      
        if stage >= 13: allowed_enemies.append("ninja")    # שלבים עוקבים, נינגות. 
        if stage >= 15: allowed_enemies.append("shield")   # מגנים נוזקים ענקית ! חיבים לעקוף קיר
        if stage >= 17: allowed_enemies.append("summoner") 

        maps[stage] = {
            "name": f"CHAMBER MASTER" if is_boss else f"{themes[theme_index]['name']} - Sec {stage % 5}",
            "bg": themes[theme_index]["bg"],
            "floor": themes[theme_index]["floor"],
            "platforms": platforms,
            "is_boss": is_boss,
            "enemies": allowed_enemies
        }
    return maps
