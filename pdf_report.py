"""
pdf_report.py — MittiID Branded PDF Report Generator
=====================================================
Generates a professional soil provenance report for any farm or district.
Use this to email brands as a free sample before your first sales call.

Usage:
    python pdf_report.py                          # demo report
    python pdf_report.py --farm MP-IDR-033        # single farm
    python pdf_report.py --district Indore --state MP  # full district
"""

import argparse
from pathlib import Path
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white, black
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                 Table, TableStyle, HRFlowable, Image)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.graphics.shapes import Drawing, Rect, String, Circle
from reportlab.graphics import renderPDF
from mittiscore import calculate, SoilProfile

# ── Brand colours ─────────────────────────────────────────────────
GREEN    = HexColor("#1D9E75")
DGREEN   = HexColor("#085041")
LGREEN   = HexColor("#EAF3DE")
AMBER    = HexColor("#BA7517")
LAMBER   = HexColor("#FAEEDA")
CORAL    = HexColor("#D85A30")
DGREY    = HexColor("#2C2C2A")
MGREY    = HexColor("#5F5E5A")
LGREY    = HexColor("#F1EFE8")
BGREY    = HexColor("#E8E8E0")
WHITE    = white

TIER_COLORS = {
    "Organic": HexColor("#1D9E75"),
    "Gold":    HexColor("#BA7517"),
    "Silver":  HexColor("#888780"),
    "Bronze":  HexColor("#993C1D"),
}
TIER_BG = {
    "Organic": HexColor("#EAF3DE"),
    "Gold":    HexColor("#FAEEDA"),
    "Silver":  HexColor("#F1EFE8"),
    "Bronze":  HexColor("#FAECE7"),
}

# ── Sample farm data (same as dashboard) ─────────────────────────
SAMPLE_FARMS = {
    "MP-NMD-001": SoilProfile(
        "MP-NMD-001","Ramesh Patel","Sehore","Narmadapuram","MP","Soybean",
        6.8,0.72,180,22,210,0.4,ndvi=0.71,previous_score=54.2),
    "UP-VNS-014": SoilProfile(
        "UP-VNS-014","Sunita Devi","Mirzapur","Varanasi","UP","Wheat",
        7.8,0.41,95,8,88,2.1,ndvi=0.48,previous_score=28.0),
    "MP-IDR-033": SoilProfile(
        "MP-IDR-033","Kavita Sharma","Ujjain","Indore","MP","Garlic",
        6.5,1.85,255,44,265,0.05,ndvi=0.83,previous_score=68.1),
}


def score_bar_drawing(score: float, tier: str,
                       width=120, height=16) -> Drawing:
    """Horizontal score bar with filled portion."""
    d = Drawing(width, height)
    # Background
    d.add(Rect(0, 2, width, height-4, rx=4, ry=4,
               fillColor=BGREY, strokeColor=None))
    # Fill
    fill_w = max(4, int((score/100) * width))
    d.add(Rect(0, 2, fill_w, height-4, rx=4, ry=4,
               fillColor=TIER_COLORS.get(tier, GREEN),
               strokeColor=None))
    return d


def make_styles():
    """Return all paragraph styles used in the report."""
    base = dict(fontName="Helvetica", textColor=DGREY)

    return {
        "cover_brand": ParagraphStyle("cb", fontName="Helvetica-Bold",
            fontSize=11, textColor=MGREY, spaceAfter=4),
        "cover_title": ParagraphStyle("ct", fontName="Helvetica-Bold",
            fontSize=28, textColor=DGREY, spaceAfter=8, leading=34),
        "cover_sub":   ParagraphStyle("cs", fontName="Helvetica",
            fontSize=13, textColor=MGREY, spaceAfter=4),
        "section":     ParagraphStyle("sec", fontName="Helvetica-Bold",
            fontSize=13, textColor=DGREEN, spaceBefore=10, spaceAfter=6),
        "body":        ParagraphStyle("body", fontName="Helvetica",
            fontSize=10, textColor=DGREY, leading=15, spaceAfter=4),
        "small":       ParagraphStyle("sm", fontName="Helvetica",
            fontSize=8, textColor=MGREY, leading=12),
        "footer":      ParagraphStyle("ft", fontName="Helvetica",
            fontSize=8, textColor=MGREY, alignment=TA_CENTER),
        "score_big":   ParagraphStyle("sb", fontName="Helvetica-Bold",
            fontSize=42, textColor=GREEN, alignment=TA_CENTER, leading=46),
        "tier_label":  ParagraphStyle("tl", fontName="Helvetica-Bold",
            fontSize=16, textColor=GREEN, alignment=TA_CENTER),
        "insight":     ParagraphStyle("ins", fontName="Helvetica",
            fontSize=10, textColor=HexColor("#27500A"),
            backColor=LGREEN, leading=15, borderPadding=8),
        "table_head":  ParagraphStyle("th", fontName="Helvetica-Bold",
            fontSize=9, textColor=WHITE),
        "table_cell":  ParagraphStyle("tc", fontName="Helvetica",
            fontSize=9, textColor=DGREY),
    }


