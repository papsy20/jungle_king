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
        self.history = ["Stewardship started. Win by hitting 20 stable years!"]
        self.last_effects = {"player": {}, "nature": {}}

    def get_stability(self):
        if self.deer <= 0: return 0, "Extinct", "red"
        ratio = self.tigers / self.deer
        if 0.1 <= ratio <= 0.3: return 100, "Stable ✅", "green"
        return 40, "Unbalanced ⚠️", "orange"

    def get_preview(self, action):
        previews = {
            "hunt_deer": "🏹 Deer -5 | 👥 Village Fed",
            "hunt_tiger": "⚔️ Tigers -2 | 🦌 Deer Safer",
            "expand_village": "🏗️ Forest -10 | 👥 Villagers +3",
            "protect_forest": "🛡️ Villagers -1 | 🌱 Forest +8"
        }
        return previews.get(action, "")

    def step(self, action: str):
        if self.game_over: return
        self.turn += 1
        p_eff, n_eff = {}, {}
        
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
        elif action == 'protect_forest':
            self.villagers = max(1, self.villagers - 1)
            self.forest = min(100, self.forest + 8)

        cap = self.forest * 0.8
        growth = int(self.deer * 0.25 * (1 - (self.deer / max(1, cap))))
        self.deer += max(1, growth)
        n_eff['Deer Births'] = max(1, growth)

        eaten = min(int(self.tigers * self.deer * 0.02), self.deer)
        self.deer -= eaten
        n_eff['Predation'] = -eaten

        demand = int(self.villagers * 0.5)
        if self.deer < demand:
            lost = max(1, int((demand - self.deer) * 0.5))
            self.villagers -= lost
            self.deer = 0
            n_eff['Famine'] = -lost
        else:
            self.deer -= demand

        eff = eaten / max(1, self.tigers) if self.tigers > 0 else 0
        if self.tigers > 0 and eff < 0.8:
            loss = max(1, int(self.tigers * 0.2))
            self.tigers -= loss
            n_eff['Starved'] = -loss
        elif self.tigers > 0 and eff > 1.3:
            self.tigers += 1
            n_eff['New Cubs'] = 1

        self.last_effects = {"player": p_eff, "nature": n_eff}
        self.cumulative_score += int(self.tigers * 3 + self.deer * 0.5 + self.villagers * 2)
        self.deer, self.tigers, self.forest = max(0, self.deer), max(0, self.tigers), max(0, self.forest)
        
        perc, status, _ = self.get_stability()
        self.stable_streak = self.stable_streak + 1 if status == "Stable ✅" else 0

        if self.stable_streak >= 20: self.game_over, self.victory = True, True
        elif any(v <= 0 for v in [self.villagers, self.deer, self.forest]): self.game_over = True

# -----------------------------
# Mobile-First UI
# -----------------------------
st.set_page_config(page_title="Jungle King", layout="centered")

if 'j' not in st.session_state: st.session_state.j = Jungle()
if 'high_score' not in st.session_state: st.session_state.high_score = 0
j = st.session_state.j

# Compact Header
st.title("🦁 Jungle King")
st.caption(f"v1.0 | Papsy | {date.today().strftime('%Y-%m-%d')}")

# High Score Display (Minimalist)
st.write(f"🏆 High Score: `{st.session_state.high_score}`")

# 1. Vital Stats Grid (Works well on mobile)
m1, m2 = st.columns(2)
m1.metric("🐅 Tigers", j.tigers)
m2.metric("🦌 Deer", j.deer)
m3, m4 = st.columns(2)
m3.metric("🌳 Forest", j.forest)
m4.metric("👥 Village", j.villagers)

# 2. Stability Tracker
perc, status, color = j.get_stability()
st.write(f"**{status}** (Streak: {j.stable_streak}/20)")
st.progress(perc / 100)

st.divider()

if j.game_over:
    if j.cumulative_score > st.session_state.high_score:
        st.session_state.high_score = j.cumulative_score
    
    if getattr(j, 'victory', False):
        st.success("🏆 VICTORY! You are the King.")
    else:
        st.error("❌ GAME OVER")
    
    st.button("🔄 Play Again", on_click=j.reset, type="primary", use_container_width=True)
else:
    # 3. Mobile Decision Center
    st.subheader("🧭 Next Move")
    action = st.selectbox("Action:", ["Hunt Deer", "Hunt Tigers", "Expand Village", "Protect Forest"])
    key = action.lower().replace(" ", "_")
    
    # Impact Preview (Condensed for Mobile)
    st.info(f"**Impact:** {j.get_preview(key)}")
            
    if st.button(f"Confirm {action}", type="primary", use_container_width=True):
        j.step(key)
        st.rerun()

    # 4. Feedback Logs (Tucked away in expander for mobile)
    with st.expander("📋 Last Turn Feedback"):
        if j.last_effects['player'] or j.last_effects['nature']:
            for k, v in j.last_effects['player'].items(): st.write(f"🔹 {k}: {v}")
            for k, v in j.last_effects['nature'].items(): st.write(f"🍃 {k}: {v}")
        else:
            st.write("Start your first turn!")

st.divider()
with st.expander("📖 Guide"):
    st.write("Maintain Tiger-to-Deer ratio (1:10 to 3:10).")
    
    

st.caption(f"Year: {j.turn} | Score: {j.cumulative_score}")