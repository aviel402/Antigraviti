# maps9.py

# נשתמש בזה ליצור משתני שלבים קלים
# המערך מחזיק 20 מפות/שלבים. 
# כל stage_config מגדיר אילו אויבים מופיעים ואת מערך הבמות של הרצפה ("platforms") (גובה מהרצפה, מיקום מהשמאל של העולם)

MAPS_CONFIG = []

theme_colors =['#110915', '#0f1a1a', '#2b100e', '#101010', '#181f2f']

for i in range(1, 21):
    is_boss = (i % 5 == 0)
    bg = theme_colors[i % len(theme_colors)]
    
    platforms =[]
    # נוסיף פלטפורמות במקומות קבועים או תלוי שלב, כדי שלא נלך תמיד על קרקע ישרה
    if not is_boss:
        if i % 2 == 0:
            platforms =[
                {"offset_x": 300, "height": 100, "w": 200},
                {"offset_x": 700, "height": 220, "w": 150},
                {"offset_x": 1200, "height": 120, "w": 250}
            ]
        else:
            platforms =[
                {"offset_x": 500, "height": 150, "w": 400},
            ]

    # כמויות וסוגי האויבים.
    MAPS_CONFIG.append({
        "stage": i,
        "background": bg,
        "platforms": platforms,
        "enemies": {
            # לאויבים נוספו סוגים - walkers (זוחלים), jumpers (קופצניים), shooters (יורים לייזר מהצד)
            "walkers": 0 if is_boss else 2 + (i // 2),
            "jumpers": 0 if is_boss else (i // 3),
            "shooters": 0 if is_boss else (1 if i > 3 else 0) + (i // 5),
            "boss": 1 if is_boss else 0
        }
    })
