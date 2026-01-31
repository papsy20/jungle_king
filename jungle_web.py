import streamlit as st
import random
import pandas as pd
from datetime import date

# -----------------------------
# The Jungle Spirit (Game Logic)
# -----------------------------
class JungleKing:
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
        self.last_news = [] # Jovial turn feedback
        self.history = []

    def get_status_emoji(self, category, val):
        """Simple status checks for the UI."""
        if category == "lions":
            return "🦁" if val > 2 else "🥀" if val > 0 else "💀"
        if category == "deer":
            return "🦌" if val > 10 else "🍃" if val > 0 else "🦴"
        if category == "forest":
            return "🌳" if val > 30 else "🪵" if val > 15 else "🔥"
        return "🏡"

    def step(self, action: str):
        if self.game_over: return
        self.turn += 1
        self.last_news = []
        
        # --- 1. Your Choices (Village Deeds) ---
        if action == 'hunt_deer':
            hunted = random.randint(5, 8)
            self.deer -= hunted
            self.last_news.append(f"🍖 Feast! We caught {hunted} deer for the village.")
        elif action == 'hunt_lion':
            killed = random.randint(1, 2)
            self.lions = max(0, self.lions - killed)
            self.last_news.append(f"🛡️ Safety: We chased away {killed} lions.")
        elif action == 'expand_village':
            # Harder to build houses if the woods are thin
            cost = 15 if self.forest < 30 else 10
            gain = random.randint(3, 5)
            self.forest -= cost
            self.villagers += gain
            self.last_news.append(f"🏗️ Building: New homes built! +{gain} people, but trees were cut.")
        elif action == 'protect_forest':
            # Bigger villages need more people to guard the woods
            labor = 1 + (self.villagers // 15)
            self.villagers = max(1, self.villagers - labor)
            regen = random.randint(10, 15)
            self.forest = min(100, self.forest + regen)
            self.last_news.append(f"🌱 Planting: We planted new saplings! (Labor: {labor} people).")

        # --- 2. The Jungle's Mood (Natural Changes) ---
        
        # [The Lion Rule] No lions means the deer eat everything green!
        if self.lions == 0 and self.deer > 5:
            loss = random.randint(2, 4)
            self.forest -= loss
            self.last_news.append(f"🦗 Messy Woods: No lions to scare them, so deer ate {loss} units of forest!")

        # [Baby Deer] More forest space means more deer families.
        cap = self.forest * 0.75
        babies = max(1, int(self.deer * 0.20 * (1 - (self.deer / max(1, cap)))))
        self.deer += babies
        
        # [Hungry Lions] Lions hunt deer to stay strong.
        eaten_by_lions = min(int(self.lions * self.deer * 0.035), self.deer)
        self.deer -= eaten_by_lions
        
        # [Hungry People] Every 2 neighbors need 1 deer per turn.
        dinner_needed = int(self.villagers * 0.5)
        if self.deer < dinner_needed:
            sadness = max(1, int((dinner_needed - self.deer) * 0.6))
            self.villagers -= sadness
            self.deer = 0
            self.last_news.append(f"🥣 Empty Bowls: {sadness} people left the village due to hunger.")
        else:
            self.deer -= dinner_needed

        # [Sad Lions] If there's no deer to catch, the lions won't survive.
        if self.lions > 0 and (eaten_by_lions / self.lions) < 1.0: 
            self.lions -= 1
            self.last_news.append("😿 A lion went hungry and left the pride.")

        # --- 3. Wrap Up ---
        self.history.append({"Year": self.turn, "Lions": self.lions, "Deer": self.deer, "Forest": self.forest})
        self.cumulative_score += int(self.lions * 15 + self.deer * 1 + self.villagers * 5 + self.forest * 1)
        self.deer, self.lions, self.forest = max(0, self.deer), max(0, self.lions), max(0, self.forest)
        
        ratio = self.lions / max(1, self.deer)
        if 0.15 <= ratio <= 0.35: self.stable_streak += 1
        else: self.stable_streak = 0

        if self.stable_streak >= 15: self.game_over, self.victory = True, True
        elif any(v <= 0 for v in [self.villagers, self.deer, self.forest]): self.game_over = True

# -----------------------------
# Simple & Clean UI
# -----------------------------
st.set_page_config(page_title="Jungle King", layout="centered")

if 'game' not in st.session_state: st.session_state.game = JungleKing()
if 'high_score' not in st.session_state: st.session_state.high_score = 0
jk = st.session_state.game

# Update High Score
if jk.cumulative_score > st.session_state.high_score:
    st.session_state.high_score = jk.cumulative_score

st.title("🦁 Jungle King")

# Simple Top Bar
c1, c2, c3 = st.columns(3)
c1.write(f"📅 **Year {jk.turn}**")
c2.write(f"🪙 **Score: {jk.cumulative_score}**")
c3.write(f"🏆 **Best: {st.session_state.high_score}**")

with st.expander("📜 The Elder's Wisdom (Rules)", expanded=jk.turn == 0):
    st.write("Welcome, young King! Here is how our world works:")
    st.write("• **Keep the Balance:** Lions keep the deer in check. If lions disappear, deer will eat our forest away!")
    
    st.write("• **Feed the Tribe:** Your people need deer for dinner. If the deer vanish, the village suffers.")
    st.write("• **Stable Heart:** Keep the Lions and Deer in a happy ratio for **15 years** to win!")
    

st.divider()

# Resource Grid (Mobile-friendly 2x2)
g1, g2 = st.columns(2)
g1.metric(f"{jk.get_status_emoji('lions', jk.lions)} Lions", jk.lions)
g1.metric(f"{jk.get_status_emoji('forest', jk.forest)} Forest", jk.forest)
g2.metric(f"{jk.get_status_emoji('deer', jk.deer)} Deer", jk.deer)
g2.metric(f"{jk.get_status_emoji('village', jk.villagers)} People", jk.villagers)

# Stability Bar
st.write(f"**Peace Meter ({jk.stable_streak}/15 Years of Balance)**")
st.progress(jk.stable_streak / 15)

if jk.game_over:
    if jk.victory: st.success(f"👑 YOU ARE THE JUNGLE KING! Score: {jk.cumulative_score}")
    else: st.error("💀 The Jungle has fallen. Nature is out of balance.")
    st.button("🔄 Start New Reign", on_click=jk.reset, type="primary", use_container_width=True)
else:
    # Action Selection
    choice = st.selectbox("What should we do this year?", 
                         ["Hunt Deer", "Hunt Lions", "Expand Village", "Protect Forest"])
    
    # The Elder's Advice Box
    advice = {
        "Hunt Deer": "🏹 'A good hunt fills our bellies, but don't take too many or the lions will starve!'" ,
        "Hunt Lions": "⚔️ 'The lions are getting bold. We should thin the pride to save our deer.'",
        "Expand Village": "🏗️ 'Our families are growing! We need more homes, even if it costs some trees.'",
        "Protect Forest": "🛡️ 'The woods look thin. Let's send the youngsters to plant new life.'"
    }
    st.info(advice[choice])

    if st.button("MAKE IT SO!", type="primary", use_container_width=True):
        jk.step(choice.lower().replace(" ", "_").replace("lions", "lion"))
        st.rerun()

    # Village News (Recent Effects)
    if jk.last_news:
        with st.container(border=True):
            st.write("**Recent News:**")
            for news in jk.last_news: st.write(f"• {news}")

# Trend History
if jk.history:
    with st.expander("📈 Jungle Trends"):
        st.line_chart(pd.DataFrame(jk.history).set_index("Year"))
