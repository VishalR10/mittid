"""
qr_story.py — Consumer-facing QR story page (Flask)
deploy free on Vercel or Railway

pdf_report.py — PDF report generator for brand sales calls
"""

# ════════════════════════════════════════════════════════════════
# PART 1: qr_story.py  — run with: python qr_story.py
# ════════════════════════════════════════════════════════════════

from flask import Flask, render_template_string
from mittiscore import calculate, SoilProfile

app = Flask(__name__)

# Sample farm DB (replace with real DB later)
FARM_DB = {
    "MP-NMD-001": SoilProfile(
        "MP-NMD-001","Ramesh Patel","Sehore","Narmadapuram","MP","Soybean",
        6.8,0.72,180,22,210,0.4,ndvi=0.71,previous_score=54.2
    ),
    "MP-IDR-033": SoilProfile(
        "MP-IDR-033","Kavita Sharma","Ujjain","Indore","MP","Garlic",
        6.5,1.85,255,44,265,0.05,ndvi=0.83,previous_score=68.1
    ),
}

QR_PAGE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ result.farmer_name }} — MittiID Soil Story</title>
<style>
  * { box-sizing:border-box; margin:0; padding:0; }
  body { font-family: -apple-system, sans-serif; background:#f5f5f0;
         color:#1a1a1a; padding:20px; max-width:480px; margin:0 auto; }
  .header { background:#1D9E75; color:#fff; border-radius:14px;
            padding:24px; margin-bottom:16px; text-align:center; }
  .score  { font-size:64px; font-weight:700; line-height:1; }
  .tier   { font-size:18px; margin-top:4px; opacity:.9; }
  .card   { background:#fff; border-radius:14px; padding:20px;
            margin-bottom:12px; border:1px solid #e8e8e0; }
  .card h3 { font-size:13px; color:#6b6b60; text-transform:uppercase;
             letter-spacing:.6px; margin-bottom:10px; }
  .row    { display:flex; justify-content:space-between; align-items:center;
            padding:6px 0; border-bottom:1px solid #f0f0e8; }
  .row:last-child { border:none; }
  .param  { font-size:14px; color:#444; }
  .val    { font-weight:600; font-size:14px; }
  .good   { color:#1D9E75; }
  .ok     { color:#BA7517; }
  .poor   { color:#D85A30; }
  .bar-bg { background:#f0f0e8; border-radius:4px; height:6px;
            width:80px; overflow:hidden; display:inline-block; }
  .bar-fill { height:100%; border-radius:4px; background:#1D9E75; }
  .insight { background:#EAF3DE; border-radius:10px; padding:14px;
             font-size:14px; color:#27500A; margin-top:4px; }
  .not-used { display:flex; flex-wrap:wrap; gap:6px; }
  .tag { background:#EAF3DE; color:#27500A; font-size:12px;
         padding:4px 10px; border-radius:20px; }
  .footer { text-align:center; font-size:12px; color:#888;
            padding:20px 0 10px; }
</style>
</head>
<body>

<div class="header">
  <div style="font-size:13px;opacity:.8;margin-bottom:6px">VERIFIED SOIL IDENTITY</div>
  <div class="score">{{ result.score }}</div>
  <div class="tier">{{ result.tier }} tier · MittiScore</div>
  <div style="font-size:13px;margin-top:8px;opacity:.85">{{ result.tier_desc }}</div>
</div>

<div class="card">
  <h3>The farmer</h3>
  <div class="row"><span class="param">Name</span><span class="val">{{ result.farmer_name }}</span></div>
  <div class="row"><span class="param">Village</span><span class="val">{{ result.village }}</span></div>
  <div class="row"><span class="param">District</span><span class="val">{{ result.district }}</span></div>
  <div class="row"><span class="param">Crop</span><span class="val">{{ farm.crop }}</span></div>
  <div class="row"><span class="param">Farm ID</span><span class="val" style="font-size:12px;color:#888">{{ result.farm_id }}</span></div>
</div>

<div class="card">
  <h3>Soil health breakdown</h3>
  {% for key, val in result.breakdown.items() %}
  <div class="row">
    <span class="param">{{ key.replace('_',' ').title() }}</span>
    <div style="display:flex;align-items:center;gap:10px">
      <div class="bar-bg"><div class="bar-fill" style="width:{{ val }}%"></div></div>
      <span class="val {{ 'good' if val >= 60 else 'ok' if val >= 35 else 'poor' }}">{{ val }}</span>
    </div>
  </div>
  {% endfor %}
</div>

<div class="card">
  <h3>What was NOT used on this farm</h3>
  <div class="not-used">
    {% if farm.pesticide_residue < 0.5 %}<span class="tag">No synthetic pesticides</span>{% endif %}
    {% if farm.organic_carbon > 0.75 %}<span class="tag">No chemical fertilisers</span>{% endif %}
    <span class="tag">No GMO seeds</span>
    {% if result.tier in ['Gold','Organic'] %}<span class="tag">No herbicides</span>{% endif %}
  </div>
</div>

<div class="card">
  <h3>Improvement insight</h3>
  <div class="insight">{{ result.insight }}</div>
</div>

<div class="footer">
  Verified by MittiID · mittid.in<br>
  Scan date: today · Data updated quarterly
</div>

</body>
</html>
"""

@app.route("/farm/<farm_id>")
def farm_story(farm_id):
    farm = FARM_DB.get(farm_id)
    if not farm:
        return "Farm not found", 404
    result = calculate(farm)
    return render_template_string(QR_PAGE_HTML, farm=farm, result=result)

@app.route("/")
def index():
    return """
    <h2 style="font-family:sans-serif;padding:30px">MittiID QR Story Server</h2>
    <p style="font-family:sans-serif;padding:0 30px">
      Try: <a href="/farm/MP-NMD-001">/farm/MP-NMD-001</a> · 
           <a href="/farm/MP-IDR-033">/farm/MP-IDR-033</a>
    </p>"""


# ════════════════════════════════════════════════════════════════
# PART 2: PDF report generator
# pip install reportlab
# ════════════════════════════════════════════════════════════════

def generate_pdf_report(farm_id: str, output_path: str = None):
    """
    Generate a branded PDF report for a brand's sales call.
    Usage: generate_pdf_report("MP-IDR-033", "kavita_report.pdf")
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.colors import HexColor, white, black
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.units import mm
    from reportlab.lib.enums import TA_CENTER, TA_LEFT

    farm = FARM_DB.get(farm_id)
    if not farm:
        raise ValueError(f"Farm {farm_id} not found")

    result = calculate(farm)
    output_path = output_path or f"mittiscore_{farm_id}.pdf"

    GREEN  = HexColor("#1D9E75")
    LGTEEN = HexColor("#EAF3DE")
    DGREY  = HexColor("#2C2C2A")
    MGREY  = HexColor("#5F5E5A")
    LGREY  = HexColor("#F1EFE8")

    doc = SimpleDocTemplate(output_path, pagesize=A4,
                            leftMargin=20*mm, rightMargin=20*mm,
                            topMargin=20*mm, bottomMargin=20*mm)
    styles = getSampleStyleSheet()
    story  = []

    # Header
    header_data = [[
        Paragraph(f"<font color='white'><b>MittiID</b><br/>Soil Provenance Report</font>",
                  ParagraphStyle("h", fontName="Helvetica-Bold", fontSize=16,
                                 textColor=white, leading=22)),
        Paragraph(f"<font color='white'><b>{result.score} / 100</b><br/>"
                  f"{result.tier} Tier</font>",
                  ParagraphStyle("s", fontName="Helvetica-Bold", fontSize=20,
                                 textColor=white, alignment=TA_CENTER, leading=26)),
    ]]
    header_table = Table(header_data, colWidths=[120*mm, 50*mm])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), GREEN),
        ("TOPPADDING",  (0,0), (-1,-1), 12),
        ("BOTTOMPADDING",(0,0),(-1,-1), 12),
        ("LEFTPADDING", (0,0), (-1,-1), 14),
        ("ROUNDEDCORNERS", [8]),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 8*mm))

    # Farm details
    story.append(Paragraph("Farm details",
                 ParagraphStyle("sh", fontName="Helvetica-Bold", fontSize=11,
                                textColor=DGREY, spaceAfter=4)))
    detail_data = [
        ["Farmer", result.farmer_name, "District", result.district],
        ["Village", result.village,    "State",    farm.state],
        ["Crop",    farm.crop,         "Farm ID",  result.farm_id],
    ]
    dt = Table(detail_data, colWidths=[30*mm, 60*mm, 30*mm, 50*mm])
    dt.setStyle(TableStyle([
        ("FONTNAME",  (0,0), (-1,-1), "Helvetica"),
        ("FONTNAME",  (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTNAME",  (2,0), (2,-1), "Helvetica-Bold"),
        ("FONTSIZE",  (0,0), (-1,-1), 9),
        ("TEXTCOLOR", (0,0), (-1,-1), DGREY),
        ("TEXTCOLOR", (0,0), (0,-1), MGREY),
        ("TEXTCOLOR", (2,0), (2,-1), MGREY),
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [white, LGREY]),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ]))
    story.append(dt)
    story.append(Spacer(1, 6*mm))

    # Score breakdown
    story.append(Paragraph("Soil health breakdown",
                 ParagraphStyle("sh2", fontName="Helvetica-Bold", fontSize=11,
                                textColor=DGREY, spaceAfter=4)))
    bd_data = [["Parameter", "Score", "Status"]]
    for k, v in result.breakdown.items():
        status = "Excellent" if v >= 75 else "Good" if v >= 50 else "Fair" if v >= 30 else "Needs attention"
        bd_data.append([k.replace("_"," ").title(), f"{v}/100", status])

    bd = Table(bd_data, colWidths=[80*mm, 30*mm, 60*mm])
    bd.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0), GREEN),
        ("TEXTCOLOR",     (0,0), (-1,0), white),
        ("FONTNAME",      (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTNAME",      (0,1), (-1,-1), "Helvetica"),
        ("FONTSIZE",      (0,0), (-1,-1), 9),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [white, LGREY]),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("GRID",          (0,0), (-1,-1), 0.25, HexColor("#e0e0d8")),
    ]))
    story.append(bd)
    story.append(Spacer(1, 6*mm))

    # Insight box
    insight_para = Paragraph(
        f"<b>Key recommendation:</b> {result.insight}",
        ParagraphStyle("ins", fontName="Helvetica", fontSize=9,
                       textColor=HexColor("#27500A"), backColor=LGTEEN,
                       borderPadding=8, leading=14)
    )
    story.append(insight_para)
    story.append(Spacer(1, 6*mm))

    # Footer
    story.append(Paragraph(
        "Report generated by MittiID · mittid.in · Data verified quarterly",
        ParagraphStyle("ft", fontName="Helvetica", fontSize=8,
                       textColor=MGREY, alignment=TA_CENTER)
    ))

    doc.build(story)
    return output_path


# ── Run Flask dev server ──────────────────────────────────────────
if __name__ == "__main__":
    # Generate a sample PDF
    try:
        path = generate_pdf_report("MP-IDR-033", "/home/claude/mittiscore_kavita.pdf")
        print(f"PDF report generated: {path}")
    except Exception as e:
        print(f"PDF generation: {e}")

    print("\nStarting QR story server on http://localhost:5000")
    print("Try: http://localhost:5000/farm/MP-NMD-001")
    app.run(debug=True, port=5000)
