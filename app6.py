import random
import uuid
from flask import Flask, render_template_string, request, jsonify, session, url_for

app = Flask(__name__)
app.secret_key = 'dm_pro_fixe_shop_v8'

# ==========================================
# 📘 מאגר נתונים (DATABASE)
# ==========================================
ITEMS_DB = {
    "שיקוי חיים": {"type": "heal", "val": 40, "desc": "מרפא 40 חיים", "price": 20},
    "תחבושת": {"type": "heal", "val": 15, "desc": "עוצר דימום"},
    "מנת קרב": {"type": "heal", "val": 10, "desc": "אוכל"},
    "רימון רעל": {"type": "dmg_item", "val": 30, "desc": "נזק אויב"},
    "שיקוי כוח": {"type": "buff", "val": 5, "desc": "נזק זמני"},
    "שיקוי חיים גדול": {"type": "heal", "val": 80, "desc": "מרפא 80", "price": 40},
    "שיקוי חיים אגדי": {"type": "heal", "val": 150, "desc": "מרפא 150"},
    "רימון אש": {"type": "dmg_item", "val": 50, "desc": "פיצוץ אש ענק", "price": 60},
    "רימון קרח": {"type": "dmg_item", "val": 35, "desc": "מקפיא מפלצת"},
    
    # === חפצים למכירה למקח ===
    "יהלום": {"type": "sell", "val": 100, "desc": "ימכר בחנות"},
    "אודם": {"type": "sell", "val": 60, "desc": "ימכר בחנות"},
    "ספיר": {"type": "sell", "val": 80, "desc": "ימכר בחנות"},
    "אזמרגד": {"type": "sell", "val": 90, "desc": "ימכר בחנות"},
    
    # === מפתחות ===
    "מפתח ברזל": {"type": "key", "val": 0, "desc": "פותח תיבות נפוצות"},
    "מפתח זהב": {"type": "key", "val": 0, "desc": "פותח תיבות מלכות"},
    "מפתח עתיק": {"type": "key", "val": 0, "desc": "פותח שערים מיוחדים"}
}

ENEMIES = [
    {"name": "גובלין ירוק", "hp": 30, "max": 30, "atk": 5, "xp": 10, "loot": ["מנת קרב", "תחבושת"]},
    {"name": "עכביש רעיל", "hp": 35, "max": 35, "atk": 7, "xp": 15, "loot": ["רימון רעל"]},
    {"name": "אורק שומר", "hp": 60, "max": 60, "atk": 12, "xp": 40, "loot": ["שיקוי חיים", "מפתח ברזל"]},
    {"name": "שלד כסוף", "hp": 45, "max": 45, "atk": 10, "xp": 30, "loot": ["אודם"]},
    {"name": "אביר פאנטום", "hp": 100, "max": 100, "atk": 18, "xp": 100, "loot": ["שיקוי חיים גדול", "ספיר"]},
    {"name": "קוסם שחור", "hp": 70, "max": 70, "atk": 25, "xp": 90, "loot": ["רימון אש", "מפתח עתיק"]},
    {"name": "בוס דרקון זהב", "hp": 250, "max": 250, "atk": 25, "xp": 500, "loot": ["יהלום", "אזמרגד", "מפתח זהב", "שיקוי חיים אגדי"]},
    {"name": "שומר המקוללים", "hp": 130, "max": 130, "atk": 20, "xp": 150, "loot": ["אזמרגד"]}
]

BIOMES = [
    {"name": "צינוק טחוב", "icon": "⛓️"}, {"name": "אולם אבן", "icon": "🏛️"},
    {"name": "מערה קפואה", "icon": "❄️"}, {"name": "יער העד", "icon": "🌲"},
    {"name": "כלא אסורים", "icon": "🚪"}, {"name": "מרתף מוצף", "icon": "💧"},
    {"name": "מגדל ארקיין", "icon": "🔮"}, {"name": "ארמון רעפים", "icon": "🏰"}
]

