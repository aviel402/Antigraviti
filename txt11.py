# txt11.py
# כל הטקסטים, השמות והגדרות הקבוצות של המשחק

TEXTS = {
    "title": "Manager PRO XI",
    "sub_title": "בחר מועדון ותתחיל במסע",
    "budget": "תקציב: ₪",
    "tabs": {
        "squad": "מגרש והרכב ⚽",
        "market": "שוק ההעברות 🛒",
        "table": "טבלת הליגה 🏆",
        "calendar": "יומן ואימונים 📅"
    },
    "squad_pitch_title": "ההרכב הפותח (לחץ על שחקן להחלפה)",
    "squad_bench_title": "ספסל המחליפים",
    "training_title": "מחנה אימונים",
    "training_desc": "שלח את הקבוצה למחנה אימונים מרוכז. עלות: 15,000 ₪. ישפר מדדים ל-3 שחקנים אקראיים.",
    "btn_train": "התחל אימון (15,000 ₪)",
    "market_desc": "קנה ומכור שחקנים כדי לחזק את הסגל. שים לב לתקציב שלך!",
    "btn_play_match": "▶️ שחק מחזור ",
    "btn_reboot": "מחק שמירה והתחל מחדש",
    "stats": ["PAC", "SHO", "PAS", "DRI", "DEF", "PHY"],
    "status_injured": "🚑 פצוע",
    "status_red": "🟥 מורחק"
}

FIRST_NAMES = [
    "ערן", "מנור", "אוסקר", "מונס", "דיא", "דניאל", "עומר", "ליונל", "כריסטיאנו", 
    "קיליאן", "קווין", "ארלינג", "לוקה", "הארי", "מוחמד", "אייל", "רועי", "יהב"
]
LAST_NAMES = [
    "זהבי", "סולומון", "גלוך", "דבור", "סבע", "מסי", "רונאלדו", "אמבפה", 
    "דה ברוינה", "הלאנד", "מודריץ'", "קיין", "סלאח", "חזיזה", "כהן", "פרץ"
]

# חלוקה ל-2 ליגות
LEAGUES_DB = {
    "israel": [
        {"name": "מכבי תל אביב", "primary": "#fcc70e", "secondary": "#051660"},
        {"name": "מכבי חיפה", "primary": "#036531", "secondary": "#ffffff"},
        {"name": "הפועל באר שבע", "primary": "#dd1c20", "secondary": "#ffffff"},
        {"name": "בית\"ר ירושלים", "primary": "#fee411", "secondary": "#010101"},
        {"name": "הפועל תל אביב", "primary": "#e30613", "secondary": "#ffffff"},
        {"name": "מכבי נתניה", "primary": "#fed501", "secondary": "#010101"}
    ],
    "europe": [
        {"name": "ריאל מדריד", "primary": "#ffffff", "secondary": "#000000"},
        {"name": "מנצ'סטר סיטי", "primary": "#6CABDD", "secondary": "#1C2C5B"},
        {"name": "ברצלונה", "primary": "#004D98", "secondary": "#A50044"},
        {"name": "באיירן מינכן", "primary": "#DC052D", "secondary": "#ffffff"},
        {"name": "פריז סן ז'רמן", "primary": "#004170", "secondary": "#DA291C"},
        {"name": "ארסנל", "primary": "#EF0107", "secondary": "#ffffff"}
    ]
}
