"""
PDF Generator v5 — SACS and TCC matching exact client templates
"""
import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import HexColor, white, black
import io

PAGE_W, PAGE_H = letter  # 612 x 792

GREEN_INFLOW  = HexColor('#43A047')
RED_OUTFLOW   = HexColor('#E53935')
BLUE_RESERVE  = HexColor('#1565C0')
BLUE_FICA     = HexColor('#90CAF9')
BLUE_INVEST   = HexColor('#1A237E')
CLIENT_GREEN  = HexColor('#558B2F')
GRAY_BOX      = HexColor('#BDBDBD')
GRAY_LIGHT    = HexColor('#F5F5F5')
NAVY          = HexColor('#0A2540')
DARK_TEXT     = HexColor('#212121')
MID_GRAY      = HexColor('#757575')
LIABILITY_BG  = HexColor('#FFF9C4')
OVAL_BORDER   = HexColor('#424242')
RED_TEXT      = HexColor('#C62828')

def fmt(val):
    try: return f"${val:,.2f}"
    except: return "$0.00"

def calc_age(dob_str):
    if not dob_str: return ''
    try: return str(datetime.date.today().year - int(dob_str.split('-')[0]))
    except: return ''

def draw_circle(c, cx, cy, r, fill_color):
    c.setFillColor(HexColor('#00000018'))
    c.circle(cx+3, cy-3, r, fill=1, stroke=0)
    c.setFillColor(fill_color)
    c.setStrokeColor(white)
    c.setLineWidth(2.5)
    c.circle(cx, cy, r, fill=1, stroke=1)

def draw_oval(c, cx, cy, w, h, fill_color, stroke_color=OVAL_BORDER):
    c.setFillColor(fill_color)
    c.setStrokeColor(stroke_color)
    c.setLineWidth(1.2)
    c.ellipse(cx-w/2, cy-h/2, cx+w/2, cy+h/2, fill=1, stroke=1)

def hdr(c, client_name, today, title):
    c.setFillColor(NAVY)
    c.rect(0, PAGE_H-36, PAGE_W, 36, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 10); c.setFillColor(white)
    c.drawString(36, PAGE_H-23, "WINDBROOK SOLUTIONS")
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(PAGE_W/2, PAGE_H-23, title)
    c.setFont("Helvetica", 9)
    c.drawRightString(PAGE_W-36, PAGE_H-23, today)
    c.setFillColor(GRAY_LIGHT)
    c.rect(0, PAGE_H-56, PAGE_W, 20, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 11); c.setFillColor(NAVY)
    c.drawCentredString(PAGE_W/2, PAGE_H-49, client_name)

def ftr(c, today):
    c.setFillColor(GRAY_LIGHT)
    c.rect(0, 0, PAGE_W, 22, fill=1, stroke=0)
    c.setFont("Helvetica", 7.5); c.setFillColor(MID_GRAY)
    c.drawString(36, 7, "Windbrook Solutions  |  Confidential Financial Report")
    c.drawRightString(PAGE_W-36, 7, f"Generated: {today}")


