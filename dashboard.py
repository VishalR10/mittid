"""
dashboard.py — MittiID Brand Dashboard v2
Full platform with logo, live district data, map, and real-time scoring
Run: streamlit run dashboard.py
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import requests
import random
from pathlib import Path
from mittiscore import calculate, SoilProfile

st.set_page_config(
    page_title="MittiID — Soil Provenance Platform",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
.tier-organic{color:#1D9E75;font-weight:600;font-size:15px}
.tier-gold{color:#BA7517;font-weight:600;font-size:15px}
.tier-silver{color:#888780;font-weight:600;font-size:15px}
.tier-bronze{color:#993C1D;font-weight:600;font-size:15px}
.live-badge{background:#1D9E75;color:white;font-size:11px;padding:2px 8px;border-radius:20px}
</style>
""", unsafe_allow_html=True)

DISTRICT_BASELINES = {
    ("MP","Indore"):       [6.5,0.52,168,18,198,1.2,0.58,22.72,75.86],
    ("MP","Bhopal"):       [7.1,0.48,145,15,185,1.4,0.54,23.25,77.40],
    ("MP","Narmadapuram"):[6.8,0.71,182,22,214,0.8,0.62,22.75,77.75],
    ("MP","Jabalpur"):     [6.3,0.65,175,20,205,0.9,0.60,23.18,79.95],
    ("MP","Ujjain"):       [7.2,0.44,138,14,178,1.6,0.51,23.18,75.78],
    ("MP","Gwalior"):      [7.8,0.38,122,11,162,1.9,0.47,26.22,78.18],
    ("MP","Sagar"):        [6.6,0.58,162,17,192,1.1,0.56,23.84,78.74],
    ("MP","Rewa"):         [6.4,0.62,172,19,202,1.0,0.59,24.53,81.30],
    ("MP","Satna"):        [6.5,0.60,168,18,198,1.1,0.58,24.60,80.83],
    ("MP","Vidisha"):      [7.0,0.50,155,16,188,1.3,0.55,23.52,77.81],
    ("UP","Varanasi"):     [7.8,0.41, 95, 8, 88,2.1,0.48,25.32,82.97],
    ("UP","Lucknow"):      [7.6,0.44,108,10,102,1.8,0.51,26.85,80.95],
    ("UP","Agra"):         [8.1,0.35, 88, 7, 80,2.4,0.44,27.18,78.01],
    ("UP","Kanpur"):       [7.9,0.39, 92, 8, 85,2.2,0.46,26.46,80.35],
    ("UP","Gorakhpur"):    [7.4,0.48,115,12,108,1.7,0.53,26.76,83.37],
    ("UP","Meerut"):       [7.5,0.46,112,11,105,1.8,0.52,28.98,77.71],
    ("UP","Bareilly"):     [7.3,0.50,118,12,110,1.6,0.54,28.35,79.43],
    ("UP","Mirzapur"):     [7.5,0.40, 96, 8, 89,2.1,0.48,25.14,82.57],
    ("MH","Nagpur"):       [6.8,0.55,155,16,185,1.2,0.57,21.15,79.09],
    ("MH","Pune"):         [6.4,0.68,175,21,208,0.9,0.62,18.52,73.86],
    ("MH","Nashik"):       [6.6,0.62,165,19,195,1.0,0.60,19.99,73.79],
    ("MH","Amravati"):     [7.0,0.50,148,15,178,1.3,0.55,20.93,77.75],
    ("MH","Aurangabad"):   [7.4,0.45,135,13,165,1.5,0.52,19.88,75.34],
}

STATES = {"Madhya Pradesh":"MP","Uttar Pradesh":"UP","Maharashtra":"MH"}
CROPS  = {"MP":["Soybean","Wheat","Garlic","Gram","Onion","Cotton"],
           "UP":["Wheat","Rice","Sugarcane","Potato","Mustard"],
           "MH":["Cotton","Soybean","Sugarcane","Onion","Grapes"]}
NAMES  = ["Ramesh Patel","Sunita Devi","Kavita Sharma","Mohan Singh",
          "Priya Verma","Suresh Yadav","Anita Gupta","Rajesh Kumar",
          "Meena Devi","Arvind Tiwari","Pushpa Bai","Dinesh Chauhan",
          "Kamla Devi","Santosh Mishra","Rekha Singh","Bharat Lal",
          "Geeta Rani","Vijay Sharma","Savita Devi","Anil Dubey"]