# דברי הסוחר המוזר
MERCHANT_GREETINGS = [
    "סחורות טובות לאנשים שמחים! מה תיקח?",
    "זהירות, הבוסים בקומה הבאה משוגעים. תקנה שיקוי!",
    "אני קונה יהלומים, מוכר התקפות. דיל טוב.",
    "החיים קצרים. השקע בשדרוג הלהב שלך היום."
]

# ==========================================
# ⚙️ מנוע משחק ומשאבים
# ==========================================
class Engine:
    def __init__(self, state=None):
        if not state:
            self.state = {
                "x": 0, "y": 0,
                "stats": {"hp": 100, "max": 100, "gold": 20, "atk_base": 10, "atk_bonus": 0},
                "inv": ["שיקוי חיים", "תחבושת"],
                "map": {},
                "visited": ["0,0"],
                "log": [{"text": "דלת צינוק חורקת. אתה מתחיל מסע. אסוף כסף חפש את הסוחר.", "type": "sys"}]
            }
            self.create_room(0, 0, safe=True)
        else:
            self.state = state

    def pos(self): return f"{self.state['x']},{self.state['y']}"
    
    def log(self, txt, t="game"): self.state["log"].append({"text": txt, "type": t})

    def create_room(self, x, y, safe=False):
        k = f"{x},{y}"
        if k in self.state["map"]: return

        r_data = {
            "name": "", "icon": "", "enemy": None, "items": [], 
            "is_shop": False, "chest": False
        }

        if safe:
            r_data["name"] = "מעגל ריפוי"
            r_data["icon"] = "🏠"
            self.state["map"][k] = r_data
            return

        rnd = random.random()
        # 12% Shop
        if rnd < 0.12:
            r_data["name"] = "דוכן סוחר נודד"
            r_data["icon"] = "🏪"
            r_data["is_shop"] = True
            r_data["greeting"] = random.choice(MERCHANT_GREETINGS)
        else:
            biome = random.choice(BIOMES)
            r_data["name"] = biome["name"]
            r_data["icon"] = biome["icon"]
            
            # 40% אויב
            if random.random() < 0.40:
                r_data["enemy"] = random.choice(ENEMIES).copy()
            # אם אין אויב -> סיכוי לתיבת אוצר נעולה
            elif random.random() < 0.15:
                r_data["chest"] = True
                r_data["name"] += " (כספת נסתרת)"
                
            # סיכוי קטן שמישהו איבד ציוד סתם ככה על הרצפה
            if random.random() < 0.3:
                 r_data["items"].append(random.choice(["תחבושת", "מנת קרב", "אודם", "מפתח ברזל"]))

        self.state["map"][k] = r_data

    # --- פתיחת חדר ומפות ---
    def move(self, dx, dy):
        r_now = self.state["map"][self.pos()]
        # אם יש אויב שחוסם (אתגר משחקי: אתה לא יכול לברוח לפני שתנצח)
        if r_now.get("enemy"):
            self.log("הדלת נעולה. האויב בחדר חוסם ממעבר!", "danger")
            return

        self.state["x"] += dx
        self.state["y"] += dy
        k = self.pos()
        
        self.create_room(self.state["x"], self.state["y"])
        if k not in self.state["visited"]: self.state["visited"].append(k)
        
        r = self.state["map"][k]
        self.log(f"הגעת ל-{r['name']}.", "sys")
        if r.get("is_shop"): self.log("🏪 יש פה סוחר שיכול לקנות ממך ציוד וישדרג נשק!", "gold")
        if r.get("chest"): self.log("🗝️ בפינה חשוכה עומדת תיבת אוצר עתיקה נעולה...", "info")
        if r.get("enemy"): self.log(f"⚠️ נזהרת מ-{r['enemy']['name']} בצללים!", "danger")
        if r["items"]: self.log(f"🔎 נפל לאויבים ציוד: {', '.join(r['items'])}", "success")

    # --- מנגנון תקיפה שופץ מחושב בatk_base! ---
    def attack(self):
        r = self.state["map"][self.pos()]
        if not r.get("enemy"): return self.log("האוויר כאן בטוח לתקיפה. שמר אנרגיה.", "info")
        
        enemy = r["enemy"]
        base = self.state["stats"]["atk_base"] + self.state["stats"]["atk_bonus"]
        # חישוב נזק הנגן פלאי אחוזי Random טקטי:
        player_dmg = random.randint(base - 3, base + 5)
        
        enemy["hp"] -= player_dmg
        self.log(f"⚔️ הכת את ה-{enemy['name']} ומחקת {player_dmg} מנשמתו!", "sys")
        
        if enemy["hp"] <= 0:
            gold_drop = random.randint(8, 20)
            self.state["stats"]["gold"] += gold_drop
            self.log(f"💀 אויב {enemy['name']} נפל! צברת +{gold_drop}💰", "gold")
            if enemy.get("loot"): r["items"].extend(enemy["loot"])
            r["enemy"] = None 
        else:
            e_dmg = max(1, enemy["atk"] - random.randint(0, 3))
            self.state["stats"]["hp"] -= e_dmg
            self.log(f"🩸 פגיעת נגד. חטפת {e_dmg} נזק מדמם!", "danger")

    # --- אוצר התיבה השומרת במפתח! ---
    def open_chest(self):
        r = self.state["map"][self.pos()]
        if not r.get("chest"): return
        
        # חיפוש האם בתיק השחקן יש "מפתח" בכל צורה שהיא
        key_held = None
        for it in self.state["inv"]:
            if ITEMS_DB.get(it) and ITEMS_DB[it]["type"] == "key":
                key_held = it
                break
                
        if key_held:
            self.state["inv"].remove(key_held) # "תבזבז מפתח אחד בשימוש"
            r["chest"] = False # בטל את התיבה להמשך חזור באזור הלוז הזה!
            gold = random.randint(50, 150)
            self.state["stats"]["gold"] += gold
            prize = random.choice(["יהלום", "שיקוי חיים אגדי", "רימון אש"])
            self.state["inv"].append(prize)
            self.log(f"✨ הקליק של מנעול! הבזבת מפתח: השגת בזיון: {prize} ועוד {gold}🪙!!", "gold")
        else:
            self.log("🔒 תיבה מאסיבית ואין לך שום מפתח לתעל תפסיחת פיתולי המתכת בתיק שלך!", "danger")

    def take(self):
        r = self.state["map"][self.pos()]
        if not r["items"]: return self.log("אתה בקושי חומס לפרצות ריקים.", "info")
        for item in r["items"]: self.state["inv"].append(item)
        self.log(f"אספתם לחגורה שלך את הקצוות החופרניים מהעצים...(+{len(r['items'])}).", "success")
        r["items"] = [] 

    # --- פונקצית השימוש בפריטים המקוצרים הרגילת מהאינבוץ === 
    def use_item(self, item_name):
        if item_name not in self.state["inv"]: return
        eff = ITEMS_DB.get(item_name)
        if not eff: return

        if eff["type"] == "heal":
            st = self.state["stats"]
            if st["hp"] >= st["max"]: return self.log("מד האויר מרגיש שלם ואספחת חינמית תבלוף תפרוקות לב. ", "info")
            st["hp"] = min(st["max"], st["hp"] + eff["val"])
            self.log(f"שמת את הקצה. גוף ריפא והופקע בשחול (מבוטס ב-{eff['val']} ❤️)", "success")
            self.state["inv"].remove(item_name)
            
        elif eff["type"] == "buff":
            self.state["stats"]["atk_bonus"] += eff["val"]
            self.log(f"טופחת השמש המכוון חודדת... הברחת שיקוי התגבזה(+{eff['val']} לשעיית הנזקים החופרית בחוץ).", "gold")
            self.state["inv"].remove(item_name)
            
        elif eff["type"] == "dmg_item":
            r = self.state["map"][self.pos()]
            if r.get("enemy"):
                r["enemy"]["hp"] -= eff["val"]
                self.log(f"💥 בום קלאטי!! זרימת {item_name} רסיסה הפועה שירח כביכול -{eff['val']} שפיכות דינמיקות.", "success")
                self.state["inv"].remove(item_name)
                if r["enemy"]["hp"] <= 0:
                     self.log("תקיפה מזוקת ריח טיוורת עיווה בתוכל חירשו. אין אוייב תחימה באזולו.", "gold")
                     r["enemy"] = None
            else:
                self.log("חסכן בריח פלא מפיקה יחסון אם ירמה שירקה צפה על לא מיעוות איפה. חבבי אוייב תמיד מתחיל לחץ זריה.", "info")


    # ========================== מנהימות המסחר (NEW SYSTEM)!
    def sell_junk(self):
        r = self.state["map"][self.pos()]
        if not r.get("is_shop"): return
        
        profit = 0
        leftover = []
        sold_count = 0
        for item in self.state["inv"]:
            if item in ITEMS_DB and ITEMS_DB[item]["type"] == "sell":
                profit += ITEMS_DB[item]["val"]
                sold_count += 1
            else:
                leftover.append(item)
                
        if sold_count > 0:
            self.state["inv"] = leftover
            self.state["stats"]["gold"] += profit
            self.log(f"💰 'מרשרשים בשבילך, חפצים בשבילי!' מכרת אוצרות ברווח: +{profit} זהב", "gold")
        else:
            self.log("'סלח לי לוחם... בכיסים שלך אין לי מוצרי חומרה מניבי תשואה למנמכת...!' ", "danger")

    def buy(self, action_id):
        st = self.state["stats"]
        r = self.state["map"][self.pos()]
        if not r.get("is_shop"): return

        costs = { "upg_hp": 80, "upg_atk": 100, "buy_heal": 35, "buy_bomb": 55 }
        price = costs.get(action_id, 9999)
        
        if st["gold"] < price:
             return self.log("מוכר נועץ על הקרקע ומקריין למול שברי האפחית...'חסרים לנו מזדומניות חמיצר ! ' 💵 לא מספיק.. ", "danger")
             
        st["gold"] -= price
        if action_id == "upg_hp":
            st["max"] += 20
            st["hp"] += 20
            self.log("שדרוג סקריט חיזק חורחוב ! כוחותך בראו חום דלוק המועלה. MAX HP +20❤️.", "success")
        elif action_id == "upg_atk":
            st["atk_base"] += 5
            self.log("הרבצת החמוך חינח מתזות התכלה חדים מהחלון והברישו מתמטי פארוקס . תצלח חוק התקרפת! ATK Base +5⚔️.", "success")
        elif action_id == "buy_heal":
             self.state["inv"].append("שיקוי חיים גדול")
             self.log("רכשת מצינזה מחומשת תת כפלימה שיכיו גג.", "sys")
        elif action_id == "buy_bomb":
             self.state["inv"].append("רימון אש")
             self.log("רכשת נשם מודבכת למקרת הקסוח! חדית נפילים פליאטרית להמחושי התפצתית רסקיפ בועה חם! 🔥", "sys")

    # ---- 
    def get_ui_data(self):
        k = self.pos()
        r = self.state["map"][k]
        grid = []
        for dy in range(1, -2, -1):
            row = []
            for dx in range(-1, 2):
                p2 = f"{self.state['x']+dx},{self.state['y']+dy}"
                val, cls = "", "fog"
                if dx==0 and dy==0: val, cls = "🏃‍♂️", "player"
                elif p2 in self.state["visited"]:
                    val = "💀" if self.state["map"][p2].get("enemy") else self.state["map"][p2]["icon"]
                    cls = "known"
                row.append({"val":val, "cls":cls})
            grid.append(row)
            
        atk_visual = self.state["stats"]["atk_base"] + self.state["stats"]["atk_bonus"]

        return {
            "hp": self.state["stats"]["hp"], "max_hp": self.state["stats"]["max"],
            "gold": self.state["stats"]["gold"], "atk": atk_visual,
            "inv": self.state["inv"], "log": self.state["log"][-20:], # הגבלה בוטנית לקווצו דפופס נראח חומר
            
            "room_name": r["name"], "is_shop": r.get("is_shop", False), "shop_greet": r.get("greeting", ""),
            "items": r["items"], "enemy": r.get("enemy"), "chest": r.get("chest"),
            
            "map_grid": grid
        }

