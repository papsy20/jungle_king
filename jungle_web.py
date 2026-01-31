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
        self.tigers = 6
        self.deer = 30
        self.forest = 60
        self.villagers = 10
        self.turn = 0
        self.stable_streak = 0
        self.cumulative_score = 0
        self.game_over = False
        self.victory = False
        self.history = ["Stewardship started. Balance the ecosystem for 20 years to win!"]
        self.last_effects = {"player": {}, "nature": {}}

    def get_stability(self):
        if self.deer <= 0: return 0, "Extinct", "red"
        ratio = self.tigers / self.deer
        if 0.1 <= ratio <= 0.3: return 100, "Stable ✅", "green"
        return 40, "Unbalanced ⚠️", "orange"

    def get_preview(self, action):
        previews = {
            "hunt_deer": "🏹 Deer: -5 | 👥 Village: Fed\n*Provides immediate food, but hungry Tigers may target villagers.*",
            "hunt_tiger": "⚔️ Tigers: -2 | 🦌 Deer: Safer\n*Reduces predation, but risks a Trophic Cascade.*",
            "expand_village": "🏗️ Forest: -10 | 👥 Villagers: +3\n*Fast growth, but permanently lowers the Jungle's capacity.*",
            "protect_forest": "🛡️ Villagers: -1 | 🌱 Forest: +8\n*Sacrifice labor to restore the habitat foundation.*"
        }
        return previews.get(action, "")

    def step(self, action: str):
        if self.game_over: return
        self.turn += 1
        p_eff, n_eff = {}, {}
        
        # --- 1. Player Action Phase ---
        if action == 'hunt_deer':
            self.deer -= 5
            p_eff['Deer Hunted'] = -5
        elif action == 'hunt_tiger':
            killed = max(1, int(0.2 * self.tigers))
            self.tigers -= killed
            p_eff['Tigers Culled'] = -killed
        elif action == 'expand_village':
            self.forest -= 10
            self.villagers += 3
            p_eff['Forest Cleared'] = -10
            p_eff['New Villagers'] = 3
        elif action == 'protect_forest':
            self.villagers = max(1, self.villagers - 1)
            self.forest = min(100, self.forest + 8)
            p_eff['Labor Sacrificed'] = -1
            p_eff['Forest Restored'] = 8

        # --- 2. Natural Dynamics ---
        cap = self.forest * 0.8
        growth = int(self.deer * 0.25 * (1 - (self.deer / max(1, cap))))
        self.deer += max(1, growth)
        n_eff['Deer Births'] = max(1, growth)

        eaten = min(int(self.tigers * self.deer * 0.02), self.deer)
        self.deer -= eaten
        n_eff['Predation Loss'] = -eaten

        demand = int(self.villagers * 0.5)
        if self.deer < demand:
            lost = max(1, int((demand - self.deer) * 0.5))
            self.villagers -= lost
            self.deer = 0
            n_eff['Famine Deaths'] = -lost
        else:
            self.deer -= demand
            n_eff['Deer Consumed'] = -demand

        eff = eaten / max(1, self.tigers) if self.tigers > 0 else 0
        if self.tigers > 0 and eff < 0.8:
            loss = max(1, int(self.tigers * 0.2))
            self.tigers -= loss
            n_eff['Tigers Starved'] = -loss
        elif self.tigers > 0 and eff > 1.3:
            self.tigers += 1
            n_eff['Tiger Cubs'] = 1

        # --- 3. Wrap Up ---
        self.last_effects = {"player": p_eff, "nature": n_eff}
        self.cumulative_score += int(self.tigers * 3 + self.deer * 0.5 + self.villagers * 2)
        self.deer, self.tigers, self.forest = max(0, self.deer), max(0, self.tigers), max(0, self.forest)
        
        perc, status, _ = self.get_stability()
        self.stable_streak = self.stable_streak + 1 if status == "Stable ✅" else 0

        if self.stable_streak >= 20:
            self.game_over, self.victory = True, True
        elif any(v <= 0 for v in [self.villagers, self.deer, self.forest]):
            self.game_over = True

# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(page_title="Jungle King", layout="centered")

# Initialize Session States
if 'j' not in st.session_state:
    st.session_state.j = Jungle()
if 'high_score' not in st.session_state:
    st.session_state.high_score = 0

j = st.session_state.j

# Header Section
head1, head2 = st.columns([3, 1])
with head1:
    st.title("🦁 Jungle King")
    st.caption(f"**Author:** Papsy | **Version:** 1.0 | **Date:** {date.today().strftime('%B %d, %Y')}")
with head2:
    st.metric("🏆 High Score", st.session_state.high_score)

st.divider()

# Dashboard
m1, m2, m3, m4 = st.columns(4)
m1.metric("🐅 Tigers", j.tigers)
m2.metric("🦌 Deer", j.deer)
m3.metric("🌳 Forest", j.forest)
m4.metric("👥 Villagers", j.villagers)

# Stability Tracking
perc, status, color = j.get_stability()
st.write(f"**Stability Status:** {status} | **Stable Streak:** {j.stable_streak}/20")
st.progress(perc / 100)

st.divider()

if j.game_over:
    # Update High Score
    if j.cumulative_score > st.session_state.high_score:
        st.session_state.high_score = j.cumulative_score
        st.success("🔥 NEW PERSONAL BEST!")

    if getattr(j, 'victory', False):
        st.balloons()
        st.success("🏆 LEGACY VICTORY: You stabilized the jungle for 20 years! You are the true Jungle King.")
    else:
        st.error("❌ COLLAPSE: The jungle has fallen out of balance.")
    
    st.metric("Final Score", j.cumulative_score)
    if st.button("🔄 Restart Game", type="primary"):
        st.session_state.j = Jungle()
        st.rerun()
else:
    # Interface
    col_act, col_log = st.columns([1, 1])
    
    with col_act:
        st.subheader("🧭 Action Center")
        action = st.radio("Choose Move:", ["Hunt Deer", "Hunt Tigers", "Expand Village", "Protect Forest"])
        key = action.lower().replace(" ", "_")
        
        with st.container(border=True):
            st.caption("Strategic Impact Preview:")
            st.info(j.get_preview(key))
            
        if st.button(f"Confirm {action}", type="primary", use_container_width=True):
            j.step(key)
            st.rerun()

    with col_log:
        st.subheader("📋 Turn Analysis")
        if j.last_effects['player'] or j.last_effects['nature']:
            st.markdown("**Last Year's Impacts:**")
            for k, v in j.last_effects['player'].items(): st.write(f"🔹 {k}: {v}")
            for k, v in j.last_effects['nature'].items(): st.write(f"🍃 {k}: {v}")
        else:
            st.write("Take an action to begin the simulation.")

st.divider()
with st.expander("📖 Jungle King's Handbook"):
    st.write("Understand the mechanics to survive:")
    
    st.markdown("**1. Trophic Cascades**")
    st.write("Removing too many predators leads to 'Overpopulation' where deer destroy the forest vegetation, eventually killing the entire ecosystem.")
    
    
    st.markdown("**2. Predator-Prey Balance**")
    st.write("Population levels naturally fluctuate in waves. Aim for a ratio where tigers have enough food without depleting the herd to extinction.")
    
    
st.caption(f"Years of Stewardship: {j.turn} | Total Score: {j.cumulative_score}")