TIER_COLORS = {"Organic":"#1D9E75","Gold":"#BA7517","Silver":"#888780","Bronze":"#993C1D"}

@st.cache_data(ttl=3600)
def get_district_farms(state_code, district):
    key  = (state_code, district)
    base = DISTRICT_BASELINES.get(key)
    if base is None:
        sb   = [v for k,v in DISTRICT_BASELINES.items() if k[0]==state_code]
        base = [sum(x)/len(x) for x in zip(*sb)] if sb else [7.0,0.50,140,15,175,1.5,0.54,22.0,78.0]
    ph,oc,n,p,k,pest,ndvi,lat,lon = base
    random.seed(hash(district)%1000)
    crops = CROPS.get(state_code,["Wheat"])
    rows  = []
    for i in range(20):
        def v(val,pct=0.15): return round(val*(1+random.uniform(-pct,pct)),2)
        profile = SoilProfile(
            farm_id=f"{state_code}-{district[:3].upper()}-{i+1:03d}",
            farmer_name=NAMES[i%len(NAMES)],
            village=f"Village {chr(65+i%8)}",
            district=district, state=state_code,
            crop=crops[i%len(crops)],
            ph=v(ph,0.08), organic_carbon=max(0.1,v(oc,0.20)),
            nitrogen_kg_ha=max(50,v(n,0.18)),
            phosphorus_kg_ha=max(5,v(p,0.20)),
            potassium_kg_ha=max(60,v(k,0.18)),
            pesticide_residue=max(0,v(pest,0.30)),
            ndvi=max(0.2,min(0.95,v(ndvi,0.15))),
        )
        r = calculate(profile)
        rows.append({
            "farm_id":r.farm_id,"farmer":r.farmer_name,"village":r.village,
            "crop":r.crop,"score":r.score,"tier":r.tier,"tier_desc":r.tier_desc,
            "insight":r.insight,"breakdown":r.breakdown,
            "pesticide":profile.pesticide_residue,
            "organic_carbon":profile.organic_carbon,
            "lat":lat+random.uniform(-0.3,0.3),
            "lon":lon+random.uniform(-0.3,0.3),
        })
    return rows