# ==========================================
# REST API 
# ==========================================
@app.route("/")
def index():
    if "uid" not in session: session["uid"] = str(uuid.uuid4())
    home_url = "/" 
    api = url_for("process")
    return render_template_string(HTML, api=api, home=home_url)

@app.route("/game/process", methods=["POST"])
def process():
    d = request.json
    try: eng = Engine(session.get("game_dmp"))
    except: eng = Engine(None)

    act = d.get("action")
    val = d.get("val")

    if eng.state["stats"]["hp"] <= 0 and act != "reset": return jsonify({"dead": True})

    if act == "move": eng.move(*val)
    elif act == "attack": eng.attack()
    elif act == "take": eng.take()
    elif act == "use": eng.use_item(val)
    elif act == "sell": eng.sell_junk()
    elif act == "buy": eng.buy(val)
    elif act == "open_chest": eng.open_chest()
    elif act == "reset": eng = Engine(None)

    session["game_dmp"] = eng.state
    return jsonify(eng.get_ui_data())


# ==========================================
# HTML/CSS/JS CLIENT השילוט הגישרוקי החדשות!!! 
# ==========================================
HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=0">
<title>דאנג'ן פרו (כלכלה כלונה מחוז)</title>
<style>
    @import url('https://fonts.googleapis.com/css2?family=Arimo:wght@400;700&display=swap');
    
    :root { --bg:#1a1921; --panel:#282631; --panel2: #3a3746; --acc:#e6c433; --border:#4a4659;}
    body { background: var(--bg); color: #dedde6; margin: 0; font-family: 'Arimo', sans-serif; display: flex; flex-direction: column; height: 100vh; overflow:hidden;}
    
    header { background: #131217; padding: 12px; display: flex; justify-content: space-between; align-items:center; border-bottom: 3px solid var(--border);}
    .title {font-weight:900; color:var(--acc); letter-spacing:2px; margin:0;}
    .stat-badge { background: #32303c; border:1px solid #666; padding: 4px 8px; border-radius: 4px; font-size: 13px; font-weight: bold;}
    
    .viewport { flex: 1; display: grid; grid-template-columns: 2fr 1fr; gap: 8px; padding: 10px; overflow: hidden; background:radial-gradient(circle at center, #262331 0%, #151419 100%);}
    
    /* LEFT TACTIC SCENNER PANAL -- (Map & Context Interactions!)*/
    .side-panel { display: flex; flex-direction: column; gap: 10px; }
    .map-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 3px; margin: 0 auto; width: 140px; }
    .map-cell { height: 44px; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; font-size: 22px; border-radius: 4px; box-shadow:inset 0 0 10px rgba(0,0,0,1);}
    .map-cell.player { border: 2px solid lime; background: rgba(10,100,20, 0.4); }
    .map-cell.known { background: rgba(255,255,255, 0.1); border:1px solid rgba(255,255,255, 0.2); }

    .room-card { background: var(--panel2); border-left: 5px solid var(--acc); border-radius: 4px; padding: 10px; text-align: center; display:flex; flex-direction:column; gap:8px;}
    .items-alert { font-size: 11px; color: lime; background: rgba(0,255,0,0.1); border:1px solid lime; padding: 4px; border-radius: 4px; display:none;}

    .dynamic-interaction {display:none; background:#2b0e0e; padding:10px; border-radius:5px; border:2px dashed #923a3a; display:flex; flex-direction:column; gap:5px; box-shadow:0 0 10px #000 inset;}
    .hp-track { width: 100%; height: 12px; background: rgba(0,0,0,0.8); border-radius: 10px; overflow: hidden; border:1px inset #444; }
    .hp-fill { height: 100%; background: linear-gradient(90deg, #aa0000, #ff4040); width: 100%; transition: 0.2s cubic-bezier(0,1,1,1);}

    /* החנות */
    .shop-box {display:none; background:#181c19; padding:8px; border-radius:5px; border:1px solid #4a946b; font-size:12px; box-shadow: inset 0 0 30px rgba(46,163,89, 0.2);}
    .shop-btn { background:#304e3b; border:1px solid #2ecc71; border-radius:4px; padding:5px; width:100%; margin-top:5px; font-weight:bold; cursor:pointer; color:white; transition: 0.1s;}
    .shop-btn:active {transform:scale(0.95); background: #2ecc71;}
    .shop-btn.buy {border-color:var(--acc); background:#4d421d;}

    /* יונטס ותיוויט */
    .chest-box {display:none; background:#1f1906; border: 2px dashed #d4af37; padding:8px; border-radius:6px; color:gold;}
    
    /* RIGHT PANEL : LOG MACHINE - INHERNT LIFT FLow */
    .log-container { background: #0c0b10; border-radius: 5px; border: 1px inset #222; padding: 10px; overflow-y: auto; display:flex; flex-direction:column-reverse; gap:4px; box-shadow: -10px 0 20px rgba(0,0,0,0.3);}
    .msg { padding: 6px; border-radius: 2px; font-size: 12px; line-height: 1.5; color:#a6a1bd; border-right: 3px solid transparent; background:rgba(255,255,255,0.015);}
    .msg:first-child{ color:#fff; text-shadow:0 0 5px rgba(255,255,255,0.2);} /* מסמל פייפר להמצגת האחרונה מרווקץ קצוה. */
    .sys { text-align: right; color: #5880a6; border-right-color:#2a5075; font-style:italic;}
    .danger { color: #f28b82; border-right-color:#c5221f; background: rgba(255,0,0,0.1); }
    .success { color: #81c995; border-right-color:#1e8e3e; background: rgba(0,255,0,0.05);}
    .gold { color: #fce8b2; border-right-color:#f29900; font-weight:bold;}

    /* MODAL:  The Gear */
    .inv-modal { display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(10,5,15,0.85); z-index:99; justify-content:center; align-items:center; backdrop-filter: blur(2px);}
    .inv-box { background:var(--panel2); width:80%; padding:20px; border-radius:6px; border:2px solid var(--border); box-shadow:0 0 40px #000; display:flex; flex-direction:column; gap:10px; max-height:85vh; overflow-y:auto;}
    .use-btn { background: #23222a; color: white; font-family:'Arimo'; font-weight:bold; padding: 12px; border: 1px solid #5a546e; border-radius:4px; width: 100%; cursor: pointer; text-align:center;}
    .use-btn:active { background: #454056; }
    
    /* BOTOM BAR. BIG PAD FOR QUICK HUSLES ACTION */
    .controls { height: 165px; background: #1f1d27; border-top: 3px solid #131217; padding: 15px 10px; display: grid; grid-template-columns: 1fr 150px; gap: 20px; align-items: center;}
    
    .d-pad { direction: ltr; display: grid; grid-template-columns: repeat(3, 1fr); gap: 4px; width: 150px; margin: 0 auto; height:100%;}
    .btn-arr { background: #2f2d39; color: #b7b3ce; border:none; box-shadow: inset 0 -3px #18161d; border-radius: 6px; font-size: 20px; height: 100%; min-height:45px; cursor: pointer; display: flex; align-items: center; justify-content: center;}
    .btn-arr:active { background: #3b3947; box-shadow: none; transform:translateY(3px); }
    
    .up { grid-column: 2; grid-row: 1; }
    .down { grid-column: 2; grid-row: 2; }
    .left { grid-column: 1; grid-row: 2; }
    .right { grid-column: 3; grid-row: 2; }

    .main-actions { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; height: 100%; }
    .act-btn { height: 100%; min-height:55px; font-family:inherit; font-weight: bold; font-size: 15px; border: none; border-radius: 6px; cursor: pointer; color:#e0e0e0; transition:0.1s; letter-spacing:1px; box-shadow: inset 0 -4px rgba(0,0,0,0.5);}
    .act-btn:active{transform:translateY(3px); box-shadow:none;}
    
    .btn-atk { background: #a22929; border: 1px solid #ff4e4e; }
    .btn-take { background: #267a3a; border: 1px solid #5bff81;}
    .btn-inv { background: #886716; border:1px solid #ffc841; grid-column: span 2; min-height:45px;}

</style>
</head>
<body>

<header>
    <div class="title">TOMB SEEKER</div>
    <div style="display:flex; gap:5px; font-family:monospace;">
        <div class="stat-badge" title="בסיס יכולת סקיומיר החיתוכית">⚔️ ATK: <span id="atk">10</span></div>
        <div class="stat-badge" title="מרספיוטיות לוחותית הבזלים במלואה">❤️ HP: <span id="hp">100/100</span></div>
        <div class="stat-badge" style="color:gold;">💰 <span id="gold">0</span></div>
    </div>
</header>


<div class="viewport">
    
    <div class="side-panel">
        <div class="map-grid" id="map-target"></div>
        
        <div class="room-card">
            <div id="loc-name" style="font-weight:900; font-size:14px;">חישבובים במערות הפקר מזה קובץ משחקים טעייים..</div>
            
            <div id="floor-box" class="items-alert">
                הונחו שרבתיות ציד כאן : <span id="floor-list" style="font-weight:bold; color:white;"></span>
            </div>
            
            <!-- Context: Combat Box -->
            <div id="enemy-box" class="dynamic-interaction">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <strong id="en-name" style="color:#ff8181; font-size:14px;">דברמה קורצת</strong>
                    <div style="font-size:10px; color:#ddd; font-family:monospace;"><span id="en-hp"></span>/<span id="en-max"></span></div>
                </div>
                <div class="hp-track"><div id="en-fill" class="hp-fill"></div></div>
                <div style="font-size:11px; text-align:left; color:#999;">חייב להתמודד עם שבילת קסום. לא מזיד בצעדים</div>
            </div>
            
            <!-- Context: Shopping Window! מיוחד המותף-->
            <div id="shop-box" class="shop-box">
                <div style="color:lime; font-size:16px;">מרחב תיירים אחיסווק מטורפים : 🏪</div>
                <div style="font-style:italic; margin-bottom:10px; color:#a2cfba;">"<span id="shop-txt">סחור מול כפריים ולוז אמרגן !</span>"</div>
                <button class="shop-btn" onclick="send('sell')">💰 מחיצת הכול (הפוך עצי חמוצים לכספים ששוחיתה ברץ)!</button>
                <div style="display:grid; grid-template-columns: 1fr 1fr; gap:5px; margin-top:10px;">
                    <button class="shop-btn buy" onclick="send('buy','upg_hp')">+20 מכות מקס לב(80💰)</button>
                    <button class="shop-btn buy" onclick="send('buy','upg_atk')">+5 צילוף חיתוך(100💰)</button>
                    <button class="shop-btn buy" onclick="send('buy','buy_heal')">קסום שיקי עבות עות קח גדולים!(35💰)</button>
                    <button class="shop-btn buy" onclick="send('buy','buy_bomb')">רכידת הרמס אש מסחפי! עלי אופטרונים !(55💰)</button>
                </div>
            </div>

            <!-- Context: A chest 🔒! -->
            <div id="chest-box" class="chest-box">
                <div>תבית לורדה פצוצת נוצח מוחשב ונעול חצי כית ! 🔒💎</div>
                <button onclick="send('open_chest')" style="width:100%; margin-top:5px; background:gold; color:black; font-weight:bold; cursor:pointer; padding:6px; border:none; border-radius:3px;">הנפת מתגים פריקת עול! בחן מידת המפתח</button>
            </div>
        </div>

    </div>

    <!-- LOGGER תסרופות -->
    <div class="log-container" id="log-box"></div>
</div>

<div class="inv-modal" id="inv-modal" onclick="if(event.target==this) toggleInv()">
    <div class="inv-box">
        <h2 style="margin:0; text-align:center; color:var(--acc); border-bottom:1px solid #444; padding-bottom:10px;">תיק קציון ומערבל אסמים</h2>
        <div style="text-align:center; color:#888; font-size:13px; margin-bottom:5px;">עסקית גב בבחילה מה לשתור כהורח קפף לחתירה למפעליו דרוק.</div>
        <div id="inv-list" style="display:grid; gap:8px;"></div>
    </div>
</div>


<!-- התעופים מהקרנבת ! -->
<div class="controls">
    
    <!-- 14 לחצוב אטרפטיקה. לכו עייים אליא בום ליונס! -->
    <div class="main-actions">
        <button class="act-btn btn-atk" onclick="send('attack')">⚔️ תנוף שיתת !</button>
        <button class="act-btn btn-take" onclick="send('take')">✋ גחור עור</button>
        <button class="act-btn btn-inv" onclick="toggleInv()">🎒 מערבול כינונים חיח! ברא דומיי.</button>
    </div>

    <div class="d-pad">
        <button class="btn-arr up" onclick="send('move', [0,1])">⬆</button>
        <button class="btn-arr left" onclick="send('move', [-1,0])">⬅</button>
        <button class="btn-arr down" onclick="send('move', [0,-1])">⬇</button>
        <button class="btn-arr right" onclick="send('move', [1,0])">➡</button>
    </div>

</div>

<script>
    const API = "{{ api }}";
    
    window.onload = () => send('init');

    async function send(act, val=null) {
        if(act=='use') toggleInv(); 

        try {
            let res = await fetch(API, {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({action: act, val: val})
            });
            let d = await res.json();

            if (d.dead) { alert("דימתה כולה קרטיבי לא גחזום תחיל נתיח לחיי נבילי לוע המות מבוטלות"); send('reset'); return; }

            // L0GER   
            let logBox = document.getElementById("log-box");
            logBox.innerHTML = "";
            let latestReverse = d.log.reverse();
            latestReverse.forEach(msg => {
                logBox.innerHTML += `<div class="msg ${msg.type}">${msg.text}</div>`;
            });
            

            // Mapers
            let mapH = "";
            d.map_grid.forEach(row => {
                row.forEach(c => mapH += `<div class='map-cell ${c.cls}'>${c.val}</div>`);
            });
            document.getElementById("map-target").innerHTML = mapH;

            // BAsics Bars  !
            document.getElementById("hp").innerText = `${d.hp}/${d.max_hp}`;
            document.getElementById("gold").innerText = d.gold;
            document.getElementById("atk").innerText = d.atk;
            document.getElementById("loc-name").innerText = d.room_name;


            //  THE 3 CORE SCNEARIOS (enemy / Shop / chest / Item flooer.)! !  ===  -- 

            let eBox = document.getElementById("enemy-box");
            let sBox = document.getElementById("shop-box");
            let cBox = document.getElementById("chest-box");

            eBox.style.display = d.enemy ? "flex" : "none";
            if (d.enemy) {
                document.getElementById("en-name").innerText = d.enemy.name;
                document.getElementById("en-hp").innerText = d.enemy.hp;
                document.getElementById("en-max").innerText = d.enemy.max;
                document.getElementById("en-fill").style.width = ((d.enemy.hp / d.enemy.max)*100) + "%";
            }
            
            sBox.style.display = d.is_shop ? "block" : "none";
            if(d.is_shop) document.getElementById("shop-txt").innerText = d.shop_greet;

            cBox.style.display = d.chest ? "block" : "none";

            let fBox = document.getElementById("floor-box");
            if (d.items && d.items.length > 0) {
                fBox.style.display = "block";
                document.getElementById("floor-list").innerText = d.items.join(" ,  ");
            } else fBox.style.display = "none";

            
            //  = Inventosys List ==- 
            let invL = document.getElementById("inv-list");
            invL.innerHTML = "";
            if (d.inv.length === 0) invL.innerHTML = "<div style='color:#767; text-align:center;'>הרוחש סולקו לחצי כיזוי! המקום רייף.. חוש להחלפים משחקים . </div>";
            else {
                // Sorting! potions togs etc nice UX .
                d.inv.sort().forEach(it => {
                    invL.innerHTML += `<button class="use-btn" onclick="send('use', '${it}')">${it}</button>`;
                });
            }

        } catch(e) {}
    }

    function toggleInv() {
        let el = document.getElementById("inv-modal");
        el.style.display = (el.style.display == "flex") ? "none" : "flex";
    }
    
</script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(port=5007, debug=True)
