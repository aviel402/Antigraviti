def generate_maps():
    maps = {}
    
    themes =[
        {"bg": "#0B1D28", "floor": "#1A3644", "name": "Dark Forest"},      # 1-5 (יער גשם כהה)
        {"bg": "#311C0C", "floor": "#6B431D", "name": "Dusty Canyon"},       # 6-10 (קניון / מדבר חרוך)
        {"bg": "#082138", "floor": "#40769D", "name": "Glacier Peaks"},      # 11-15 (פסגות קרחון קרות)
        {"bg": "#2F0909", "floor": "#4F1414", "name": "Inferno Volcano"}     # 16-20 (וולקן בוער מאובק)
    ]
    
    for stage in range(1, 21):
        theme_index = (stage - 1) // 5
        is_boss = (stage % 5 == 0)
        platforms =[]

        # ====================================================
        # תכנון מוקפד של מבני שלבים אסטרטגיים (פלטפורמות מתרבות על X של 3500 פיקסלים)
        # y_offset מסמל את הגובה מהרצפה למעלה (ברירת מחדל הרצפה בערך ב-80).
        # ====================================================
        
        # שלבים 1 עד 5: סביבה 1 (Forest)
        if stage == 1:
            for offset in range(300, 3000, 600):
                platforms.append({"x": offset, "y_offset": 120, "w": 250, "h": 20})  # במות לאימון 
        elif stage == 2:
            for offset in range(300, 3000, 800):
                # מדרגות טיפוס קלאסי
                platforms.append({"x": offset, "y_offset": 110, "w": 100, "h": 20})
                platforms.append({"x": offset+150, "y_offset": 180, "w": 100, "h": 20})
                platforms.append({"x": offset+300, "y_offset": 250, "w": 200, "h": 20})
        elif stage == 3:
            for offset in range(400, 3000, 1000):
                # חופה ורציפים למטה
                platforms.append({"x": offset, "y_offset": 120, "w": 400, "h": 20})
                platforms.append({"x": offset+200, "y_offset": 220, "w": 400, "h": 20})
        elif stage == 4:
            for offset in range(300, 3000, 400):
                # עמודים בלבד! כיף לאירובאטיקה של דאש (מקפצות גבוהות)
                platforms.append({"x": offset, "y_offset": 140 if offset % 800 == 0 else 240, "w": 120, "h": 20})
        elif stage == 5:
            # בוס יער 1: במות רחבות מאסיביות בצורת טירה לקבלות מחסות ירי.
            platforms.append({"x": 400, "y_offset": 180, "w": 400, "h": 30})
            platforms.append({"x": 1000, "y_offset": 250, "w": 300, "h": 30})
            platforms.append({"x": 1600, "y_offset": 180, "w": 400, "h": 30})
            
        # שלבים 6 עד 10: סביבה 2 (Desert Canyon)
        elif stage == 6:
            for offset in range(300, 3000, 600):
                platforms.append({"x": offset, "y_offset": 150, "w": 180, "h": 20})
                platforms.append({"x": offset+100, "y_offset": 250, "w": 150, "h": 20})
        elif stage == 7:
            for offset in range(200, 3000, 900):
                # מסלול משולב ללכת על "גשר ענק"
                platforms.append({"x": offset, "y_offset": 160, "w": 500, "h": 20})
                platforms.append({"x": offset+600, "y_offset": 100, "w": 200, "h": 20})
        elif stage == 8:
            for offset in range(300, 3000, 750):
                platforms.append({"x": offset, "y_offset": 130, "w": 150, "h": 20})
                platforms.append({"x": offset+200, "y_offset": 190, "w": 150, "h": 20})
                platforms.append({"x": offset+400, "y_offset": 260, "w": 200, "h": 20})
        elif stage == 9:
            # מקפצות זיגזג בלבד - סיוט לשחקנים שלא זזים.
            for offset in range(250, 3000, 500):
                heights =[150, 250, 350, 250]
                idx = (offset//500) % 4
                platforms.append({"x": offset, "y_offset": heights[idx], "w": 180, "h": 20})
        elif stage == 10:
            # זירת הבוס - הר אולימפוס (בנוי מחסות קטנות בצדדים, במת ירי למעלה)
            platforms.append({"x": 500, "y_offset": 160, "w": 120, "h": 20})
            platforms.append({"x": 800, "y_offset": 250, "w": 600, "h": 30})
            platforms.append({"x": 1600, "y_offset": 160, "w": 120, "h": 20})

        # שלבים 11 עד 15: סביבה 3 (Glacier Ice)
        elif stage == 11:
            for offset in range(250, 3500, 700):
                platforms.append({"x": offset, "y_offset": 150, "w": 350, "h": 20})
                platforms.append({"x": offset+450, "y_offset": 280, "w": 150, "h": 20})
        elif stage == 12:
            # מגדלים צפופים (Tower formations) - טובים נגד הסאמונר
            for offset in range(300, 3500, 800):
                platforms.append({"x": offset, "y_offset": 120, "w": 120, "h": 20})
                platforms.append({"x": offset, "y_offset": 220, "w": 120, "h": 20})
                platforms.append({"x": offset, "y_offset": 320, "w": 120, "h": 20})
        elif stage == 13:
            for offset in range(200, 3000, 450):
                platforms.append({"x": offset, "y_offset": 200, "w": 120, "h": 20})
                platforms.append({"x": offset+200, "y_offset": 100, "w": 180, "h": 20})
        elif stage == 14:
             for offset in range(400, 3000, 900):
                 platforms.append({"x": offset, "y_offset": 180, "w": 550, "h": 20})
                 platforms.append({"x": offset+200, "y_offset": 300, "w": 150, "h": 20})
        elif stage == 15:
            # בוס 3 (פצצה אמיתית של משטחי התמודדות למעלה / ומנהרות רצפה)
            platforms.append({"x": 400, "y_offset": 120, "w": 1000, "h": 20}) # Roof platform
            platforms.append({"x": 700, "y_offset": 250, "w": 400, "h": 30}) # Peak Center 
            platforms.append({"x": 1500, "y_offset": 160, "w": 400, "h": 20})

        # שלבים 16 עד 20: סביבה 4 (Inferno Volcano)
        elif stage == 16:
            for offset in range(300, 3500, 600):
                platforms.append({"x": offset, "y_offset": 150, "w": 250, "h": 20})
                platforms.append({"x": offset+350, "y_offset": 270, "w": 120, "h": 20})
        elif stage == 17:
             # עמק עמוק.. בלוקים רק במרומי המערות! 
             for offset in range(500, 3000, 500):
                 platforms.append({"x": offset, "y_offset": 250, "w": 150, "h": 20})
        elif stage == 18:
             # ארנה צמודה.. במות כפולות לאגור דמויות נורמאליות בלי לרמות על הריצפה
             for offset in range(300, 3000, 800):
                 platforms.append({"x": offset, "y_offset": 130, "w": 450, "h": 20})
                 platforms.append({"x": offset+250, "y_offset": 230, "w": 250, "h": 20})
                 platforms.append({"x": offset+550, "y_offset": 320, "w": 150, "h": 20})
        elif stage == 19:
            for offset in range(300, 3500, 400):
                 platforms.append({"x": offset, "y_offset": 180, "w": 100, "h": 20})
        elif stage == 20:
             # הקרב האחרון - אלוף העולם במות גבוהות ומחבואים לנינג'ות המלוכלכות
             platforms.append({"x": 300, "y_offset": 160, "w": 300, "h": 20})
             platforms.append({"x": 800, "y_offset": 250, "w": 600, "h": 30})
             platforms.append({"x": 900, "y_offset": 350, "w": 400, "h": 30}) # Ultimate highest ground! 
             platforms.append({"x": 1600, "y_offset": 160, "w": 300, "h": 20})

        # בניית רשימת סוגי אויבים עלילתית-דינאמית - אויב עפי רמה ! 
        allowed_enemies = ["melee"]
        if stage >= 2: allowed_enemies.append("jumper")
        if stage >= 4: allowed_enemies.append("shooter")
        if stage >= 7: allowed_enemies.append("tank")      
        if stage >= 9: allowed_enemies.append("ninja")     
        if stage >= 11: allowed_enemies.append("summoner") 

        maps[stage] = {
            "name": "BOSS CHAMBER" if is_boss else f"{themes[theme_index]['name']} - Sector {stage}",
            "bg": themes[theme_index]["bg"],
            "floor": themes[theme_index]["floor"],
            "platforms": platforms,
            "is_boss": is_boss,
            "enemies": allowed_enemies
        }
        
    return maps
