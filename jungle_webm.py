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
        self.echo_log = []

        # Difficulty settings
        diff_settings = {
            "Low":    {"growth": 0.16, "weight_start": 8,  "ramp": 0.28, "win_target": 25},
            "Medium": {"growth": 0.24, "weight_start": 12, "ramp": 0.22, "win_target": 18},
            "High":   {"growth": 0.30, "weight_start": 10, "ramp": 0.30, "win_target": 15}
        }
        self.cfg = diff_settings[self.difficulty]

    def get_difficulty_weight(self):
        return 1.0 + (max(0, self.turn - self.cfg["weight_start"]) * self.cfg["ramp"])

    def calculate_mechanics(self, action, l, d, f, v, w, prev_cap):
        comm_list = []  # Multiple commentary messages per turn

        # 1. Action Impact (Change Parameters)
        if action == 'hunt_deer': 
            d -= 5
            f -= (1.0 * w)
            comm_list.append(f"The spears find their mark ({w:.1f}x Winter Weight).")
        elif action == 'hunt_lion': 
            l = max(0, l - 1)
            f -= (1.5 * w)
            comm_list.append(f"A roar is silenced. The forest feels the Weight ({w:.1f}x) of our presence.")
        elif action == 'expand_village': 
            f -= (12 * w)
            v += 3
            comm_list.append(f"Homes rise; forest recedes under our growing needs ({w:.1f}x).")
        elif action == 'protect_forest':
            # FIX: Ensure float division before int conversion for smoother scaling
            regen_calc = ((100.0 - f) * 0.25) / (1.0 + (d/200.0)) / float(w)
            regen = max(3, int(regen_calc))
            f = min(100, f + regen)
            comm_list.append(f"Our folk are in the mud, planting saplings (+{regen}% Forest).")

        # 2. Births & Predation (The Spring Echo)
        # Smoothed from 0.9-1.2 to 0.95-1.05 to reduce extreme RNG
        boom_factor = random.uniform(0.95, 1.05) 
        births = max(2, int(d * (self.cfg["growth"] / w) * (1 - (d / max(1, prev_cap))) * boom_factor))
        d += births
        if births > 10: comm_list.append("The Spring Echo brings a flood of fawns from the past bounty!")

        # Predation smoothing: limit extreme swings
        predation_rate = random.uniform(0.9, 1.1) 
        eaten = min(round(l * predation_rate), d)
        d -= eaten
        comm_list.append(f"Lions have hunted {eaten} deer.")

        # 3. Hunger & Village Flight (Decay Parameters)
        food_needed = max(1, int((v // 4) * w))
        if d < food_needed: 
            v_lost = max(1, int(v * 0.12 * w))
            v = max(0, v - v_lost)
            d = 0
            comm_list.append(f"Famine! {v_lost} villagers left for kinder lands.")
        else: 
            d -= food_needed

        # Lion starvation (Death Spiral) scaled with weight
        if l > 0 and (eaten / max(1, l)) < (0.5 * w): 
            l = max(0, l - 1)
            comm_list.append("A lion has wandered away in search of easier prey.")

        # 4. Collapse Mechanics (Trophic Decay)
        current_cap = f * 1.1
        if l <= 0: 
            f = max(0, f - (2.5 * w)) 
            comm_list.append("The Lions are gone! The Silent Rot eats the world at double speed.")
        
        if d > current_cap: 
            excess_decay = min(8.0, ((d - current_cap) / 10) * 0.5 * w)
            f = max(0, f - excess_decay)
            comm_list.append("Overgrazing! The herd devours the new shoots before they can grow.")

        return l, d, f, v, births, eaten, comm_list, current_cap

    def step(self, action):
        if self.game_over: return
        self.turn += 1
        w = self.get_difficulty_weight()

        self.lions, self.deer, self.forest, self.villagers, _, _, comm_list, new_cap = \
            self.calculate_mechanics(action, self.lions, self.deer, self.forest, self.villagers, w, self.prev_forest_cap)
        self.prev_forest_cap = new_cap
        self.history.append({"Season": self.turn, "L": self.lions, "D": self.deer, "F": self.forest, "V": self.villagers})
        self.echo_log.extend([(self.turn, c) for c in comm_list]) 

        # Harmony Check
        ratio = self.lions / max(1, self.deer)
        if 0.12 <= ratio <= 0.42: self.stable_streak += 1
        else: self.stable_streak = 0

        if self.stable_streak >= self.cfg["win_target"]: 
            self.game_over, self.victory = True, True
        elif self.villagers <= 0 or self.deer <= 0 or self.forest <= 0 or self.turn >= 60:
            self.failure_reason = "The circle of life has shattered."
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

# Atmosphere
ratio = jk.lions / max(1, jk.deer)
is_harmonious = 0.12 <= ratio <= 0.42
bg_color = "#f0f2f6" if is_harmonious else "#fbe9e7"
if jk.forest < 30: bg_color = "#e6e1d3"
st.markdown(f"<style>.stApp {{ background-color: {bg_color}; transition: background-color 2s; }}</style>", unsafe_allow_html=True)

st.title("🦁 Jungle King")

with st.expander("👴 *'Listen closely to the Laws of the Valley...'*", expanded=(jk.turn == 0)):
    st.info(f"""
    * 🌿 **The Spring Echo:** Nature moves slowly. Deer births reflect the forest health of the *last* season.
    * ❄️ **The Winter Weight:** As the years pass, hunger and overgrazing become **{jk.cfg['ramp']}x heavier** each turn.
    * 🦁 **The Golden Ratio:** Keep Lions/Deer between **0.12 and 0.42**. Hold this for **{jk.cfg['win_target']} seasons** to win!
    * 🍂 **The Silent Rot:** Without Lions, the deer settle and rot the forest roots at double the speed.
    """)

if jk.turn == 0:
    jk.difficulty = st.select_slider("👴 *'How heavy shall the crown be?'*", options=["Low","Medium","High"], value=jk.difficulty)
    jk.reset()

with st.sidebar:
    st.header("📜 High King's Library")
    if st.button("New Era"): jk.reset(); st.rerun()
    if jk.history: st.table(pd.DataFrame(jk.history).tail(3))

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

    action = st.radio("👴 *'Which Decree shall be read?'*", 
                      ["Hunt Deer", "Hunt Lions", "Expand Village", "Protect Forest"], horizontal=True)

    w = jk.get_difficulty_weight()
    f_l, f_d, f_f, f_v, _, _, comm_list, _ = jk.calculate_mechanics(action.lower().replace(" ", "_").replace("lions","lion"), jk.lions, jk.deer, jk.forest, jk.villagers, w, jk.prev_forest_cap)
    n_ratio = f_l / max(1, f_d)
    h_col = "green" if (0.12 <= n_ratio <= 0.42) else "red"

    with st.container(border=True):
        st.caption("🔮 **The Elder's Vision**")
        for msg in comm_list: st.write(f"👴 *\"{msg}\"*")
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