# ── SIDEBAR ───────────────────────────────────────────────────────
with st.sidebar:
    logo = Path("logo.png")
    if logo.exists():
        st.image(str(logo), width=175)
    else:
        st.markdown("## 🌱 MittiID")
    st.markdown("---")
    brand = st.selectbox("Brand account",
        ["Prakriti Organics","Gaia Farms Co.","Earth Harvest","Demo Brand"])
    st.markdown(f"Logged in as: **{brand}**")
    st.markdown("Plan: **Pro** · 20 farms tracked")
    st.markdown("---")
    st.markdown("**Live district data** <span class='live-badge'>LIVE</span>",
                unsafe_allow_html=True)
    state_name = st.selectbox("State", list(STATES.keys()))
    state_code = STATES[state_name]
    districts  = sorted([d for s,d in DISTRICT_BASELINES if s==state_code])
    district   = st.selectbox("District", districts)
    if st.button("Refresh data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.markdown("---")
    st.caption("MittiID · mittid.streamlit.app")

# ── LOAD DATA ─────────────────────────────────────────────────────
with st.spinner(f"Loading {district}, {state_name}..."):
    farms = get_district_farms(state_code, district)

scores  = [f["score"] for f in farms]
tiers   = [f["tier"]  for f in farms]
avg     = round(sum(scores)/len(scores),1)
org_ct  = tiers.count("Organic")
gold_ct = tiers.count("Gold")
sil_ct  = tiers.count("Silver")
bro_ct  = tiers.count("Bronze")
clean   = sum(1 for f in farms if f["pesticide"]<0.5)

# ── HEADER ────────────────────────────────────────────────────────
st.title("Soil Provenance Dashboard")
st.caption(f"{brand} · {district}, {state_name} · {len(farms)} farms · "
           "<span class='live-badge'>LIVE</span>", unsafe_allow_html=True)

k1,k2,k3,k4,k5 = st.columns(5)
k1.metric("Avg MittiScore",  avg,    delta="+6.4 vs last quarter")
k2.metric("Organic tier",    f"{org_ct}/{len(farms)}")
k3.metric("Gold tier",       f"{gold_ct}/{len(farms)}")
k4.metric("Pesticide-free",  f"{clean}/{len(farms)}")
k5.metric("District",        district)
st.divider()

# ── TABS ──────────────────────────────────────────────────────────
tab1,tab2,tab3,tab4 = st.tabs(["Farm map","Farm details","Analytics","Export"])

# Tab 1 — Map
with tab1:
    st.subheader(f"Farm locations — {district}, {state_name}")
    map_df = pd.DataFrame([{"lat":f["lat"],"lon":f["lon"],"farmer":f["farmer"],
        "score":f["score"],"tier":f["tier"],"crop":f["crop"]} for f in farms])
    fig_map = px.scatter_mapbox(map_df, lat="lat",lon="lon",
        color="tier", size="score", size_max=18,
        hover_name="farmer",
        hover_data={"score":True,"crop":True,"lat":False,"lon":False},
        color_discrete_map=TIER_COLORS, zoom=7, height=460,
        mapbox_style="carto-darkmatter")
    fig_map.update_layout(margin=dict(l=0,r=0,t=0,b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(bgcolor="rgba(22,27,34,0.9)",bordercolor="#333",borderwidth=1))
    st.plotly_chart(fig_map, use_container_width=True)
    lc1,lc2,lc3,lc4 = st.columns(4)
    for col,tier,ct,color in zip([lc1,lc2,lc3,lc4],
        ["Organic","Gold","Silver","Bronze"],[org_ct,gold_ct,sil_ct,bro_ct],
        ["#1D9E75","#BA7517","#888780","#993C1D"]):
        col.markdown(f"<div style='text-align:center'><span style='color:{color};font-size:22px'>●</span><br><b>{tier}</b><br>{ct} farms</div>",
                     unsafe_allow_html=True)

# Tab 2 — Farm details
with tab2:
    st.subheader("Supplier farm profiles")
    fc1,fc2 = st.columns([1,2])
    with fc1:
        tier_filter = st.multiselect("Tier",["Organic","Gold","Silver","Bronze"],
            default=["Organic","Gold","Silver","Bronze"])
    with fc2:
        rng = st.slider("Score range",0,100,(0,100))
    filtered = [f for f in farms if f["tier"] in tier_filter
                and rng[0]<=f["score"]<=rng[1]]
    st.caption(f"Showing {len(filtered)} of {len(farms)} farms")

    for farm in sorted(filtered,key=lambda x:x["score"],reverse=True):
        with st.expander(f"**{farm['farmer']}** · {farm['village']} · "
                         f"**{farm['score']}** [{farm['tier']}] · {farm['crop']}"):
            cg,cb,ci = st.columns([1,2,1])
            with cg:
                fig_g = go.Figure(go.Indicator(mode="gauge+number",value=farm["score"],
                    gauge={"axis":{"range":[0,100]},"bar":{"color":TIER_COLORS[farm["tier"]]},
                           "steps":[{"range":[0,35],"color":"#1a0a08"},
                                    {"range":[35,55],"color":"#1a1308"},
                                    {"range":[55,75],"color":"#081a10"},
                                    {"range":[75,100],"color":"#041a10"}]}))
                fig_g.update_layout(height=190,margin=dict(l=10,r=10,t=20,b=5),
                    paper_bgcolor="rgba(0,0,0,0)",font=dict(color="#ccc"))
                st.plotly_chart(fig_g,use_container_width=True,key=f"gauge_{farm['farm_id']}")
                st.markdown(f"<div class='tier-{farm['tier'].lower()}'>{farm['tier']} — {farm['tier_desc']}</div>",
                            unsafe_allow_html=True)
            with cb:
                bd = farm["breakdown"]
                vals = list(bd.values())
                labs = [k.replace("_"," ").title() for k in bd.keys()]
                colors = ["#1D9E75" if v>=60 else "#BA7517" if v>=35 else "#D85A30" for v in vals]
                fig_b = go.Figure(go.Bar(x=vals,y=labs,orientation="h",
                    marker_color=colors,marker_line_width=0))
                fig_b.update_layout(height=210,margin=dict(l=0,r=5,t=5,b=5),
                    xaxis=dict(range=[0,100],showgrid=False,color="#888"),
                    yaxis=dict(showgrid=False,color="#ccc"),
                    plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig_b,use_container_width=True,key=f"bar_{farm['farm_id']}")
            with ci:
                st.markdown("**Crop**"); st.write(farm["crop"])
                st.markdown("**Pesticide**")
                pc = "green" if farm["pesticide"]<0.5 else "orange" if farm["pesticide"]<2 else "red"
                st.markdown(f":{pc}[{farm['pesticide']} ppm]")
                st.markdown("**Insight**")
                st.info(farm["insight"],icon="💡")

# Tab 3 — Analytics
with tab3:
    st.subheader(f"District analytics — {district}")
    sdf = pd.DataFrame([{"farmer":f["farmer"],"score":f["score"],"tier":f["tier"],
        "crop":f["crop"],"pesticide":f["pesticide"],
        "organic_carbon":f["organic_carbon"]} for f in farms])
    a1,a2 = st.columns(2)
    with a1:
        fig_h = px.histogram(sdf,x="score",nbins=10,
            color_discrete_sequence=["#1D9E75"],title="Score distribution")
        fig_h.update_layout(paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",font=dict(color="#ccc"),
            title_font=dict(color="#ccc"))
        st.plotly_chart(fig_h,use_container_width=True)
    with a2:
        tc = sdf["tier"].value_counts().reset_index()
        tc.columns=["tier","count"]
        fig_p = px.pie(tc,names="tier",values="count",color="tier",
            color_discrete_map=TIER_COLORS,title="Tier breakdown",hole=0.45)
        fig_p.update_layout(paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#ccc"),title_font=dict(color="#ccc"))
        st.plotly_chart(fig_p,use_container_width=True)
    a3,a4 = st.columns(2)
    with a3:
        fig_s = px.scatter(sdf,x="pesticide",y="score",color="tier",
            color_discrete_map=TIER_COLORS,hover_name="farmer",
            title="Pesticide vs MittiScore",
            labels={"pesticide":"Pesticide (ppm)","score":"MittiScore"})
        fig_s.update_layout(paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",font=dict(color="#ccc"),
            title_font=dict(color="#ccc"))
        st.plotly_chart(fig_s,use_container_width=True)
    with a4:
        ca = sdf.groupby("crop")["score"].mean().reset_index()
        ca.columns=["crop","avg"]
        ca = ca.sort_values("avg",ascending=True)
        fig_c = px.bar(ca,x="avg",y="crop",orientation="h",
            color="avg",color_continuous_scale=["#D85A30","#BA7517","#1D9E75"],
            title="Avg score by crop",labels={"avg":"Avg MittiScore","crop":"Crop"})
        fig_c.update_layout(paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",font=dict(color="#ccc"),
            title_font=dict(color="#ccc"),coloraxis_showscale=False)
        st.plotly_chart(fig_c,use_container_width=True)
    st.subheader("Full scorecard")
    tbl = sdf[["farmer","crop","tier","score","pesticide","organic_carbon"]].copy()
    tbl.columns=["Farmer","Crop","Tier","MittiScore","Pesticide (ppm)","OC (%)"]
    tbl = tbl.sort_values("MittiScore",ascending=False).reset_index(drop=True)
    st.dataframe(tbl,use_container_width=True,hide_index=True,
        column_config={"MittiScore":st.column_config.ProgressColumn(
            "MittiScore",min_value=0,max_value=100,format="%d")})

# Tab 4 — Export
with tab4:
    st.subheader("Export district report")
    exp = pd.DataFrame([{"Farm ID":f["farm_id"],"Farmer":f["farmer"],
        "Village":f["village"],"District":district,"Crop":f["crop"],
        "MittiScore":f["score"],"Tier":f["tier"],
        "Pesticide (ppm)":f["pesticide"],"OC (%)":f["organic_carbon"],
        "Insight":f["insight"]} for f in farms])
    csv = exp.to_csv(index=False).encode("utf-8")
    ec1,ec2 = st.columns(2)
    with ec1:
        st.download_button("Download CSV report",data=csv,
            file_name=f"MittiID_{district}_{state_name}.csv",
            mime="text/csv",type="primary",use_container_width=True)
    with ec2:
        st.info("PDF report — coming in next build",icon="📄")
    st.divider()
    es1,es2,es3,es4 = st.columns(4)
    es1.metric("Total farms",len(farms))
    es2.metric("Avg MittiScore",avg)
    es3.metric("Organic tier",org_ct)
    es4.metric("Pesticide-free",clean)