def build_report(farms: list, output_path: str,
                  brand_name: str = "Organic Brand",
                  district: str = "", state: str = "") -> str:
    """
    Build the full PDF report.

    Args:
        farms:       list of (SoilProfile, MittiResult) tuples
        output_path: where to save the PDF
        brand_name:  brand name shown on cover
        district:    district name for cover
        state:       state code for cover
    """
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=20*mm, bottomMargin=20*mm,
        title=f"MittiID Soil Provenance Report — {brand_name}",
        author="MittiID Platform",
    )

    S  = make_styles()
    story = []
    date_str = datetime.now().strftime("%B %d, %Y")
    W = 170*mm  # usable width

    # ── COVER PAGE ────────────────────────────────────────────────
    # Logo
    logo_path = Path("logo.png")
    if logo_path.exists():
        story.append(Image(str(logo_path), width=50*mm, height=50*mm))
    else:
        story.append(Paragraph("🌱 MittiID", S["cover_title"]))
    story.append(Spacer(1, 8*mm))

    story.append(Paragraph("SOIL PROVENANCE REPORT", S["cover_brand"]))
    story.append(Paragraph(
        f"Verified Soil Health Analysis<br/>{brand_name}",
        S["cover_title"]
    ))

    loc = f"{district}, {state}" if district else "India"
    story.append(Paragraph(f"{loc}  ·  {len(farms)} farms  ·  {date_str}", S["cover_sub"]))
    story.append(Spacer(1, 6*mm))
    story.append(HRFlowable(width=W, color=GREEN, thickness=2))
    story.append(Spacer(1, 6*mm))

    # Cover summary table
    scores     = [r.score for _, r in farms]
    avg_score  = round(sum(scores)/len(scores), 1)
    org_count  = sum(1 for _, r in farms if r.tier=="Organic")
    gold_count = sum(1 for _, r in farms if r.tier=="Gold")
    clean      = sum(1 for f, _ in farms if f.pesticide_residue < 0.5)

    cover_data = [
        [Paragraph("<b>Metric</b>", S["table_head"]),
         Paragraph("<b>Value</b>",  S["table_head"]),
         Paragraph("<b>Insight</b>",S["table_head"])],
        ["Average MittiScore", f"{avg_score} / 100",
         "Higher than 65% of Indian districts"],
        ["Organic tier farms", f"{org_count} of {len(farms)}",
         "Ready for premium organic market"],
        ["Gold tier farms",    f"{gold_count} of {len(farms)}",
         "Strong transition in progress"],
        ["Pesticide-free",     f"{clean} of {len(farms)}",
         "Zero detectable residue"],
        ["Report date",        date_str, "Data verified quarterly"],
    ]
    cover_table = Table(cover_data, colWidths=[55*mm, 40*mm, 75*mm])
    cover_table.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),  GREEN),
        ("TEXTCOLOR",     (0,0), (-1,0),  WHITE),
        ("FONTNAME",      (0,0), (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,-1), 9),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [WHITE, LGREY]),
        ("TEXTCOLOR",     (0,1), (-1,-1), DGREY),
        ("TOPPADDING",    (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("LEFTPADDING",   (0,0), (-1,-1), 8),
        ("GRID",          (0,0), (-1,-1), 0.25, BGREY),
        ("ROUNDEDCORNERS",[6]),
    ]))
    story.append(cover_table)
    story.append(Spacer(1, 6*mm))

    # What is MittiID box
    story.append(Paragraph("About this report", S["section"]))
    story.append(Paragraph(
        "This report is generated by <b>MittiID</b> — India's first soil identity platform. "
        "Each farm's MittiScore (0–100) is calculated from verified soil parameters including "
        "pesticide residue, organic carbon, pH, nitrogen, phosphorus, potassium, and satellite "
        "vegetation index (NDVI). Scores are independently verifiable at <b>mittid.streamlit.app</b>.",
        S["body"]
    ))
    story.append(Spacer(1, 4*mm))
    story.append(HRFlowable(width=W, color=BGREY, thickness=0.5))
    story.append(Spacer(1, 6*mm))

    # ── FARM PAGES ────────────────────────────────────────────────
    for idx, (farm, result) in enumerate(farms):
        story.append(Paragraph(
            f"Farm {idx+1} of {len(farms)} — {result.farm_id}",
            S["cover_brand"]
        ))
        story.append(Paragraph(
            f"{result.farmer_name} · {result.village}, {result.district}",
            S["section"]
        ))

        # Score + tier row
        tier_color = TIER_COLORS.get(result.tier, GREEN)
        tier_bg    = TIER_BG.get(result.tier, LGREEN)

        score_data = [[
            Paragraph(f"<b>{result.score}</b>", ParagraphStyle("sc",
                fontName="Helvetica-Bold", fontSize=40,
                textColor=tier_color, alignment=TA_CENTER)),
            Paragraph(f"<b>{result.tier}</b><br/>{result.tier_desc}",
                ParagraphStyle("td", fontName="Helvetica-Bold", fontSize=14,
                textColor=tier_color, leading=20)),
            Paragraph(f"Crop: <b>{farm.crop}</b><br/>"
                       f"Pesticide: <b>{farm.pesticide_residue} ppm</b><br/>"
                       f"Organic carbon: <b>{farm.organic_carbon}%</b>",
                ParagraphStyle("fi", fontName="Helvetica", fontSize=10,
                textColor=DGREY, leading=16)),
        ]]
        score_table = Table(score_data, colWidths=[30*mm, 70*mm, 70*mm])
        score_table.setStyle(TableStyle([
            ("BACKGROUND",   (0,0), (-1,-1), tier_bg),
            ("TOPPADDING",   (0,0), (-1,-1), 10),
            ("BOTTOMPADDING",(0,0), (-1,-1), 10),
            ("LEFTPADDING",  (0,0), (-1,-1), 10),
            ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
            ("ROUNDEDCORNERS",[8]),
        ]))
        story.append(score_table)
        story.append(Spacer(1, 4*mm))

        # Component breakdown table
        story.append(Paragraph("Soil parameter breakdown", S["section"]))

        # ICAR thresholds for context
        THRESHOLDS = {
            "pesticide_score":  ("Residue-free", "Trace residue", "High residue"),
            "organic_carbon":   ("Excellent OC", "Low OC",        "Very low OC"),
            "ph_suitability":   ("Ideal pH",      "Acceptable",    "Correction needed"),
            "nitrogen":         ("Adequate N",    "Moderate N",    "N deficient"),
            "phosphorus":       ("Adequate P",    "Moderate P",    "P deficient"),
            "potassium":        ("Adequate K",    "Moderate K",    "K deficient"),
            "ndvi_satellite":   ("Healthy canopy","Moderate crop", "Poor canopy"),
        }

        bd_header = [
            Paragraph("<b>Parameter</b>", S["table_head"]),
            Paragraph("<b>Score</b>",     S["table_head"]),
            Paragraph("<b>Bar</b>",       S["table_head"]),
            Paragraph("<b>Status</b>",    S["table_head"]),
        ]
        bd_rows = [bd_header]
        for param, val in result.breakdown.items():
            thresh = THRESHOLDS.get(param, ("Good","Fair","Poor"))
            if val >= 60:
                status = thresh[0]; sc = GREEN
            elif val >= 35:
                status = thresh[1]; sc = AMBER
            else:
                status = thresh[2]; sc = CORAL
            bd_rows.append([
                Paragraph(param.replace("_"," ").title(), S["table_cell"]),
                Paragraph(f"<b>{val}</b>/100", ParagraphStyle("v",
                    fontName="Helvetica-Bold", fontSize=9, textColor=sc)),
                score_bar_drawing(val, result.tier, width=80, height=12),
                Paragraph(status, ParagraphStyle("st", fontName="Helvetica",
                    fontSize=9, textColor=sc)),
            ])

        bd_table = Table(bd_rows, colWidths=[52*mm, 22*mm, 60*mm, 36*mm])
        bd_table.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,0),  GREEN),
            ("FONTSIZE",      (0,0), (-1,-1), 9),
            ("ROWBACKGROUNDS",(0,1), (-1,-1), [WHITE, LGREY]),
            ("TOPPADDING",    (0,0), (-1,-1), 5),
            ("BOTTOMPADDING", (0,0), (-1,-1), 5),
            ("LEFTPADDING",   (0,0), (-1,-1), 6),
            ("GRID",          (0,0), (-1,-1), 0.25, BGREY),
            ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ]))
        story.append(bd_table)
        story.append(Spacer(1, 4*mm))

        # Insight box
        story.append(Paragraph(
            f"<b>Key recommendation:</b> {result.insight}",
            S["insight"]
        ))
        story.append(Spacer(1, 4*mm))

        # Delta from last quarter
        if result.delta is not None:
            arrow   = "▲" if result.delta >= 0 else "▼"
            d_color = "#1D9E75" if result.delta >= 0 else "#D85A30"
            story.append(Paragraph(
                f"<font color='{d_color}'><b>{arrow} {abs(result.delta)} points</b></font> "
                f"improvement from last quarter — farm is actively improving.",
                S["body"]
            ))
            story.append(Spacer(1, 2*mm))

        # What was NOT used
        not_used = []
        if farm.pesticide_residue < 0.5:
            not_used.append("No synthetic pesticides detected")
        if farm.organic_carbon > 0.75:
            not_used.append("No chemical fertiliser dependence")
        if result.tier in ["Gold","Organic"]:
            not_used.append("No herbicides")
            not_used.append("No GMO seeds reported")
        if not_used:
            story.append(Paragraph("Verified absences", S["section"]))
            nu_data = [[Paragraph(f"✓  {item}", ParagraphStyle("nu",
                fontName="Helvetica", fontSize=9, textColor=HexColor("#27500A")))
                for item in not_used]]
            # wrap to 2 columns
            wrapped = []
            for i in range(0, len(not_used), 2):
                row = [Paragraph(f"✓  {not_used[i]}", ParagraphStyle("nu",
                    fontName="Helvetica", fontSize=9,
                    textColor=HexColor("#27500A")))]
                if i+1 < len(not_used):
                    row.append(Paragraph(f"✓  {not_used[i+1]}", ParagraphStyle("nu",
                        fontName="Helvetica", fontSize=9,
                        textColor=HexColor("#27500A"))))
                else:
                    row.append(Paragraph("", S["small"]))
                wrapped.append(row)
            nu_table = Table(wrapped, colWidths=[85*mm, 85*mm])
            nu_table.setStyle(TableStyle([
                ("BACKGROUND",   (0,0),(-1,-1), LGREEN),
                ("TOPPADDING",   (0,0),(-1,-1), 6),
                ("BOTTOMPADDING",(0,0),(-1,-1), 6),
                ("LEFTPADDING",  (0,0),(-1,-1), 10),
                ("ROUNDEDCORNERS",[6]),
            ]))
            story.append(nu_table)

        story.append(Spacer(1, 4*mm))
        story.append(HRFlowable(width=W, color=BGREY, thickness=0.5))
        story.append(Spacer(1, 4*mm))

    # ── CLOSING PAGE ──────────────────────────────────────────────
    story.append(Paragraph("About MittiID", S["section"]))
    story.append(Paragraph(
        "MittiID is India's first soil identity platform — built to bridge the trust gap "
        "between organic farmers and premium buyers. Every farm receives a unique Soil ID "
        "backed by verified biological data, giving brands the proof they need to command "
        "premium prices and giving consumers the transparency they demand.",
        S["body"]
    ))
    story.append(Spacer(1, 4*mm))

    closing_data = [
        ["Platform",   "mittid.streamlit.app"],
        ["Contact",    "hello@mittid.in"],
        ["Report date",date_str],
        ["Data source","ICAR Soil Health Card programme + satellite NDVI"],
        ["Verified by","MittiID Scoring Engine v1.0"],
    ]
    cl_table = Table(closing_data, colWidths=[50*mm, 120*mm])
    cl_table.setStyle(TableStyle([
        ("FONTNAME",      (0,0),(0,-1),  "Helvetica-Bold"),
        ("FONTNAME",      (1,0),(1,-1),  "Helvetica"),
        ("FONTSIZE",      (0,0),(-1,-1), 9),
        ("TEXTCOLOR",     (0,0),(-1,-1), DGREY),
        ("ROWBACKGROUNDS",(0,0),(-1,-1), [WHITE, LGREY]),
        ("TOPPADDING",    (0,0),(-1,-1), 5),
        ("BOTTOMPADDING", (0,0),(-1,-1), 5),
        ("LEFTPADDING",   (0,0),(-1,-1), 8),
        ("GRID",          (0,0),(-1,-1), 0.25, BGREY),
    ]))
    story.append(cl_table)
    story.append(Spacer(1, 6*mm))
    story.append(Paragraph(
        "© 2025 MittiID · All soil data verified quarterly · "
        "Not for redistribution without permission",
        S["footer"]
    ))

    doc.build(story)
    return output_path


