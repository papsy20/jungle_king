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
        # Balanced for Turn 12-16 Climax
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
        self.warnings = []

    def get_stability(self):
        if self.deer <= 0: return 0, "Extinct", "red"
        ratio = self.tigers / self.deer
        if 0.15 <= ratio <= 0.35: return 100, "Stable ✅", "green"
        return 40, "Unstable ⚠️", "orange"

    def step(self, action: str):
        if self.game_over: return
        self.turn += 1
        self.warnings = []
        p_eff, n_eff = {}, {}
        
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
            p_eff['Habitat Cleared'] = -12
        elif action == 'protect_forest':
            self.villagers = max(1, self.villagers - 2)
            self.forest = min(100, self.forest + 10)
            p_eff['Labor Used'] = -2

        # --- 2. Ecological Decay Logic (Simple English) ---
        
        # [Decay] Overgrazing: If Tigers are gone, Deer destroy the Forest.
        if self.tigers == 0 and self.deer > 5:
            self.forest -= 3
            n_eff['Overgrazing Decay'] = -3
            self.warnings.append("⚠️ Trophic Cascade: No predators! Deer are eating the Forest younglings.")

        # [Growth] Forest Capacity: The forest determines how many deer can be born.
        cap = self.forest * 0.75
        growth = int(self.deer * 0.20 * (1 - (self.deer / max(1, cap))))
        self.deer += max(1, growth)
        n_eff['Deer Births'] = max(1, growth)
        
        # [Decay] Predation: Tigers eat 2.5% of the Deer population.
        eaten = min(int(self.tigers * self.deer * 0.025), self.deer)
        self.deer -= eaten
        n_eff['Predation'] = -eaten

        # [Decay] Famine: 2 Villagers eat 1 Deer. 
        demand = int(self.villagers * 0.5)
        if self.deer < demand:
            lost = max(1, int((demand - self.deer) * 0.6))
            self.villagers -= lost
            self.deer = 0
            n_eff['Famine Loss'] = -lost
            self.warnings.append("🥣 Hunger: Not enough Deer to feed the village!")
        else:
            self.deer -= demand

        # [Decay] Tiger Starvation: A Tiger dies if it catches less than 1 Deer.
        if self.tigers > 0 and (eaten / self.tigers) < 1.0: 
            self.tigers -= 1
            n_eff['Tiger Starved'] = -1
            self.warnings.append("💀 Starvation: A Tiger died because it couldn't find food.")

        # --- 3. Finalization ---
        self.last_effects = {"player": p_eff, "nature": n_eff}
        self.cumulative_score += int(self.tigers * 5 + self.deer * 1 + self.villagers * 3)
        self.deer, self.tigers, self.forest = max(0, self.deer), max(0, self.tigers), max(0, self.forest)
        
        perc, status, _ = self.get_stability()
        self.stable_streak = self.stable_streak + 1 if status == "Stable ✅" else 0

        if self.stable_streak >= 15: self.game_over, self.victory = True, True
        elif any(v <= 0 for v in [self.villagers, self.deer, self.forest]): self.game_over = True

# -----------------------------
# Mobile UI 
# -----------------------------
st.set_page_config(page_title="Jungle King", layout="centered")

if 'j' not in st.session_state: st.session_state.j = Jungle()
if 'high_score' not in st.session_state: st.session_state.high_score = 0
j = st.session_state.j

st.title("🦁 Jungle King")
st.caption(f"v1.3 | Author: Papsy | {date.today().strftime('%Y-%m-%d')}")

# Top Row Stats
m1, m2 = st.columns(2)
m1.metric("🐅 Tigers", j.tigers)
m2.metric("🦌 Deer", j.deer)
m3, m4 = st.columns(2)
m3.metric("🌳 Forest", j.forest)
m4.metric("👥 Village", j.villagers)

# Status Bar
perc, status, color = j.get_stability()
st.write(f"**{status}** (Streak: {j.stable_streak}/15) | Best: `{st.session_state.high_score}`")
st.progress(perc / 100)

# Nature's Warnings
for w in j.warnings:
    st.warning(w)

st.divider()

if j.game_over:
    if j.cumulative_score > st.session_state.high_score:
        st.session_state.high_score = j.cumulative_score
    if getattr(j, 'victory', False): st.success("🏆 VICTORY! The Jungle King reigns.")
    else: st.error("❌ THE JUNGLE COLLAPSED")
    st.button("🔄 Try Again", on_click=j.reset, type="primary", use_container_width=True)
else:
    action = st.selectbox("Your Move:", ["Hunt Deer", "Hunt Tigers", "Expand Village", "Protect Forest"])
    key = action.lower().replace(" ", "_")
    if st.button(f"Confirm {action}", type="primary", use_container_width=True):
        j.step(key)
        st.rerun()

with st.expander("📋 Turn Insights"):
    if j.last_effects['player']:
        st.write("**Human Impact:**")
        for k, v in j.last_effects['player'].items(): st.write(f"🔹 {k}: {v}")
        st.write("**Nature's Response:**")
        for k, v in j.last_effects['nature'].items(): st.write(f"🍃 {k}: {v}")

with st.expander("📖 Nature's Rules (Simple English)"):
    st.write("""
    1. **Trophic Cascade (The Tiger Rule)**: If Tigers go extinct, the Deer will overpopulate and destroy the Forest automatically.
    2. **Carrying Capacity**: The Deer population cannot grow larger than what the Forest can feed.
    3. **Deer Decay**: 2 Villagers eat 1 Deer. If the Deer are gone, the Village starves.
    4. **Tiger Decay**: A Tiger must catch at least 1 Deer per turn or it will perish.
    """)
