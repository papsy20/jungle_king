import streamlit as st
import random
import pandas as pd

# -----------------------------
# THE GAME ENGINE
# -----------------------------
class JungleKing:
    def __init__(self):
        self.reset()

    def reset(self):
        # v3.1 "Goldilocks" Starting Parameters
        self.lions = 5
        self.deer = 55
        self.forest = 80
        self.villagers = 10
        self.turn = 0
        self.stable_streak = 0
        self.cumulative_score = 0
        self.game_over = False
        self.victory = False
        self.last_news = []
        self.history = []

    def get_status_ui(self, category, val):
        if category == "lions":
            if val <= 0: return "💀", "Extinct"
            return "🦁", "Healthy"
        if category == "deer":
            if val <= 0: return "🦴", "Gone"
            return "🦌", "Thriving"
        if category == "forest":
            if val <= 20: return "🔥", "Critical"
            return "🌳", "Lush"
        return "🏡", "Good"

    def step(self, action: str):
        if self.game_over: return
        self.turn += 1
        self.last_news = []

        # 1. Weighted Difficulty Logic
        # Decay parameters start scaling up after Year 25 to ensure difficulty by Year 35.
        diff_weight = 1.0
        if self.turn > 25:
            # Increases decay by 7% per year after turn 25
            diff_weight = 1.0 + ((self.turn - 25) * 0.07)

        # 2. Player Commands (Planned Change)
        if action == 'hunt_deer':
            hunted = random.randint(4, 6)
            self.deer -= hunted
            self.last_news.append(f"🏹 Meat: The hunters brought back {hunted} deer.")
        elif action == 'hunt_lion':
            self.lions = max(0, self.lions - 1)
            self.last_news.append("⚔️ Cull: A lion was chased into the far hills.")
        elif action == 'expand_village':
            # Weighted Decay: Forest cost increases over time
            cost = 8 * diff_weight
            gain = random.randint(2, 4)
            self.forest -= cost
            self.villagers += gain
            self.last_news.append(f"🏗️ Growth: +{gain} people, but -{cost:.1f} forest.")
        elif action == 'protect_forest':
            regen = random.randint(15, 20)
            self.forest = min(100, self.forest + regen)
            self.last_news.append(f"🌱 Care: The village restored {regen} forest.")

        # 3. Nature & Weighted Decay Parameters
        # Change: Deer Births (High fertility keeps 12-16 median stable)
        cap = self.forest * 1.1
        growth_rate = 0.26
        babies = int(self.deer * growth_rate * (1 - (self.deer / max(1, cap))))
        self.deer += max(4, babies)

        # Change: Predation (Lions hunt)
        eaten_by_lions = min(self.lions, self.deer)
        self.deer -= eaten_by_lions

        # Decay: Human Hunger (Weighted Difficulty)
        food_needed = max(1, int((self.villagers // 4) * diff_weight))
        if self.deer < food_needed:
            lost = 1
            self.villagers = max(0, self.villagers - lost)
            self.deer = 0
            self.last_news.append(f"🥣 Famine: {lost} person left the village.")
        else:
            self.deer -= food_needed

        # Decay: Lion Starvation (Weighted Difficulty)
        lion_threshold = 0.6 * diff_weight
        if self.lions > 0 and (eaten_by_lions / self.lions) < lion_threshold:
            self.lions -= 1
            self.last_news.append("💀 Hunger: A lion left because prey was too scarce.")

        # Decay: Overgrazing (Only if lions are gone)
        if self.lions <= 0:
            self.forest -= (1.5 * diff_weight)

        # 4. Wrap Up Logic
        self.cumulative_score += int(self.lions * 15 + self.villagers * 8 + self.deer + self.forest)
        self.history.append({"Year": self.turn, "Lions": self.lions, "Deer": self.deer, "Forest": self.forest})

        # Balance Window for Win Condition
        ratio = self.lions / max(1, self.deer)
        if 0.12 <= ratio <= 0.42:
            self.stable_streak += 1
        else:
            self.stable_streak = 0

        # Victory/Loss Checks
        if self.stable_streak >= 15:
            self.game_over, self.victory = True, True
        elif any(v <= 0 for v in [self.villagers, self.deer, self.forest]):
            self.game_over = True

# -----------------------------
# THE DISPLAY (STREAMLIT UI)
# -----------------------------
st.set_page_config(page_title="Jungle King", layout="centered")

if 'game' not in st.session_state:
    st.session_state.game = JungleKing()
jk = st.session_state.game

st.title("🦁 Jungle King")
st.write(f"📅 **Year:** {jk.turn} | 🏆 **Score:** {jk.cumulative_score}")

# Resource Dashboard
m1, m2, m3, m4 = st.columns(4)
l_ico, l_msg = jk.get_status_ui("lions", jk.lions)
d_ico, d_msg = jk.get_status_ui("deer", jk.deer)
f_ico, f_msg = jk.get_status_ui("forest", jk.forest)

m1.metric(f"{l_ico} Lions", jk.lions, l_msg)
m2.metric(f"{d_ico} Deer", jk.deer, d_msg)
m3.metric(f"{f_ico} Forest", int(jk.forest), f_msg)
m4.metric("🏡 People", jk.villagers)

# Peace Meter
st.write(f"**Peace Meter ({jk.stable_streak}/15 Years)**")
st.progress(jk.stable_streak / 15)

if jk.game_over:
    if jk.victory:
        st.success(f"👑 VICTORY! Your reign achieved perfect balance. Final Score: {jk.cumulative_score}")
    else:
        st.error(f"💀 THE FALL: Your kingdom has collapsed. Final Score: {jk.cumulative_score}")
    st.button("🔄 Start New Reign", on_click=jk.reset, use_container_width=True)
else:
    # Village Elder Jovial Commentary
    choice = st.selectbox("Command:", ["Hunt Deer", "Hunt Lions", "Expand Village", "Protect Forest"])
    
    advice = {
        "Hunt Deer": "🏹 'The pots are low, but don't take so many that the lions look at us instead!'" ,
        "Hunt Lions": "⚔️ 'The big cats are numerous. A little culling keeps the village safe.'",
        "Expand Village": "🏗️ 'More neighbors means more glory, though the trees might grumble.'",
        "Protect Forest": "🛡️ 'Water the saplings, King! A lush forest is the mother of all deer.'"
    }
    st.info(advice[choice])

    if st.button("EXECUTE ORDER", type="primary", use_container_width=True):
        jk.step(choice.lower().replace(" ", "_").replace("lions", "lion"))
        st.rerun()

    # Event Feed
    if jk.last_news:
        with st.container(border=True):
            for news in jk.last_news:
                st.write(f"• {news}")

# Historical Trends
if jk.history:
    with st.expander("📈 Jungle Trends"):
        st.line_chart(pd.DataFrame(jk.history).set_index("Year"))
