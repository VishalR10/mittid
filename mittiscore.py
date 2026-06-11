"""
mittiscore.py — MittiID core scoring engine
Run: python mittiscore.py
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import Optional


# ── Tier thresholds ──────────────────────────────────────────────
TIERS = [
    (75, "Organic",  "Meets premium organic standards"),
    (55, "Gold",     "Strong organic transition progress"),
    (35, "Silver",   "Active transition — chemical use declining"),
    (0,  "Bronze",   "Early stage — baseline established"),
]


@dataclass
class SoilProfile:
    """One farm plot's soil data. All values normalised 0–100 before scoring."""
    farm_id:           str
    farmer_name:       str
    village:           str
    district:          str
    state:             str
    crop:              str

    # Soil parameters (raw values)
    ph:                float          # 0–14
    organic_carbon:    float          # % (0–3+ is typical)
    nitrogen_kg_ha:    float          # kg/hectare
    phosphorus_kg_ha:  float          # kg/hectare
    potassium_kg_ha:   float          # kg/hectare
    pesticide_residue: float          # ppm (lower = better)

    # Optional enrichment
    ndvi:              Optional[float] = None   # 0–1 satellite greenness
    rainfall_mm:       Optional[float] = None   # annual mm
    previous_score:    Optional[float] = None   # last quarter's score


@dataclass
class MittiResult:
    farm_id:      str
    farmer_name:  str
    village:      str
    district:     str
    crop:         str
    score:        float
    tier:         str
    tier_desc:    str
    breakdown:    dict
    insight:      str
    delta:        Optional[float] = None  # change from last score


def _norm_ph(ph: float) -> float:
    """pH 6.0–7.5 is ideal for most crops → score 100. Outside → drops."""
    if 6.0 <= ph <= 7.5:
        return 100.0
    elif ph < 6.0:
        return max(0, 100 - (6.0 - ph) * 25)
    else:
        return max(0, 100 - (ph - 7.5) * 25)


def _norm_oc(oc: float) -> float:
    """Organic carbon: 0.75% = baseline (50), 2%+ = excellent (100)."""
    return min(100, max(0, (oc / 2.0) * 100))


def _norm_npk(val: float, low: float, high: float) -> float:
    """Linear normalise: below low = poor, above high = excellent."""
    return min(100, max(0, ((val - low) / (high - low)) * 100))


def _norm_pesticide(ppm: float) -> float:
    """Invert: 0 ppm = 100 (clean), 5+ ppm = 0 (heavily contaminated)."""
    return max(0, 100 - (ppm / 5.0) * 100)


def calculate(profile: SoilProfile) -> MittiResult:
    """
    Weighted MittiScore formula (v1.0)

    Component            Weight   Rationale
    ─────────────────────────────────────────────────────────────────
    Pesticide residue     30%     Core organic signal — most important
    Organic carbon        25%     Long-term soil health indicator
    pH suitability        15%     Foundation for nutrient availability
    Nitrogen (N)          10%     Primary macronutrient
    Phosphorus (P)         8%     Root development, flowering
    Potassium (K)          7%     Disease resistance, water regulation
    NDVI satellite bonus   5%     Real-world crop health evidence
    ─────────────────────────────────────────────────────────────────
    """
    pest  = _norm_pesticide(profile.pesticide_residue)
    oc    = _norm_oc(profile.organic_carbon)
    ph    = _norm_ph(profile.ph)
    n     = _norm_npk(profile.nitrogen_kg_ha,    low=100, high=280)
    p     = _norm_npk(profile.phosphorus_kg_ha,  low=10,  high=50)
    k     = _norm_npk(profile.potassium_kg_ha,   low=100, high=280)
    ndvi  = (profile.ndvi * 100) if profile.ndvi is not None else ph  # fallback

    score = (
        pest  * 0.30 +
        oc    * 0.25 +
        ph    * 0.15 +
        n     * 0.10 +
        p     * 0.08 +
        k     * 0.07 +
        ndvi  * 0.05
    )
    score = round(score, 1)

    tier_name, tier_desc = "Bronze", TIERS[-1][2]
    for threshold, name, desc in TIERS:
        if score >= threshold:
            tier_name, tier_desc = name, desc
            break

    breakdown = {
        "pesticide_score":  round(pest, 1),
        "organic_carbon":   round(oc,   1),
        "ph_suitability":   round(ph,   1),
        "nitrogen":         round(n,    1),
        "phosphorus":       round(p,    1),
        "potassium":        round(k,    1),
        "ndvi_satellite":   round(ndvi, 1),
    }

    # Auto-generate the key insight for the brand report
    weakest = min(breakdown, key=breakdown.get)
    labels  = {
        "pesticide_score": "pesticide residue is still present — continue chemical-free period",
        "organic_carbon":  "organic carbon is low — add compost or green manure",
        "ph_suitability":  "soil pH needs adjustment — consider lime or sulfur application",
        "nitrogen":        "nitrogen is deficient — use legume cover crops",
        "phosphorus":      "phosphorus needs attention — apply rock phosphate",
        "potassium":       "potassium is low — banana peels or wood ash compost help",
        "ndvi_satellite":  "crop canopy health needs monitoring",
    }
    insight = f"Priority improvement: {labels[weakest]}"

    delta = None
    if profile.previous_score is not None:
        delta = round(score - profile.previous_score, 1)

    return MittiResult(
        farm_id=profile.farm_id,
        farmer_name=profile.farmer_name,
        village=profile.village,
        district=profile.district,
        crop=profile.crop,
        score=score,
        tier=tier_name,
        tier_desc=tier_desc,
        breakdown=breakdown,
        insight=insight,
        delta=delta,
    )


