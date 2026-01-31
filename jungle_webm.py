import streamlit as st
import random
import pandas as pd
from datetime import date

# -----------------------------
# Jungle Environment Logic
# -----------------------------
class Jungle:
    def __init__(self):
        self.reset()

    def reset(self):
        self.lions = 5
        self.deer = 25
        self.forest = 50
        self.villagers = 12 
        self.turn = 0
        self.stable_streak = 0
        self.cumulative_score = 0
        self.game_over = False
        self.victory = False
        self.last_effects = []
        self.history = []

    def get_resource_ui(self, category, val):
        """Simple English status and icons for quick scanning."""
        if category == "lions":
            if val <= 0: return "💀", "Extinct"
            if val <= 2: return "🥀", "Low"
            return "🦁", "Healthy"
        if category == "deer":
            if val <= 0: return "🦴", "Gone"
            if val <= 10: return "🍃", "Low"
            return "🦌", "Strong"
        if category == "forest":
            if val <= 15: return "🔥", "Critical"
            if val <= 30: return "🪵", "Low"
            return "🌳", "Lush"
        if category == "village":
            if val <= 3: return "🏚️", "Dying"
            return "🏡", "Good"

    def step(self, action: str):
        if self.game_over: return
        self.turn += 1
        self.last_effects = []
        
        # --- 1. Player Action Changes ---
        if action == 'hunt_deer':
            hunted = random.randint(5, 8)
            self.deer -= hunted
            self.last_effects.append(f"🏹 Meat Secured: Hunted {hunted} deer.")
        elif action == 'hunt_lion':
            killed = random.randint(1, 2)
            self.lions = max(0, self.lions - killed)
            self.last_effects.append(f"⚔️ Lion Cull: {killed} lions removed.")
        elif action == 'expand_village':
            # Expansion Decay: Costs more forest if land is already thin
            cost = 15 if self.forest < 30 else 10
            gain = random.randint(3, 5)
            self.forest -= cost
            self.villagers += gain
            self.last_effects.append(f"🏗️ Growth: +{gain} people, -{cost} forest.")
        elif action == 'protect_forest':
            # Labor Decay: Bigger villages need more people for patrol
            labor = 1 + (self.villagers // 15)
            self.villagers = max(1, self.villagers - labor)
            regen = random.randint(10, 15)
            self.forest = min(100, self.forest + regen)
            self.last_effects.append(f"🛡️ Patrols: +{regen} forest (Labor: -{labor}).")

        # --- 2. Ecological Decay Logic (Simple English) ---
        # [Decay] The Lion Rule: Lions control deer population. 
        if self.lions == 0 and self.deer > 5:
            decay = random.randint(2, 4)
            self.forest -= decay
            self.last_effects.append(f"🍂 Overgrazing: No lions! Deer ate {decay} forest.")

        # [Growth] Space to Grow: Deer need forest space.
        cap = self.forest * 0.75
        growth = max(1, int(self.deer * 0.20 * (1 - (self.deer / max(1, cap)))))
        self.deer += growth
        
        # [Decay] Hunger: People and Lions eat Deer.
        eaten_by_lions = min(int(self.lions * self.deer * 0.035), self.deer)
        self.deer -= eaten_by_lions
        
        demand = int(self.villagers * 0.5)
        if self.deer < demand:
            lost = max(1, int((demand - self.deer) * 0.6))
            self.villagers -= lost
            self.deer = 0
            self.last_effects.append(f"🥣 Famine: {lost} people died.")
        else:
            self.deer -= demand

        # [Decay] Lion Starvation: Lions die if they find no deer.
        if self.lions > 0 and (eaten_by_lions / self.lions) < 1.0: 
            self.lions -= 1
            self.last_effects.append("💀 Hunger: A lion died.")

        # --- 3. Wrap Up ---
        self.history.append({"Turn": self.turn, "Lions": self.lions, "Deer": self.deer, "Forest": self.forest})
        self.cumulative_score += int(self.lions * 15 + self.deer * 1 + self.villagers * 5 + self.forest * 1)
        self.deer, self.lions, self.forest = max(0, self.deer), max(0, self.lions), max(0, self.forest)
        
        ratio = self.lions / max(1, self.deer)
        if 0.15 <= ratio <= 0.35: self.stable_streak += 1
        else: self.stable_streak = 0

        if self.stable_streak >= 15: self.game_over, self.victory = True, True
        elif any(v <= 0 for v in [self.villagers, self.deer, self.forest]): self.game_over = True

# -----------------------------
# Mobile Optimized UI
# -----------------------------
st.set_page_config(page_title="Lion Warden", layout="centered")

if 'j' not in st.session_state: st.session_state.j = Jungle()
j = st.session_state.j

# Compact Header
st.title("🦁 Lion King Warden")
col_score1, col_score2 = st.columns(2)
col_score1.write(f"**Year:** {j.turn}")
col_score2.write(f"**Score:** {j.cumulative_score}")

with st.expander("📖 Rules & Biology"):
    st.write("1. **Lions 🦁:** Hunt deer. No lions = Deer kill the forest.")
    st.write("2. **Deer 🦌:** Food for all. They need forest to grow.")
    st.write("3. **Balance ⚖️:** Keep a 1:5 ratio of Lions to Deer for 15 years.")
    

st.divider()

# Resource Dashboard - 2x2 Grid for Mobile Visibility
r1_c1, r1_c2 = st.columns(2)
l_icon, l_msg = j.get_resource_ui("lions", j.lions)
d_icon, d_msg = j.get_resource_ui("deer", j.deer)
r1_c1.metric(f"{l_icon} Lions", j.lions, l_msg)
r1_c2.metric(f"{d_icon} Deer", j.deer, d_msg)

r2_c1, r2_c2 = st.columns(2)
f_icon, f_msg = j.get_resource_ui("forest", j.forest)
v_icon, v_msg = j.get_resource_ui("village", j.villagers)
r2_c1.metric(f"{f_icon} Forest", j.forest, f_msg)
r2_c2.metric(f"{v_icon} Village", j.villagers, v_msg)

st.write(f"**Stability Progress ({j.stable_streak}/15)**")
st.progress(j.stable_streak / 15)

if j.game_over:
    if j.victory: st.success(f"🏆 VICTORY! Final Score: {j.cumulative_score}")
    else: st.error(f"❌ COLLAPSE! Nature failed.")
    st.button("🔄 Restart Game", on_click=j.reset, type="primary", use_container_width=True)
else:
    # Action Selection
    action = st.selectbox("Select Action:", ["Hunt Deer", "Hunt Lion", "Expand Village", "Protect Forest"])
    
    guidance = {
        "Hunt Deer": "🏹 Gain food, but don't starve the Lions.",
        "Hunt Lion": "⚔️ Control predators, but protect the Forest.",
        "Expand Village": "🏗️ Grow the tribe at a Forest cost.",
        "Protect Forest": "🛡️ Restore land using Village labor."
    }
    st.info(guidance[action])

    # Big Mobile-Friendly Button
    if st.button("EXECUTE YEAR", type="primary", use_container_width=True):
        j.step(action.lower().replace(" ", "_"))
        st.rerun()

    # Feedback container
    if j.last_effects:
        with st.container(border=True):
            for e in j.last_effects: st.markdown(f"**{e}**")

# Population Chart
if j.history:
    with st.expander("📈 Nature Trends"):
        st.line_chart(pd.DataFrame(j.history).set_index("Turn"))
