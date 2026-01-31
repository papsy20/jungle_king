import streamlit as st
import random
from datetime import date

# -----------------------------
# Jungle Environment Logic
# -----------------------------
class Jungle:
    def __init__(self):
        self.reset()

    def reset(self):
        # Parameters tuned for a Turn 12-16 Climax
        self.tigers = 5
        self.deer = 25
        self.forest = 50
        self.villagers = 12 
        self.turn = 0
        self.stable_streak = 0
        self.cumulative_score = 0
        self.game_over = False
        self.victory = False
        self.last_effects = {"player": {}, "nature": {}}

    def get_stability(self):
        if self.deer <= 0: return 0, "Extinct", "red"
        ratio = self.tigers / self.deer
        if 0.15 <= ratio <= 0.35: return 100, "Stable ✅", "green"
        return 40, "Unstable ⚠️", "orange"

    def get_preview(self, action):
        previews = {
            "hunt_deer": "🏹 Deer -6 | 🥘 Village Fed",
            "hunt_tiger": "⚔️ Tigers -2 | 🦌 Deer Safety Up",
            "expand_village": "🏗️ Forest -12 | 👥 Villagers +4",
            "protect_forest": "🛡️ Villagers -2 | 🌱 Forest +10"
        }
        return previews.get(action, "")

    def step(self, action: str):
        if self.game_over: return
        self.turn += 1
        p_eff, n_eff = {} , {}
        
        # --- 1. Player Actions ---
        if action == 'hunt_deer':
            self.deer -= 6
            p_eff['Deer Hunted'] = -6
        elif action == 'hunt_tiger':
            self.tigers = max(0, self.tigers - 2)
            p_eff['Tigers Culled'] = -2
        elif action == 'expand_village':
            self.forest -= 12
            self.villagers += 4
            p_eff['Habitat Lost'] = -12
        elif action == 'protect_forest':
            self.villagers = max(1, self.villagers - 2)
            self.forest = min(100, self.forest + 10)
            p_eff['Village Labor Cost'] = -2

        # --- 2. Nature's Logic (The Decay/Growth Math) ---
        
        # Forest Limits: The forest can only support a certain amount of deer.
        cap = self.forest * 0.75
        
        # Deer Growth: Deer naturally increase by 20% each year, but stop if they run out of forest space.
        growth = int(self.deer * 0.20 * (1 - (self.deer / max(1, cap))))
        self.deer += max(1, growth)
        n_eff['Deer Births'] = max(1, growth)
        
        # Tiger Hunger: Tigers eat 2.5% of the deer population.
        eaten = min(int(self.tigers * self.deer * 0.025), self.deer)
        self.deer -= eaten
        n_eff['Deer Eaten by Tigers'] = -eaten

        # Village Hunger: Every 2 villagers need 1 deer per turn.
        demand = int(self.villagers * 0.5)
        if self.deer < demand:
            # Famine: If there isn't enough food, 60% of the hungry people perish.
            lost = max(1, int((demand - self.deer) * 0.6))
            self.villagers -= lost
            self.deer = 0
            n_eff['Famine Deaths'] = -lost
        else:
            self.deer -= demand
            n_eff['Deer Eaten by Village'] = -demand

        # Tiger Survival: If a tiger doesn't catch at least 1 deer, it starves.
        eff = eaten / max(1, self.tigers) if self.tigers > 0 else 0
        if self.tigers > 0 and eff < 1.0: 
            self.tigers -= 1
            n_eff['Tiger Starved'] = -1

        # --- 3. Wrap Up ---
        self.last_effects = {"player": p_eff, "nature": n_eff}
        self.cumulative_score += int(self.tigers * 5 + self.deer * 1 + self.villagers * 3)
        self.deer, self.tigers, self.forest = max(0, self.deer), max(0, self.tigers), max(0, self.forest)
        
        perc, status, _ = self.get_stability()
        self.stable_streak = self.stable_streak + 1 if status == "Stable ✅" else 0

        if self.stable_streak >= 15: 
            self.game_over, self.victory = True, True
        elif any(v <= 0 for v in [self.villagers, self.deer, self.forest]): 
            self.game_over = True

# -----------------------------
# Mobile UI 
# -----------------------------
st.set_page_config(page_title="Jungle King", layout="centered")

if 'j' not in st.session_state: st.session_state.j = Jungle()
if 'high_score' not in st.session_state: st.session_state.high_score = 0
j = st.session_state.j

st.title("🦁 Jungle King")
st.caption(f"v1.1 | Author: Papsy | {date.today().strftime('%Y-%m-%d')}")
st.write(f"🏆 Best Score: `{st.session_state.high_score}`")

m1, m2 = st.columns(2)
m1.metric("🐅 Tigers", j.tigers)
m2.metric("🦌 Deer", j.deer)
m3, m4 = st.columns(2)
m3.metric("🌳 Forest", j.forest)
m4.metric("👥 Village", j.villagers)

perc, status, color = j.get_stability()
st.write(f"**{status}** (Streak: {j.stable_streak}/15)")
st.progress(perc / 100)

st.divider()

if j.game_over:
    if j.cumulative_score > st.session_state.high_score:
        st.session_state.high_score = j.cumulative_score
    if getattr(j, 'victory', False): st.success("🏆 VICTORY! You saved the Jungle.")
    else: st.error("❌ COLLAPSE! Nature has failed.")
    st.button("🔄 Try Again", on_click=j.reset, type="primary", use_container_width=True)
else:
    action = st.selectbox("Your Move:", ["Hunt Deer", "Hunt Tigers", "Expand Village", "Protect Forest"])
    key = action.lower().replace(" ", "_")
    st.info(f"**Impact:** {j.get_preview(key)}")
    if st.button(f"Confirm Action", type="primary", use_container_width=True):
        j.step(key)
        st.rerun()

with st.expander("📊 Turn Insights"):
    if j.last_effects['player']:
        st.write("**Human Impact:**")
        for k, v in j.last_effects['player'].items(): st.write(f"🔹 {k}: {v}")
        st.write("**Nature's Response:**")
        for k, v in j.last_effects['nature'].items(): st.write(f"🍃 {k}: {v}")

with st.expander("📖 Nature's Rules"):
    st.write("""
    1. **Deer Growth**: Deer increase by 20% yearly, but they need Forest to live. If the Forest is small, Deer stop born.
    2. **Predation**: Tigers eat roughly 2.5% of the Deer every turn.
    3. **Starvation**: If a Tiger can't find at least 1 Deer to eat, it will die.
    4. **Famine**: Every 2 Villagers need 1 Deer. If the Deer are gone, 60% of your people will perish.
    """)

st.caption(f"Year: {j.turn} | Score: {j.cumulative_score}")
