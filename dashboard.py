"""
dashboard.py — MittiID brand-facing Streamlit dashboard
Run: streamlit run dashboard.py
Deploy free: streamlit.io/cloud
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from mittiscore import calculate, SoilProfile, TIERS

st.set_page_config(
    page_title="MittiID — Soil Provenance Dashboard",
    page_icon="🌱",
    layout="wide"
)

st.markdown("""
<style>
.metric-card {
    background: #f8f9fa;
    border-radius: 10px;
    padding: 16px 20px;
    border: 1px solid #e9ecef;
}
.tier-organic { color: #1D9E75; font-weight: 600; }
.tier-gold    { color: #BA7517; font-weight: 600; }
.tier-silver  { color: #5F5E5A; font-weight: 600; }
.tier-bronze  { color: #993C1D; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar: brand login simulation ──────────────────────────────
with st.sidebar:
    st.image("https://via.placeholder.com/200x60?text=MittiID", width=200)
    st.markdown("---")
    brand = st.selectbox("Brand account", ["Prakriti Organics", "Gaia Farms Co.", "Demo Brand"])
    st.markdown(f"**Logged in as:** {brand}")
    st.markdown("**Plan:** Pro · 5 farms tracked")
    st.markdown("---")
    st.caption("MittiID · Soil Provenance Platform")

# ── Sample farm data (replace with live DB in production) ────────
FARMS = [
    SoilProfile("MP-NMD-001","Ramesh Patel","Sehore","Narmadapuram","MP","Soybean",
                6.8,0.72,180,22,210,0.4,ndvi=0.71,previous_score=54.2),
    SoilProfile("UP-VNS-014","Sunita Devi","Mirzapur","Varanasi","UP","Wheat",
                7.8,0.41,95,8,88,2.1,ndvi=0.48,previous_score=28.0),
    SoilProfile("MP-IDR-033","Kavita Sharma","Ujjain","Indore","MP","Garlic",
                6.5,1.85,255,44,265,0.05,ndvi=0.83,previous_score=68.1),
]
results = [calculate(f) for f in FARMS]

# ── Header ────────────────────────────────────────────────────────
st.title("Soil Provenance Dashboard")
st.caption(f"{brand} · {len(results)} supplier farms · Last updated today")

# ── Top KPI row ───────────────────────────────────────────────────
avg_score = round(sum(r.score for r in results) / len(results), 1)
organic_count = sum(1 for r in results if r.tier == "Organic")
improving = sum(1 for r in results if r.delta and r.delta > 0)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Average MittiScore", avg_score, delta="+8.2 vs last quarter")
c2.metric("Organic tier farms", f"{organic_count} / {len(results)}")
c3.metric("Improving farms", f"{improving} / {len(results)}")
c4.metric("Pesticide-free farms", sum(1 for f in FARMS if f.pesticide_residue < 0.5))

st.divider()

# ── Farm cards ────────────────────────────────────────────────────
st.subheader("Your supplier farms")

for farm, result in zip(FARMS, results):
    with st.expander(
        f"**{result.farmer_name}** · {result.village}, {result.district}"
        f"  —  MittiScore **{result.score}** [{result.tier}]",
        expanded=(result.score == max(r.score for r in results))
    ):
        col_score, col_breakdown, col_insight = st.columns([1, 2, 1])

        with col_score:
            # Gauge chart
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=result.score,
                domain={"x": [0, 1], "y": [0, 1]},
                title={"text": "MittiScore"},
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"color": "#1D9E75"},
                    "steps": [
                        {"range": [0,  35], "color": "#FAECE7"},
                        {"range": [35, 55], "color": "#FAEEDA"},
                        {"range": [55, 75], "color": "#E1F5EE"},
                        {"range": [75,100], "color": "#EAF3DE"},
                    ],
                    "threshold": {"line": {"color": "#0F6E56","width": 3},
                                  "thickness": 0.75, "value": result.score}
                }
            ))
            fig.update_layout(height=220, margin=dict(l=10,r=10,t=30,b=10))
            st.plotly_chart(fig, use_container_width=True)
            tier_color = result.tier.lower()
            st.markdown(f"<div class='tier-{tier_color}'>{result.tier} tier — {result.tier_desc}</div>",
                        unsafe_allow_html=True)
            if result.delta:
                arrow = "▲" if result.delta > 0 else "▼"
                st.caption(f"{arrow} {abs(result.delta)} points from last quarter")

        with col_breakdown:
            bd = result.breakdown
            labels = [k.replace("_", " ").title() for k in bd.keys()]
            values = list(bd.values())
            fig2 = go.Figure(go.Bar(
                x=values, y=labels,
                orientation="h",
                marker_color=["#1D9E75" if v >= 60 else "#BA7517" if v >= 35 else "#D85A30"
                              for v in values],
            ))
            fig2.update_layout(
                height=220, margin=dict(l=0,r=10,t=10,b=10),
                xaxis=dict(range=[0,100], showgrid=False),
                yaxis=dict(showgrid=False),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig2, use_container_width=True)

        with col_insight:
            st.markdown("**Crop**")
            st.write(farm.crop)
            st.markdown("**Pesticide level**")
            st.write(f"{farm.pesticide_residue} ppm")
            st.markdown("**Organic carbon**")
            st.write(f"{farm.organic_carbon}%")
            st.markdown("**Key insight**")
            st.info(result.insight, icon="💡")

# ── Portfolio trend chart ─────────────────────────────────────────
st.divider()
st.subheader("Portfolio score history")

history = pd.DataFrame({
    "Quarter": ["Q2 2024","Q3 2024","Q4 2024","Q1 2025","Q2 2025"],
    "Ramesh Patel":   [42, 48, 54, 58, 66],
    "Sunita Devi":    [20, 24, 28, 33, 39],
    "Kavita Sharma":  [52, 61, 68, 76, 94],
})
fig3 = px.line(
    history.melt("Quarter", var_name="Farmer", value_name="MittiScore"),
    x="Quarter", y="MittiScore", color="Farmer",
    markers=True,
    color_discrete_sequence=["#1D9E75","#BA7517","#534AB7"]
)
fig3.update_layout(
    height=300, margin=dict(l=0,r=0,t=10,b=0),
    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    yaxis=dict(range=[0,100], showgrid=True, gridcolor="#f0f0f0"),
    xaxis=dict(showgrid=False),
)
st.plotly_chart(fig3, use_container_width=True)

st.caption("MittiID — Soil Provenance Platform · Built for organic food brands")