# ═══════════════════════════════════════════════════════════════
# SACS
# ═══════════════════════════════════════════════════════════════
def generate_sacs_pdf(client, totals):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    today = datetime.date.today().strftime('%B %d, %Y')
    inflow  = client['monthly_inflow']
    outflow = client['monthly_outflow']
    excess  = totals['excess']
    reserve_target = totals['reserve_target']
    reserve_bal = client.get('private_reserve_balance', 0)
    schwab_bal  = client.get('schwab_investment_balance', 0)
    deductibles = client.get('insurance_deductibles', 0)

    # PAGE 1
    hdr(c, client['name'], today, "Simple Automated Cashflow System (SACS)")

    # Page title area
    c.setFont("Helvetica-Bold", 24); c.setFillColor(GREEN_INFLOW)
    c.drawString(44, PAGE_H-90, "$")
    c.setFont("Helvetica-Bold", 15); c.setFillColor(DARK_TEXT)
    c.drawCentredString(PAGE_W/2, PAGE_H-80, "Simple Automated Cashflow System (SACS)")
    c.setFont("Helvetica", 11); c.setFillColor(MID_GRAY)
    c.drawCentredString(PAGE_W/2, PAGE_H-96, "Client Example")

    # Salary lines top-left
    c.setFont("Helvetica", 8); c.setFillColor(GREEN_INFLOW)
    c.drawString(44, PAGE_H-112, f"${inflow:,.0f} - {client.get('c1_name','Client 1')}")
    if client.get('c2_name'):
        c.drawString(44, PAGE_H-124, f"${outflow:,.0f} - {client.get('c2_name','Client 2')}")

    # X = Monthly Expenses top-right
    c.setFont("Helvetica", 8); c.setFillColor(DARK_TEXT)
    c.drawRightString(PAGE_W-44, PAGE_H-112, "X = Monthly")
    c.drawRightString(PAGE_W-44, PAGE_H-124, "Expenses")

    # Circle layout — bigger and better spaced
    r = 78
    left_cx  = 158
    right_cx = PAGE_W - 158
    top_cy   = PAGE_H - 300
    bot_cx   = PAGE_W / 2
    bot_cy   = PAGE_H - 498

    # Green down arrow into Inflow (top-left corner arrow)
    c.setFillColor(GREEN_INFLOW)
    p = c.beginPath()
    p.moveTo(left_cx - r + 15, top_cy + r + 45)
    p.lineTo(left_cx - r + 35, top_cy + r + 15)
    p.lineTo(left_cx - r + 22, top_cy + r + 10)
    p.close()
    c.drawPath(p, fill=1, stroke=0)

    # INFLOW circle
    draw_circle(c, left_cx, top_cy, r, GREEN_INFLOW)
    c.setFont("Helvetica-Bold", 15); c.setFillColor(white)
    c.drawCentredString(left_cx, top_cy + 34, "INFLOW")
    # White amount box
    bw, bh = 118, 30
    c.setFillColor(white); c.roundRect(left_cx-bw/2, top_cy-2, bw, bh, 4, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 16); c.setFillColor(DARK_TEXT)
    c.drawCentredString(left_cx, top_cy+14, fmt(inflow))
    # Floor
    c.setStrokeColor(white); c.setLineWidth(1)
    c.line(left_cx-55, top_cy-30, left_cx+55, top_cy-30)
    c.setFont("Helvetica", 8); c.setFillColor(white)
    c.drawCentredString(left_cx, top_cy-43, "$1,000 Floor")

    # OUTFLOW circle
    draw_circle(c, right_cx, top_cy, r, RED_OUTFLOW)
    c.setFont("Helvetica-Bold", 15); c.setFillColor(white)
    c.drawCentredString(right_cx, top_cy + 34, "OUTFLOW")
    c.setFillColor(white); c.roundRect(right_cx-bw/2, top_cy-2, bw, bh, 4, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 16); c.setFillColor(DARK_TEXT)
    c.drawCentredString(right_cx, top_cy+14, fmt(outflow))
    c.setStrokeColor(white); c.setLineWidth(1)
    c.line(right_cx-55, top_cy-30, right_cx+55, top_cy-30)
    c.setFont("Helvetica", 8); c.setFillColor(white)
    c.drawCentredString(right_cx, top_cy-43, "$1,000 Floor")

    # Arrow box between circles — ABOVE circle midpoint so it doesn't overlap amount box
    ax1 = left_cx + r + 6
    ax2 = right_cx - r - 6
    arrow_y = top_cy + 16  # above center
    ab_h = 24
    c.setFillColor(RED_OUTFLOW)
    c.roundRect(ax1, arrow_y - ab_h/2, ax2-ax1, ab_h, 5, fill=1, stroke=0)
    # Arrowhead
    c.setFillColor(RED_OUTFLOW)
    p = c.beginPath()
    p.moveTo(ax2+12, arrow_y); p.lineTo(ax2, arrow_y+8); p.lineTo(ax2, arrow_y-8)
    p.close(); c.drawPath(p, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 8); c.setFillColor(white)
    c.drawCentredString((ax1+ax2)/2, arrow_y+4, f"X = {fmt(outflow)}/month*")
    c.setFont("Helvetica", 7); c.setFillColor(white)
    c.drawCentredString((ax1+ax2)/2, arrow_y-10, "Automated transfer on the 28th")

    # Black line from Outflow down then left toward reserve
    elbow_y = top_cy - r - 14
    c.setStrokeColor(DARK_TEXT); c.setLineWidth(1.5)
    c.line(right_cx, top_cy-r, right_cx, elbow_y)
    c.line(right_cx, elbow_y, bot_cx+r+10, elbow_y)

    # Blue elbow arrow from Inflow → down → Private Reserve
    elbow_x = left_cx + 18
    c.setStrokeColor(BLUE_RESERVE); c.setFillColor(BLUE_RESERVE); c.setLineWidth(2)
    # Vertical segment
    c.line(elbow_x, top_cy-r, elbow_x, bot_cy+r+10)
    # Arrowhead pointing down
    p = c.beginPath()
    p.moveTo(elbow_x, bot_cy+r); p.lineTo(elbow_x-7, bot_cy+r+12); p.lineTo(elbow_x+7, bot_cy+r+12)
    p.close(); c.drawPath(p, fill=1, stroke=0)
    # Label
    c.setFont("Helvetica-Bold", 8); c.setFillColor(BLUE_RESERVE)
    c.drawString(elbow_x+5, (top_cy-r + bot_cy+r)//2 + 6, f"${excess:,.0f}/mo*")

    # PRIVATE RESERVE circle
    draw_circle(c, bot_cx, bot_cy, r, BLUE_RESERVE)
    c.setFont("Helvetica-Bold", 13); c.setFillColor(white)
    c.drawCentredString(bot_cx, bot_cy + 30, "PRIVATE")
    c.drawCentredString(bot_cx, bot_cy + 15, "RESERVE")
    # Coin stack symbol instead of emoji (emoji don't render in all PDF viewers)
    c.setFillColor(HexColor('#FFD54F'))
    c.circle(bot_cx, bot_cy-6, 10, fill=1, stroke=0)
    c.setFillColor(HexColor('#F9A825'))
    c.circle(bot_cx-8, bot_cy-10, 8, fill=1, stroke=0)
    c.circle(bot_cx+8, bot_cy-10, 8, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 9); c.setFillColor(DARK_TEXT)
    c.drawCentredString(bot_cx, bot_cy-9, "$")
    c.setFont("Helvetica", 8); c.setFillColor(HexColor('#BBDEFB'))
    c.drawCentredString(bot_cx, bot_cy - 34, f"${excess:,.0f}/mo*")

    # MONTHLY CASHFLOW label
    c.setFont("Helvetica-Bold", 11); c.setFillColor(DARK_TEXT)
    c.drawCentredString(PAGE_W/2, bot_cy - r - 22, "MONTHLY  CASHFLOW")

    ftr(c, today)
    c.showPage()

    # PAGE 2 — Long term cashflow
    hdr(c, client['name'], today, "Simple Automated Cashflow System (SACS)")
    c.setFont("Helvetica-Bold", 14); c.setFillColor(DARK_TEXT)
    c.drawCentredString(PAGE_W/2, PAGE_H-80, "Simple Automated Cashflow System (SACS)")

    # Dashed center line
    c.setStrokeColor(HexColor('#BDBDBD')); c.setDash(5,4); c.setLineWidth(1)
    c.line(PAGE_W/2, PAGE_H-108, PAGE_W/2, PAGE_H-570); c.setDash()

    r2 = 88
    fica_cx = PAGE_W/2 - 130
    inv_cx  = PAGE_W/2 + 130
    cy2 = PAGE_H - 340

    # FICA circle — light blue
    draw_circle(c, fica_cx, cy2, r2, BLUE_FICA)
    c.setFont("Helvetica-Bold", 12); c.setFillColor(DARK_TEXT)
    c.drawCentredString(fica_cx, cy2+52, "FICA")
    c.drawCentredString(fica_cx, cy2+37, "ACCOUNT")
    c.setFillColor(white); c.roundRect(fica_cx-58, cy2+8, 116, 26, 4, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 13); c.setFillColor(DARK_TEXT)
    c.drawCentredString(fica_cx, cy2+22, fmt(reserve_bal))
    c.setFont("Helvetica", 8); c.setFillColor(DARK_TEXT)
    c.drawCentredString(fica_cx, cy2-18, "6X Monthly Expenses + Deductibles")

    # INVESTMENT circle — dark navy
    draw_circle(c, inv_cx, cy2, r2, BLUE_INVEST)
    c.setFont("Helvetica-Bold", 12); c.setFillColor(white)
    c.drawCentredString(inv_cx, cy2+52, "INVESTMENT")
    c.drawCentredString(inv_cx, cy2+37, "ACCOUNT")
    c.setFillColor(white); c.roundRect(inv_cx-58, cy2+8, 116, 26, 4, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 13); c.setFillColor(DARK_TEXT)
    c.drawCentredString(inv_cx, cy2+22, fmt(schwab_bal)+"+")
    c.setFont("Helvetica", 8); c.setFillColor(white)
    c.drawCentredString(inv_cx, cy2-18, "Remainder")

    # Double arrow
    gap1 = fica_cx + r2 + 4
    gap2 = inv_cx  - r2 - 4
    c.setStrokeColor(BLUE_RESERVE); c.setFillColor(BLUE_RESERVE); c.setLineWidth(2.5)
    c.line(gap1, cy2, gap2, cy2)
    for tip_x, dir in [(gap2+10, 1), (gap1-10, -1)]:
        p = c.beginPath()
        p.moveTo(tip_x, cy2)
        p.lineTo(tip_x - dir*10, cy2+6)
        p.lineTo(tip_x - dir*10, cy2-6)
        p.close(); c.drawPath(p, fill=1, stroke=0)

    c.setFont("Helvetica-Bold", 11); c.setFillColor(DARK_TEXT)
    c.drawCentredString(PAGE_W/2, cy2-r2-28, "LONG TERM  CASHFLOW")
    c.setFont("Helvetica-Oblique", 9); c.setFillColor(MID_GRAY)
    c.drawCentredString(PAGE_W/2, cy2-r2-44, "(Magnified Private Reserve Cashflow)")

    # Formula box
    fy = cy2 - r2 - 104
    c.setFillColor(HexColor('#E3F2FD'))
    c.roundRect(60, fy, PAGE_W-120, 46, 6, fill=1, stroke=0)
    c.setStrokeColor(BLUE_RESERVE); c.setLineWidth(2)
    c.line(60, fy, 60, fy+46)
    c.setFont("Helvetica-Bold", 10); c.setFillColor(NAVY)
    c.drawString(76, fy+30, "Private Reserve Target Formula:")
    c.setFont("Helvetica", 10); c.setFillColor(DARK_TEXT)
    c.drawString(76, fy+14,
        f"(6 × {fmt(outflow)}/mo)  +  {fmt(deductibles)} deductibles  =  {fmt(reserve_target)}")

    ftr(c, today)
    c.showPage()
    c.save()
    return buf.getvalue()


# ═══════════════════════════════════════════════════════════════
# TCC
# ═══════════════════════════════════════════════════════════════
def generate_tcc_pdf(client, accounts, totals, ret_c1, ret_c2, non_ret, trust, liabilities):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    today = datetime.date.today().strftime('%B %d, %Y')
    hdr(c, client['name'], today, "Total Client Chart")

    age1 = calc_age(client.get('c1_dob',''))
    age2 = calc_age(client.get('c2_dob',''))
    mid_x = PAGE_W / 2

    # ── Header info ──────────────────────────────────────────────
    hy = PAGE_H - 74
    c.setFont("Helvetica-Bold", 8); c.setFillColor(DARK_TEXT)
    c.drawString(36, hy,    f"NAME   {client['name']}")
    c.drawString(36, hy-13, f"DATE    {today}")

    # Grand total box
    gt_w, gt_h = 155, 34
    c.setFillColor(GRAY_BOX)
    c.roundRect(mid_x-gt_w/2, hy-gt_h+4, gt_w, gt_h, 4, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 7.5); c.setFillColor(DARK_TEXT)
    c.drawCentredString(mid_x, hy-4, "GRAND TOTAL")
    c.setFont("Helvetica-Bold", 13)
    c.drawCentredString(mid_x, hy-18, fmt(totals['net_worth']))

    # ── Layout lines ─────────────────────────────────────────────
    top_y   = hy - 46
    horiz_y = PAGE_H - 390    # retirement / non-retirement divider — moved up
    bot_y   = 36

    c.setStrokeColor(HexColor('#9E9E9E')); c.setLineWidth(0.8)
    c.line(mid_x, top_y, mid_x, bot_y)      # vertical center
    c.line(36, horiz_y, PAGE_W-36, horiz_y) # horizontal divider

    # Section labels on divider
    c.setFont("Helvetica-Bold", 7); c.setFillColor(MID_GRAY)
    c.drawString(38, horiz_y+3, "NON")
    c.drawString(38, horiz_y-8, "RETIREMENT")
    c.drawRightString(PAGE_W-38, horiz_y+3, "NON")
    c.drawRightString(PAGE_W-38, horiz_y-8, "RETIREMENT")

    # ── Client ovals ─────────────────────────────────────────────
    c1x = mid_x / 2          # ~153
    c2x = mid_x + mid_x / 2  # ~459
    ov_cy = top_y - 38
    ow, oh = 98, 50

    for cx, name, age, dob, ssn in [
        (c1x, client.get('c1_name',''), age1, client.get('c1_dob',''), client.get('c1_ssn','')),
        (c2x, client.get('c2_name',''), age2, client.get('c2_dob',''), client.get('c2_ssn',''))
    ]:
        draw_oval(c, cx, ov_cy, ow, oh, CLIENT_GREEN, HexColor('#33691E'))
        c.setFont("Helvetica-Bold", 8.5); c.setFillColor(white)
        c.drawCentredString(cx, ov_cy+11, name)
        c.setFont("Helvetica", 7); c.setFillColor(white)
        c.drawCentredString(cx, ov_cy+0,  f"Age: {age}")
        c.drawCentredString(cx, ov_cy-10, f"DOB: {dob}")
        c.drawCentredString(cx, ov_cy-20, f"SSN: ****{ssn}")

    # ── Retirement total boxes ────────────────────────────────────
    ret_box_y = ov_cy - oh/2 - 22
    rb_w = 140
    for cx, label, val in [
        (c1x, "Client 1 Retirement Only", fmt(totals['c1_retirement'])),
        (c2x, "Client 2 Retirement Only", fmt(totals['c2_retirement']))
    ]:
        c.setFillColor(GRAY_BOX)
        c.roundRect(cx-rb_w/2, ret_box_y-20, rb_w, 22, 3, fill=1, stroke=0)
        c.setFont("Helvetica-Bold", 6.5); c.setFillColor(DARK_TEXT)
        c.drawCentredString(cx, ret_box_y-6, label)
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(cx, ret_box_y-17, val)

    # ── Liabilities box — center between client ovals ─────────────
    lib_box_cx = mid_x
    lib_top    = ov_cy + oh/2 - 6
    lib_lines  = []
    for lib in liabilities:
        lib_lines.append((lib['account_name'][:20], fmt(lib['balance'])))
        if lib.get('interest_rate'):
            lib_lines.append(("", lib['interest_rate']))
    lib_h = 22 + len(lib_lines) * 12 + 18
    lib_y_top = ov_cy + oh/2 - 4
    c.setFillColor(LIABILITY_BG); c.setStrokeColor(HexColor('#F9A825')); c.setLineWidth(1)
    c.roundRect(lib_box_cx-62, lib_y_top-lib_h, 124, lib_h, 4, fill=1, stroke=1)
    c.setFont("Helvetica-Bold", 7.5); c.setFillColor(DARK_TEXT)
    c.drawCentredString(lib_box_cx, lib_y_top-11, "Liabilities:")
    row_y = lib_y_top - 22
    for name, val in lib_lines:
        c.setFont("Helvetica", 6.5)
        if name:
            c.drawString(lib_box_cx-58, row_y, name)
            c.drawRightString(lib_box_cx+58, row_y, val)
        else:
            c.setFillColor(MID_GRAY)
            c.drawString(lib_box_cx-50, row_y, val)
            c.setFillColor(DARK_TEXT)
        row_y -= 12
    c.setFont("Helvetica-Bold", 7); c.setFillColor(RED_TEXT)
    c.drawCentredString(lib_box_cx, row_y-4, f"Total: {fmt(totals['liabilities'])}")

    # ── Retirement account ovals ──────────────────────────────────
    # Columns positioned well inside page margins
    col1 = 90
    col2 = PAGE_W - 90
    acc_w, acc_h = 116, 58

    acc_y1 = ret_box_y - 40
    for acc in ret_c1:
        draw_oval(c, col1, acc_y1, acc_w, acc_h, white, OVAL_BORDER)
        _acc_oval(c, col1, acc_y1, acc)
        acc_y1 -= acc_h + 5

    acc_y2 = ret_box_y - 40
    for acc in ret_c2:
        draw_oval(c, col2, acc_y2, acc_w, acc_h, white, OVAL_BORDER)
        _acc_oval(c, col2, acc_y2, acc)
        acc_y2 -= acc_h + 5

    # ── Non-retirement section ────────────────────────────────────
    nr_start_y = horiz_y - 22

    # Trust oval — center
    if trust:
        ta = trust[0]
        trust_cx, trust_cy = mid_x, nr_start_y - 42
        draw_oval(c, trust_cx, trust_cy, 134, 62, white, HexColor('#795548'))
        c.setFont("Helvetica-Bold", 7.5); c.setFillColor(DARK_TEXT)
        name_parts = ta['account_name']
        if len(name_parts) > 18:
            words = name_parts.split()
            mid2 = len(words)//2
            c.drawCentredString(trust_cx, trust_cy+16, ' '.join(words[:mid2]))
            c.drawCentredString(trust_cx, trust_cy+6,  ' '.join(words[mid2:]))
        else:
            c.drawCentredString(trust_cx, trust_cy+12, name_parts)
        if ta.get('property_address'):
            c.setFont("Helvetica", 6.5); c.setFillColor(MID_GRAY)
            c.drawCentredString(trust_cx, trust_cy-4, ta['property_address'][:24])
        c.setFont("Helvetica-Bold", 9); c.setFillColor(HexColor('#4E342E'))
        c.drawCentredString(trust_cx, trust_cy-16, fmt(ta['balance']))
        c.setFont("Helvetica", 6.5); c.setFillColor(MID_GRAY)
        c.drawCentredString(trust_cx, trust_cy-27, "Zillow Zestimate")

    nr_left  = non_ret[0::2]
    nr_right = non_ret[1::2]
    nr_aw, nr_ah = 116, 56

    ly = nr_start_y - 30
    for acc in nr_left:
        draw_oval(c, col1, ly, nr_aw, nr_ah, white, OVAL_BORDER)
        _acc_oval(c, col1, ly, acc)
        ly -= nr_ah + 7

    ry = nr_start_y - 30
    for acc in nr_right:
        draw_oval(c, col2, ry, nr_aw, nr_ah, white, OVAL_BORDER)
        _acc_oval(c, col2, ry, acc)
        ry -= nr_ah + 7

    # Non-retirement total box
    nr_bot = min(ly, ry) - 14
    if nr_bot < 50: nr_bot = 50
    nr_box_w = 175
    c.setFillColor(GRAY_BOX)
    c.roundRect(mid_x-nr_box_w/2, nr_bot-24, nr_box_w, 26, 3, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 7.5); c.setFillColor(DARK_TEXT)
    c.drawCentredString(mid_x, nr_bot-6, "NON RETIREMENT TOTAL")
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(mid_x, nr_bot-19, fmt(totals['non_retirement']))

    c.setFont("Helvetica-Oblique", 6.5); c.setFillColor(RED_TEXT)
    c.drawCentredString(mid_x, nr_bot-32,
        "* indicates we do not have up to date information")

    ftr(c, today)
    c.showPage()
    c.save()
    return buf.getvalue()


def _acc_oval(c, cx, cy, acc):
    """Account content inside oval."""
    c.setFont("Helvetica-Bold", 6.5); c.setFillColor(DARK_TEXT)
    c.drawCentredString(cx, cy+20, "ACCT #")

    # Name — always split into max 2 lines of 12 chars each
    name = acc['account_name']
    words = name.split()
    if len(name) <= 13:
        lines = [name]
    elif len(words) == 2:
        lines = words
    elif len(words) >= 3:
        mid = (len(words) + 1) // 2
        lines = [' '.join(words[:mid]), ' '.join(words[mid:])]
    else:
        lines = [name[:13], name[13:26]]

    c.setFont("Helvetica-Bold", 7)
    if len(lines) == 1:
        c.drawCentredString(cx, cy+10, lines[0])
        name_bot = cy+10
    else:
        c.drawCentredString(cx, cy+12, lines[0])
        c.drawCentredString(cx, cy+3,  lines[1])
        name_bot = cy+3

    if acc.get('last_four'):
        c.setFont("Helvetica", 6.5); c.setFillColor(MID_GRAY)
        c.drawCentredString(cx, name_bot-10, f"****{acc['last_four']}")
        bal_y = name_bot - 21
    else:
        bal_y = name_bot - 12

    c.setFont("Helvetica-Bold", 9); c.setFillColor(DARK_TEXT)
    c.drawCentredString(cx, bal_y, fmt(acc['balance']))

    if acc.get('cash_balance') and acc['cash_balance'] > 0:
        c.setFont("Helvetica", 6); c.setFillColor(MID_GRAY)
        c.drawCentredString(cx, bal_y-10, f"${acc['cash_balance']:,.0f} Cash")