def generate_single_farm(farm_id: str, brand_name: str = "Organic Brand",
                          output_path: str = None) -> str:
    farm = SAMPLE_FARMS.get(farm_id)
    if not farm:
        raise ValueError(f"Farm {farm_id} not found. Available: {list(SAMPLE_FARMS.keys())}")
    result = calculate(farm)
    out    = output_path or f"MittiID_Report_{farm_id}.pdf"
    return build_report([(farm, result)], out,
                         brand_name=brand_name,
                         district=farm.district, state=farm.state)


def generate_district_report(state: str, district: str,
                               brand_name: str = "Organic Brand",
                               output_path: str = None) -> str:
    """Generate a report for all sample farms in a district."""
    district_farms = [(f, calculate(f)) for f in SAMPLE_FARMS.values()
                      if f.state.upper() == state.upper()
                      or f.district.lower() == district.lower()]
    if not district_farms:
        district_farms = [(f, calculate(f)) for f in SAMPLE_FARMS.values()]
    out = output_path or f"MittiID_{district}_{state}.pdf"
    return build_report(district_farms, out,
                         brand_name=brand_name,
                         district=district, state=state)


# ── CLI ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MittiID PDF Report Generator")
    parser.add_argument("--farm",     default="",   help="Farm ID e.g. MP-IDR-033")
    parser.add_argument("--district", default="",   help="District name")
    parser.add_argument("--state",    default="MP", help="State code")
    parser.add_argument("--brand",    default="Prakriti Organics", help="Brand name")
    parser.add_argument("--output",   default="",   help="Output PDF path")
    args = parser.parse_args()

    print("\n" + "="*50)
    print("  MittiID — PDF Report Generator")
    print("="*50)

    if args.farm:
        out = generate_single_farm(
            args.farm,
            brand_name=args.brand,
            output_path=args.output or f"MittiID_{args.farm}.pdf"
        )
    elif args.district:
        out = generate_district_report(
            args.state, args.district,
            brand_name=args.brand,
            output_path=args.output or f"MittiID_{args.district}.pdf"
        )
    else:
        # Demo — generate all 3 sample farms
        results = [(f, calculate(f)) for f in SAMPLE_FARMS.values()]
        out = build_report(results, "MittiID_Demo_Report.pdf",
                            brand_name=args.brand,
                            district="MP / UP", state="India")

    print(f"\n  Report saved → {out}")
    print(f"  Open it to preview, then email it to your first brand.\n")
