import streamlit as st
import pandas as pd
import random
import os

# -----------------------------
# THE ENGINE (Ecological Logic)
# -----------------------------
class JungleKing:
    def __init__(self, difficulty="Medium"):
        self.difficulty = difficulty
        self.reset()

    def reset(self):
        self.lions, self.deer, self.forest, self.villagers = 5, 55, 80, 10
        self.turn, self.stable_streak = 0, 0
        self.game_over, self.victory = False, False
        self.history = []
        self.prev_forest_cap = 80 * 1.1
        self.failure_reason = ""

        # Recalibrated Math Parameters
        diff_settings = {
            "Low":    {"growth": 0.16, "weight_start": 8,  "ramp": 0.28, "win_target": 25},
            "Medium": {"growth": 0.24, "weight_start": 12, "ramp": 0.22, "win_target": 18},
            "High":   {"growth": 0.30, "weight_start": 10, "ramp": 0.30, "win_target": 15}
        }
        self.cfg = diff_settings[self.difficulty]

    def get_difficulty_weight(self):
        return 1.0 + (max(0, self.turn - self.cfg["weight_start"]) * self.cfg["ramp"])

    def calculate_mechanics(self, action, l, d, f, v, w, prev_cap):
        # 1. Action Impact (Change Parameters)
        if action == 'hunt_deer': d -= 5; f -= (1.0 * w)
        elif action == 'hunt_lion': l = max(0, l - 1); f -= (1.5 * w)
        elif action == 'expand_village': f -= (12 * w); v += 3
        elif action == 'protect_forest':
            regen = max(3, int(((100 - f) * 0.25) / (1 + (d/200)) / w))
            f = min(100, f + regen)

        # 2. Births & Predation (Change & Decay)
        boom_factor = random.uniform(0.9, 1.2)
        births = max(2, int(d * (self.cfg["growth"] / w) * (1 - (d / max(1, prev_cap))) * boom_factor))
        d += births
        
        eaten = min(round(l * random.uniform(0.8, 1.2)), d)
        d -= eaten

        # 3. Hunger & Death (Decay Parameters)
        food_needed = max(1, int((v // 4) * w))
        if d < food_needed: v = max(0, v - max(1, int(v * 0.12 * w))); d = 0
        else: d -= food_needed

        if l > 0 and (eaten / max(1, l)) < (0.5 * w): l = max(0, l - 1)

        # 4. Collapse (Trophic Decay)
        current_cap = f * 1.1
        if l <= 0: f = max(0, f - (2.5 * w)) 
        if d > current_cap: f = max(0, f - min(8.0, ((d - current_cap) / 10) * 0.5 * w))

        return l, d, f, v, births, eaten, 0, current_cap

    def step(self, action):
        if self.game_over: return
        self.turn += 1
        w = self.get_difficulty_weight()
        self.lions, self.deer, self.forest, self.villagers, _, _, _, new_cap = \
            self.calculate_mechanics(action, self.lions, self.deer, self.forest, self.villagers, w, self.prev_forest_cap)
        self.prev_forest_cap = new_cap
        self.history.append({"Season": self.turn, "L": self.lions, "D": self.deer, "F": self.forest, "V": self.villagers})
        
        ratio = self.lions / max(1, self.deer)
        if 0.12 <= ratio <= 0.42: self.stable_streak += 1
        else: self.stable_streak = 0

        if self.stable_streak >= self.cfg["win_target"]: self.game_over, self.victory = True, True
        elif self.villagers <= 0 or self.deer <= 0 or self.forest <= 0 or self.turn >= 60:
            self.failure_reason = "The circle of life has broken."
            self.game_over = True

# -----------------------------
# UI HELPERS
# -----------------------------
def get_status_emojis(l, d, f, v, cap):
    l_emo = "🦁" if l > 3 else "😿" if l > 0 else "💀"
    d_emo = "🦌" if d < cap else "😰🦌"
    f_emo = "🌳" if f > 60 else "🍂" if f > 20 else "🏜️"
    v_emo = "🏰" if v > 10 else "🛖"
    return l_emo, d_emo, f_emo, v_emo

# -----------------------------
# MAIN UI
# -----------------------------
st.set_page_config(page_title="Jungle King", layout="centered")
if 'game' not in st.session_state: st.session_state.game = JungleKing("Medium")
jk = st.session_state.game

# Atmosphere logic
ratio = jk.lions / max(1, jk.deer)
is_harmonious = 0.12 <= ratio <= 0.42
bg_color = "#f0f2f6" if is_harmonious else "#fbe9e7"
if jk.forest < 30: bg_color = "#e6e1d3"
st.markdown(f"<style>.stApp {{ background-color: {bg_color}; transition: background-color 2s; }}</style>", unsafe_allow_html=True)

st.title("🦁 Jungle King")

# THE ELDER'S LAWS (Persona Based)
with st.expander("👴 *'Listen closely to the Laws of the Valley...'*", expanded=(jk.turn == 0)):
    st.info(f"""
    1. **The Goal:** Reach a streak of **{jk.cfg['win_target']} seasons** where the Ratio is balanced.
    2. **The Balance:** Keep the Ratio (Lions/Deer) between **0.12 and 0.42**.
    3. **The Spring Echo (Change):** The forest determines the deer births, but the effect is felt one season later.
    4. **The Winter Weight (Decay):** As time passes, hunger and overgrazing become **{jk.cfg['ramp']}x** heavier each year.
    5. **The Missing Keystone:** Without Lions, the very ground will rot away.
    """)

if jk.turn == 0:
    jk.difficulty = st.select_slider("👴 *'How heavy shall the crown be?'*", options=["Low", "Medium", "High"], value=jk.difficulty)
    jk.reset()

# Sidebar
with st.sidebar:
    st.header("📜 High King's Library")
    if st.button("New Era"): jk.reset(); st.rerun()
    if jk.history: st.table(pd.DataFrame(jk.history).tail(3))

# Metrics
l_e, d_e, f_e, v_e = get_status_emojis(jk.lions, jk.deer, jk.forest, jk.villagers, jk.prev_forest_cap)
c1, c2, c3, c4 = st.columns(4)
c1.metric(f"{l_e} Lions", jk.lions)
c2.metric(f"{d_e} Deer", jk.deer)
c3.metric(f"{f_e} Forest", f"{jk.forest:.0f}%")
c4.metric(f"{v_e} Folk", jk.villagers)

st.divider()

if not jk.game_over:
    st.subheader(f"{'⚖️ Harmony' if is_harmonious else '🌪️ Chaos'} | Streak: {jk.stable_streak}/{jk.cfg['win_target']}")
    st.progress(min(1.0, jk.stable_streak / jk.cfg['win_target']))

    action = st.radio("👴 *'Which Decree shall be read?'*", ["Hunt Deer", "Hunt Lions", "Expand Village", "Protect Forest"], horizontal=True)

    # Forecast (Vision)
    w = jk.get_difficulty_weight()
    f_l, f_d, f_f, f_v, _, _, _, _ = jk.calculate_mechanics(action.lower().replace(" ", "_").replace("lions","lion"), jk.lions, jk.deer, jk.forest, jk.villagers, w, jk.prev_forest_cap)
    n_ratio = f_l / max(1, f_d)
    h_col = "green" if (0.12 <= n_ratio <= 0.42) else "red"

    with st.container(border=True):
        st.caption("🔮 **Elder's Vision**")
        v1, v2, v3 = st.columns([2,2,3])
        v1.write(f"🦁 {f_l-jk.lions:+} | 🦌 {f_d-jk.deer:+}")
        v2.write(f"🌳 {f_f-jk.forest:+.1f}%")
        v3.markdown(f"**Ratio:** <span style='color:{h_col}'>{n_ratio:.2f}</span>", unsafe_allow_html=True)

    if st.button("PROCLAIM DECREE", type="primary", use_container_width=True):
        jk.step(action.lower().replace(" ", "_").replace("lions","lion")); st.rerun()
else:
    if jk.victory: st.balloons(); st.success("👑 **LEGENDARY HARMONY ATTAINED!**")
    else: st.error(f"💀 **THE ERA HAS COLLAPSED:** {jk.failure_reason}")
    st.button("🔄 Start New Reign", on_click=jk.reset, use_container_width=True)