def score_batch(df: pd.DataFrame) -> pd.DataFrame:
    """
    Score a whole CSV of farms at once.
    Expected columns: farm_id, farmer_name, village, district, state,
                      crop, ph, organic_carbon, nitrogen_kg_ha,
                      phosphorus_kg_ha, potassium_kg_ha, pesticide_residue
    Optional:         ndvi, rainfall_mm, previous_score
    """
    results = []
    for _, row in df.iterrows():
        profile = SoilProfile(
            farm_id=row["farm_id"],
            farmer_name=row["farmer_name"],
            village=row["village"],
            district=row["district"],
            state=row.get("state", ""),
            crop=row["crop"],
            ph=float(row["ph"]),
            organic_carbon=float(row["organic_carbon"]),
            nitrogen_kg_ha=float(row["nitrogen_kg_ha"]),
            phosphorus_kg_ha=float(row["phosphorus_kg_ha"]),
            potassium_kg_ha=float(row["potassium_kg_ha"]),
            pesticide_residue=float(row["pesticide_residue"]),
            ndvi=float(row["ndvi"]) if "ndvi" in row and pd.notna(row["ndvi"]) else None,
            previous_score=float(row["previous_score"]) if "previous_score" in row and pd.notna(row["previous_score"]) else None,
        )
        r = calculate(profile)
        results.append({
            "farm_id":     r.farm_id,
            "farmer_name": r.farmer_name,
            "village":     r.village,
            "district":    r.district,
            "crop":        r.crop,
            "mittiscore":  r.score,
            "tier":        r.tier,
            "tier_desc":   r.tier_desc,
            "delta":       r.delta,
            "insight":     r.insight,
            **{f"component_{k}": v for k, v in r.breakdown.items()},
        })
    return pd.DataFrame(results)


# ── Demo run ─────────────────────────────────────────────────────
if __name__ == "__main__":

    sample_farms = pd.DataFrame([
        {
            "farm_id": "MP-NMD-001",
            "farmer_name": "Ramesh Patel",
            "village": "Sehore",
            "district": "Narmadapuram",
            "state": "Madhya Pradesh",
            "crop": "Soybean",
            "ph": 6.8,
            "organic_carbon": 0.72,
            "nitrogen_kg_ha": 180,
            "phosphorus_kg_ha": 22,
            "potassium_kg_ha": 210,
            "pesticide_residue": 0.4,
            "ndvi": 0.71,
            "previous_score": 54.2,
        },
        {
            "farm_id": "UP-VNS-014",
            "farmer_name": "Sunita Devi",
            "village": "Mirzapur",
            "district": "Varanasi",
            "state": "Uttar Pradesh",
            "crop": "Wheat",
            "ph": 7.8,
            "organic_carbon": 0.41,
            "nitrogen_kg_ha": 95,
            "phosphorus_kg_ha": 8,
            "potassium_kg_ha": 88,
            "pesticide_residue": 2.1,
            "ndvi": 0.48,
            "previous_score": 28.0,
        },
        {
            "farm_id": "MP-IDR-033",
            "farmer_name": "Kavita Sharma",
            "village": "Ujjain",
            "district": "Indore",
            "state": "Madhya Pradesh",
            "crop": "Garlic",
            "ph": 6.5,
            "organic_carbon": 1.85,
            "nitrogen_kg_ha": 255,
            "phosphorus_kg_ha": 44,
            "potassium_kg_ha": 265,
            "pesticide_residue": 0.05,
            "ndvi": 0.83,
            "previous_score": 68.1,
        },
    ])

    results = score_batch(sample_farms)

    print("\n" + "="*60)
    print("  MittiID — Soil Provenance Report")
    print("="*60)

    for _, row in results.iterrows():
        delta_str = ""
        if row["delta"] is not None:
            arrow = "▲" if row["delta"] >= 0 else "▼"
            delta_str = f"  {arrow} {abs(row['delta'])} from last quarter"

        print(f"\n  {row['farm_id']}  |  {row['farmer_name']}, {row['village']}")
        print(f"  Crop: {row['crop']}  |  District: {row['district']}")
        print(f"\n  MittiScore:  {row['mittiscore']} / 100   [{row['tier']}]{delta_str}")
        print(f"  {row['tier_desc']}")
        print(f"\n  Component breakdown:")
        for col in results.columns:
            if col.startswith("component_"):
                label = col.replace("component_", "").replace("_", " ").title()
                bar = "█" * int(row[col] / 10) + "░" * (10 - int(row[col] / 10))
                print(f"    {label:<22} {bar}  {row[col]}")
        print(f"\n  Insight: {row['insight']}")
        print("  " + "-"*56)

    print("\n  Saving results to mittiscore_results.csv ...")
    results.to_csv("mittiscore_results.csv", index=False)
    print("  Done.\n")
