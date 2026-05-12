# Requirements: pip install python-pptx
"""
Generate a professionally formatted 12-slide PowerPoint presentation:
  "Rethinking SB 375 — Public Audience Edition"

Design system:
  Background ......... #1B3A2F  (dark forest green)
  Primary text ........ #F5E6D3  (cream / off-white)
  Accent headings .... #E8967A  (coral / salmon)
  Secondary accent ... #4A9B8E  (teal)
  Card backgrounds ... #254D40  (lighter green)

All speaker notes go into the Notes pane; nothing is displayed on the
slide itself except title, headline, body bullets, content boxes, and
image/chart placeholders.
"""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn
import os

# ── Design tokens ───────────────────────────────────────────────────────
BG_COLOR       = RGBColor(0x1B, 0x3A, 0x2F)
CREAM          = RGBColor(0xF5, 0xE6, 0xD3)
CORAL          = RGBColor(0xE8, 0x96, 0x7A)
TEAL           = RGBColor(0x4A, 0x9B, 0x8E)
CARD_BG        = RGBColor(0x25, 0x4D, 0x40)
DARK_CARD_BG   = RGBColor(0x1E, 0x40, 0x35)
PLACEHOLDER_BG = RGBColor(0x1E, 0x40, 0x35)
PLACEHOLDER_BORDER = RGBColor(0x4A, 0x9B, 0x8E)

TITLE_FONT   = "Georgia"
BODY_FONT    = "Calibri"
TITLE_SIZE   = Pt(34)
HEADLINE_SIZE = Pt(20)
BODY_SIZE    = Pt(18)
SMALL_SIZE   = Pt(16)
CARD_TITLE_SIZE = Pt(18)
CARD_BODY_SIZE  = Pt(14)
NOTE_FONT    = "Calibri"

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)

# Generous margins
LEFT_MARGIN  = Inches(0.8)
RIGHT_MARGIN = Inches(0.8)
CONTENT_W    = SLIDE_W - LEFT_MARGIN - RIGHT_MARGIN


# ── Helper functions ────────────────────────────────────────────────────

def set_slide_bg(slide, color):
    """Set a solid-fill background on a slide."""
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_textbox(slide, left, top, width, height,
                text="", font_name=BODY_FONT, font_size=BODY_SIZE,
                font_color=CREAM, bold=False, alignment=PP_ALIGN.LEFT,
                word_wrap=True):
    """Add a textbox with a single run of styled text and return (shape, tf)."""
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = word_wrap
    p = tf.paragraphs[0]
    p.alignment = alignment
    run = p.add_run()
    run.text = text
    run.font.name = font_name
    run.font.size = font_size
    run.font.color.rgb = font_color
    run.font.bold = bold
    return txBox, tf


def add_title(slide, text, top=Inches(0.35)):
    """Add the slide title in coral accent at the top."""
    add_textbox(slide, LEFT_MARGIN, top, CONTENT_W, Inches(1.0),
                text=text, font_name=TITLE_FONT, font_size=TITLE_SIZE,
                font_color=CORAL, bold=True)


def add_headline(slide, text, top=Inches(1.25)):
    """Add a one-sentence headline takeaway below the title."""
    add_textbox(slide, LEFT_MARGIN, top, CONTENT_W, Inches(0.85),
                text=text, font_name=BODY_FONT, font_size=HEADLINE_SIZE,
                font_color=CREAM, bold=True)


def add_bullets(slide, items, left=None, top=Inches(2.35), width=None,
                height=None, font_size=BODY_SIZE, font_color=CREAM,
                line_spacing=1.5):
    """Add bullet-pointed text body."""
    if left is None:
        left = LEFT_MARGIN
    if width is None:
        width = CONTENT_W
    if height is None:
        height = Inches(4.5)

    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True

    for i, item in enumerate(items):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.space_after = Pt(6)
        p.line_spacing = line_spacing
        p.level = 0
        run = p.add_run()
        run.text = f"•  {item}"
        run.font.name = BODY_FONT
        run.font.size = font_size
        run.font.color.rgb = font_color
    return txBox, tf


def add_card(slide, left, top, width, height, title_text, body_text,
             title_color=TEAL, body_color=CREAM, card_color=CARD_BG):
    """Add a rounded-rectangle card with a title and body text."""
    card = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height
    )
    card.fill.solid()
    card.fill.fore_color.rgb = card_color
    card.line.fill.background()  # no border
    # Adjust corner rounding — set to a gentle radius
    card.adjustments[0] = 0.05

    # Title inside card
    title_top = top + Inches(0.2)
    tb_title, _ = add_textbox(
        slide, left + Inches(0.25), title_top,
        width - Inches(0.5), Inches(0.4),
        text=title_text, font_name=BODY_FONT, font_size=CARD_TITLE_SIZE,
        font_color=title_color, bold=True
    )

    # Body inside card
    body_top = title_top + Inches(0.45)
    # Split body_text into lines and build paragraphs
    txBox = slide.shapes.add_textbox(
        left + Inches(0.25), body_top,
        width - Inches(0.5), height - Inches(0.85)
    )
    tf = txBox.text_frame
    tf.word_wrap = True

    lines = body_text.split("\n")
    for i, line in enumerate(lines):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.space_after = Pt(4)
        run = p.add_run()
        # Prefix with bullet if the line starts with "- "
        if line.strip().startswith("- "):
            run.text = f"•  {line.strip()[2:]}"
        else:
            run.text = line.strip()
        run.font.name = BODY_FONT
        run.font.size = CARD_BODY_SIZE
        run.font.color.rgb = body_color

    return card


def add_image_placeholder(slide, left, top, width, height, label_text):
    """Add a dashed-border box with a centered label for an image/chart."""
    box = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height
    )
    box.fill.solid()
    box.fill.fore_color.rgb = PLACEHOLDER_BG
    box.line.color.rgb = PLACEHOLDER_BORDER
    box.line.width = Pt(1.5)
    box.line.dash_style = 4  # dash
    box.adjustments[0] = 0.03

    # Center label
    tf = box.text_frame
    tf.word_wrap = True
    tf.paragraphs[0].alignment = PP_ALIGN.CENTER
    run = tf.paragraphs[0].add_run()
    run.text = label_text
    run.font.name = BODY_FONT
    run.font.size = Pt(12)
    run.font.color.rgb = TEAL
    run.font.italic = True
    # Vertical centering
    tf.paragraphs[0].space_before = Pt(0)
    # Use anchor middle
    txBody = tf._txBody
    bodyPr = txBody.find(qn("a:bodyPr"))
    if bodyPr is not None:
        bodyPr.set("anchor", "ctr")


def add_speaker_notes(slide, text):
    """Add speaker notes to the slide Notes pane."""
    notes_slide = slide.notes_slide
    tf = notes_slide.notes_text_frame
    tf.text = text


def add_divider_line(slide, top):
    """Add a thin teal horizontal line across the slide."""
    shape = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        LEFT_MARGIN, top, CONTENT_W, Pt(1.5)
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = TEAL
    shape.line.fill.background()


def add_slide_number(slide, number):
    """Add a small slide number in the bottom-right."""
    add_textbox(
        slide,
        SLIDE_W - Inches(1.0), SLIDE_H - Inches(0.45),
        Inches(0.6), Inches(0.3),
        text=str(number),
        font_size=Pt(11), font_color=TEAL,
        alignment=PP_ALIGN.RIGHT
    )


# ── Build presentation ─────────────────────────────────────────────────

def build_presentation():
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H

    # We use the blank layout for every slide
    blank_layout = prs.slide_layouts[6]  # Blank

    # ================================================================
    # SLIDE 1 — HOOK
    # ================================================================
    slide = prs.slides.add_slide(blank_layout)
    set_slide_bg(slide, BG_COLOR)

    add_title(slide,
              "California Has a Traffic Problem.\n"
              "And a Climate Problem.\nThey're the Same Problem.")

    add_headline(slide,
                 "Every day, Californians drive over 1 billion miles. "
                 "That's not just congestion — it's our biggest source of climate pollution.",
                 top=Inches(1.85))

    bullets = [
        "Transportation is responsible for 38% of California's total greenhouse "
        "gas emissions — more than industry, electricity, and buildings combined",
        "Vehicle Miles Traveled (VMT) — the total distance all cars drive in a "
        "day — has been climbing for years, not falling",
        "California has ambitious climate goals. But the way we fund roads is "
        "actively working against them",
    ]
    add_bullets(slide, bullets, top=Inches(3.0), height=Inches(2.5))

    add_image_placeholder(
        slide,
        SLIDE_W - Inches(4.6), Inches(5.7), Inches(3.8), Inches(1.5),
        "[IMAGE: Aerial photo of Los Angeles\nfreeway interchange at rush hour]"
    )

    add_slide_number(slide, 1)

    add_speaker_notes(slide,
        "I want to start not with policy — but with something everyone in this "
        "room has experienced. Sitting in traffic. Watching the air quality index "
        "tick up on a hot afternoon. Wondering why, despite everything we've heard "
        "about California's climate leadership, our roads keep getting more "
        "congested and our air keeps getting worse. That's what this project is "
        "about. And the answer isn't 'drive less.' It's about changing what we fund."
    )

    # ================================================================
    # SLIDE 2 — PROJECT CONTEXT
    # ================================================================
    slide = prs.slides.add_slide(blank_layout)
    set_slide_bg(slide, BG_COLOR)

    add_title(slide, "About This Project")
    add_headline(slide,
                 "This research was conducted in partnership with NRDC to find "
                 "legislative pathways to make California's transportation spending "
                 "match its climate goals.")

    card_top = Inches(2.5)
    card_h = Inches(4.2)
    card_w = Inches(3.7)
    gap = Inches(0.3)
    total_cards_w = card_w * 3 + gap * 2
    start_left = (SLIDE_W - total_cards_w) / 2

    add_card(slide,
             start_left, card_top, card_w, card_h,
             "The Partner",
             "NRDC (Natural Resources Defense Council) is one "
             "of the nation's leading environmental law and "
             "policy organizations.\n\n"
             "This project was sponsored by Zak Accuardi, "
             "Senior Transportation Policy Advocate.")

    add_card(slide,
             start_left + card_w + gap, card_top, card_w, card_h,
             "The Question",
             "California has a law — SB 375 — that requires "
             "regions to plan for lower emissions.\n\n"
             "But planning and spending are two different "
             "things. Why isn't the spending following the plans?")

    add_card(slide,
             start_left + 2 * (card_w + gap), card_top, card_w, card_h,
             "The Approach",
             "Policy analysis + stakeholder interviews + "
             "spatial data mapping across all 18 California "
             "Metropolitan Planning Organization (MPO) regions.")

    add_slide_number(slide, 2)

    add_speaker_notes(slide,
        "This capstone was done through UC Berkeley's Rausser College of Natural "
        "Resources. My partner on the project was NRDC — the Natural Resources "
        "Defense Council — specifically Zak Accuardi, who works on exactly these "
        "questions professionally. I want to be upfront: this is a policy analysis "
        "project, not an engineering one. We're looking at how laws are written and "
        "how money flows — not at individual driver behavior."
    )

    # ================================================================
    # SLIDE 3 — WHAT IS VMT
    # ================================================================
    slide = prs.slides.add_slide(blank_layout)
    set_slide_bg(slide, BG_COLOR)

    add_title(slide, "What Is VMT — And Why Does It Keep Going Up?")
    add_headline(slide,
                 "VMT stands for Vehicle Miles Traveled — the total miles driven "
                 "by all cars in a region. It's the speedometer for California's "
                 "climate progress on transportation.")

    bullets = [
        "Think of VMT as California's daily driving tab: every trip, every "
        "commute, every delivery truck adds to it",
        "Right now, Californians drive about 24–25 miles per person per day",
        "To hit carbon neutrality by 2045, CARB (California Air Resources Board) "
        "projects we need to get that down to about 17 miles per person per day",
        "The gap between where we are and where we need to be is not closing "
        "— it's growing",
    ]
    add_bullets(slide, bullets, width=Inches(6.8), top=Inches(2.5), height=Inches(3.5))

    add_image_placeholder(
        slide,
        Inches(8.5), Inches(2.6), Inches(4.2), Inches(3.5),
        "[CHART: Two-line chart —\n"
        "\"Where we are\" flat/rising line vs.\n"
        "\"Where we need to be\" declining target line,\n"
        "2015–2045]"
    )

    add_slide_number(slide, 3)

    add_speaker_notes(slide,
        "VMT is the single most important metric in this presentation, so I want "
        "to make sure it's crystal clear. It's not complicated — it's just the "
        "total mileage bill California runs up every day. The reason it matters "
        "for climate is simple: more miles driven equals more fuel burned equals "
        "more emissions. What's striking is that even as electric vehicles have "
        "grown, total VMT has continued to climb — which means electrification "
        "alone won't get us there. We have to actually drive less, collectively."
    )

    # ================================================================
    # SLIDE 4 — SB 375 EXPLAINED
    # ================================================================
    slide = prs.slides.add_slide(blank_layout)
    set_slide_bg(slide, BG_COLOR)

    add_title(slide, "The Law That Was Supposed to Fix This: SB 375")
    add_headline(slide,
                 "Passed in 2008, SB 375 requires every California region to "
                 "create a plan showing how it will reduce transportation "
                 "emissions. The keyword is 'plan.'")

    bullets = [
        "SB 375 requires California's 18 Metropolitan Planning Organizations "
        "(MPOs) — the regional agencies that decide where roads and transit go — "
        "to produce a \"Sustainable Communities Strategy\" (SCS): a transportation "
        "and land use plan aligned with state climate targets",
        "CARB (California Air Resources Board) sets GHG (greenhouse gas) "
        "reduction targets for each region",
        "Regions must show, on paper, how their plan achieves those targets",
        "The law was groundbreaking in 2008. Sixteen years later, emissions "
        "are still rising",
    ]
    add_bullets(slide, bullets, width=Inches(7.5), top=Inches(2.5), height=Inches(3.8))

    add_image_placeholder(
        slide,
        Inches(9.0), Inches(2.8), Inches(3.7), Inches(3.0),
        "[IMAGE: Simple map of California's\n18 MPO regions]"
    )

    add_slide_number(slide, 4)

    add_speaker_notes(slide,
        "SB 375 was genuinely a landmark law when it passed. It was the first "
        "in the country to link transportation planning to climate targets at a "
        "regional level. The idea was: if we require regions to plan for lower "
        "emissions, the spending will follow. Spoiler: it didn't. And the reason "
        "why is what I want to show you next."
    )

    # ================================================================
    # SLIDE 5 — THE LOOPHOLE
    # ================================================================
    slide = prs.slides.add_slide(blank_layout)
    set_slide_bg(slide, BG_COLOR)

    add_title(slide, "The Problem: Good Plans, No Consequences")
    add_headline(slide,
                 "SB 375 requires regions to write plans that show a path to "
                 "lower emissions. It doesn't require them to actually follow "
                 "the plan.")

    bullets = [
        "Think of it like a gym membership where you write a detailed workout "
        "schedule every four years — but no one ever checks if you showed up",
        "Regions can submit a plan projecting significant VMT reductions, then "
        "fund highway expansions that generate more driving — with no legal "
        "consequence",
        "This gap between planning and spending is where climate progress gets "
        "lost",
        "Result: VMT and emissions are trending upward statewide, even as "
        "regions report \"on track\" in their plans",
    ]
    add_bullets(slide, bullets, width=Inches(6.5), top=Inches(2.5), height=Inches(3.5))

    # Two-column diagram on the right
    diag_left = Inches(8.0)
    diag_top = Inches(2.6)
    diag_w = Inches(2.3)
    diag_h = Inches(3.6)

    # Left column — Teal
    add_card(slide,
             diag_left, diag_top, diag_w, diag_h,
             "What SB 375 Requires",
             "- Plans\n- Projections\n- Targets on paper",
             title_color=TEAL, card_color=CARD_BG)

    # Right column — Coral
    add_card(slide,
             diag_left + diag_w + Inches(0.2), diag_top, diag_w, diag_h,
             "What It Doesn't Require",
             "- Spending alignment\n- Enforcement\n- Consequences for\n  missing targets",
             title_color=CORAL, card_color=CARD_BG)

    add_slide_number(slide, 5)

    add_speaker_notes(slide,
        "This is the core insight of the whole project, and I want to make sure "
        "it lands. SB 375 is a planning mandate. It requires good documents. It "
        "does not require good spending decisions. And in practice, what we've "
        "seen is that regions produce plans showing impressive VMT reductions — "
        "and then fund projects that do the opposite. There's no mechanism that "
        "says: if you miss your target, you lose your highway funding. That's the "
        "gap we're trying to close."
    )

    # ================================================================
    # SLIDE 6 — THE LEGISLATIVE WINDOW
    # ================================================================
    slide = prs.slides.add_slide(blank_layout)
    set_slide_bg(slide, BG_COLOR)

    add_title(slide, "The Opening: SB 1087")
    add_headline(slide,
                 "A technical bill introduced in February 2026 quietly touches "
                 "the same legal code as SB 375 — creating a rare window to "
                 "insert real accountability.")

    card_top = Inches(2.5)
    card_h = Inches(4.3)
    card_w = Inches(5.6)
    gap = Inches(0.4)
    total_w = card_w * 2 + gap
    start_left = (SLIDE_W - total_w) / 2

    add_card(slide,
             start_left, card_top, card_w, card_h,
             "What SB 1087 Does",
             "Introduced by Senator Cabaldon, SB 1087 makes administrative "
             "updates to California's transportation planning framework:\n\n"
             "- Changes how often regions must update their plans (from every "
             "4 years to every 8 years)\n"
             "- Changes how $25 million in planning grants are allocated (from "
             "discretionary to population-based)\n"
             "- Shifts grant administration away from Caltrans")

    add_card(slide,
             start_left + card_w + gap, card_top, card_w, card_h,
             "Why This Matters",
             "Because SB 1087 touches the exact same sections of California "
             "law as SB 375, it creates \"legislative hooks\" — specific code "
             "sections where climate accountability language can be inserted "
             "during the amendment process.\n\n"
             "A technical bill becomes a potential climate accountability bill.")

    add_slide_number(slide, 6)

    add_speaker_notes(slide,
        "This is where the project gets strategic. We couldn't just amend SB 375 "
        "directly — the legal structure is too narrow for investment mandates. But "
        "SB 1087, introduced just this February, opens the right doors. It's "
        "currently a fairly dry administrative bill. But because it touches "
        "the same code sections, it gives advocates a vehicle to attach real "
        "enforcement mechanisms this legislative session. The window is open right now."
    )

    # ================================================================
    # SLIDE 7 — LESSONS FROM OTHER STATES
    # ================================================================
    slide = prs.slides.add_slide(blank_layout)
    set_slide_bg(slide, BG_COLOR)

    add_title(slide, "Other States Already Closed This Gap")
    add_headline(slide,
                 "Colorado, Minnesota, Virginia, and Massachusetts each passed "
                 "laws that tie transportation dollars directly to climate "
                 "performance. California can adapt all four.")

    # 2x2 grid of cards
    card_w = Inches(5.6)
    card_h = Inches(1.95)
    gap_x = Inches(0.4)
    gap_y = Inches(0.25)
    total_w = card_w * 2 + gap_x
    start_left = (SLIDE_W - total_w) / 2
    start_top = Inches(2.45)

    add_card(slide,
             start_left, start_top, card_w, card_h,
             "COLORADO — Budget Lock",
             "Any project that increases emissions must be paired with transit, "
             "bike lanes, or demand management to offset the impact. "
             "No mitigation = no funding.",
             title_color=CORAL)

    add_card(slide,
             start_left + card_w + gap_x, start_top, card_w, card_h,
             "MINNESOTA — Capacity Trigger",
             "Any highway expansion over 0.5 miles requires a 20-year emissions "
             "impact study. If it fails, the project must be redesigned, offset, "
             "or canceled.",
             title_color=CORAL)

    add_card(slide,
             start_left, start_top + card_h + gap_y, card_w, card_h,
             "VIRGINIA — Climate & Equity Scoring",
             "Projects are scored on GHG reduction, multimodal access, and "
             "benefits to disadvantaged communities. Sprawl-inducing projects "
             "naturally score lower and lose funding.",
             title_color=CORAL)

    add_card(slide,
             start_left + card_w + gap_x, start_top + card_h + gap_y, card_w, card_h,
             "MASSACHUSETTS — Enforceable Emission Caps",
             "Legally binding, annually declining CO₂ limits for the state DOT. "
             "Miss the target and supplemental corrective measures are legally "
             "required.",
             title_color=CORAL)

    add_slide_number(slide, 7)

    add_speaker_notes(slide,
        "None of these states reinvented the wheel. They just added consequences. "
        "Colorado locked the budget. Minnesota required honest accounting. Virginia "
        "built equity into the scoring. Massachusetts made the targets legally "
        "binding. California has the policy infrastructure to do all four — we "
        "just need the political will to attach them to the right bill."
    )

    # ================================================================
    # SLIDE 8 — SCENARIO 1
    # ================================================================
    slide = prs.slides.add_slide(blank_layout)
    set_slide_bg(slide, BG_COLOR)

    add_title(slide,
              "Reform Option 1: The 'Corrective Action' Moratorium")
    add_headline(slide,
                 "If a region misses its emissions targets twice in a row, "
                 "highway expansion funding is frozen until it has a credible "
                 "plan to get back on track.")

    bullets = [
        "Modeled on: Colorado's GHG Budget Lock",
        "Trigger: Two consecutive planning cycles with missed GHG "
        "(greenhouse gas) targets",
        "Consequence: No state or federal funds may be spent on projects that "
        "add new highway lanes until CARB (California Air Resources Board) "
        "certifies a credible Corrective Action Plan",
        "Restoration: Funding resumes only when the region demonstrates a "
        "binding path back to its 2035 and 2045 targets",
        "Political viability: MODERATE — most feasible near-term option; "
        "consequence is a pause, not a permanent cut",
    ]
    add_bullets(slide, bullets, width=Inches(7.0), top=Inches(2.5), height=Inches(4.0))

    add_image_placeholder(
        slide,
        Inches(8.5), Inches(2.8), Inches(4.2), Inches(3.2),
        "[DIAGRAM: Flowchart —\n"
        "Miss target once → Warning\n"
        "Miss target twice → Corrective Action\n"
        "→ Funding freeze → CARB review\n"
        "→ Funding restored]"
    )

    add_slide_number(slide, 8)

    add_speaker_notes(slide,
        "This is the scenario I'd recommend as the starting point for this "
        "legislative session. It's not the most transformative option, but it's "
        "the most politically viable. The key insight is that it doesn't "
        "permanently cut anyone's funding — it creates a pause with a clear path "
        "to restoration. That makes it much harder to oppose. A region that's "
        "genuinely making progress has nothing to fear from this."
    )

    # ================================================================
    # SLIDE 9 — SCENARIO 2
    # ================================================================
    slide = prs.slides.add_slide(blank_layout)
    set_slide_bg(slide, BG_COLOR)

    add_title(slide,
              "Reform Option 2: The 'VMT Neutral' Investment Rule")
    add_headline(slide,
                 "Before any highway expansion gets funded, it must prove it "
                 "won't increase total driving — or fund the alternatives that "
                 "offset it.")

    bullets = [
        "Modeled on: Minnesota's Capacity Trigger",
        "Requirement: Any project adding vehicle capacity must complete a "
        "20-year GHG (greenhouse gas) and VMT (Vehicle Miles Traveled) impact "
        "assessment before inclusion in a regional funding program",
        "If the assessment shows a net increase in driving, the project "
        "sponsor must fund a VMT Mitigation Plan — transit improvements, bike "
        "infrastructure, or infill housing — that fully offsets the projected "
        "20-year impact",
        "In plain English: if you want to widen a highway, you have to pay for "
        "the bus lines that absorb the extra demand",
        "Political viability: STRONG but contested — highway agencies will "
        "push back",
    ]
    add_bullets(slide, bullets, top=Inches(2.5), height=Inches(4.2),
                font_size=Pt(17))

    add_slide_number(slide, 9)

    add_speaker_notes(slide,
        "This one has real teeth. It basically says: 'Big Highway' projects have "
        "to fund their own climate offsets. If Caltrans wants to add a lane on "
        "I-5, it has to show that the induced demand won't blow up regional "
        "emissions targets — and if it will, it has to fund transit or housing "
        "alternatives that absorb that demand. This is how you stop the cycle of "
        "building more roads and then wondering why there's more traffic."
    )

    # ================================================================
    # SLIDE 10 — SCENARIO 3
    # ================================================================
    slide = prs.slides.add_slide(blank_layout)
    set_slide_bg(slide, BG_COLOR)

    add_title(slide,
              "Reform Option 3: The 'Climate Floor' Scoring Test")
    add_headline(slide,
                 "No project that fails a climate performance test should be "
                 "eligible for state transportation funding — period.")

    bullets = [
        "Modeled on: Virginia's SMART SCALE Scoring + Massachusetts' "
        "Enforceable Emission Caps",
        "Climate Floor: Any project with a negative net score for VMT "
        "(Vehicle Miles Traveled) reduction is automatically ineligible for "
        "state funding, regardless of how it scores on other criteria",
        "Objective Need Standard: Projects must address a need identified in a "
        "statewide assessment — not just a locally-defined traffic throughput goal",
        "Multimodal Alternatives Test: For every mobility need identified, at "
        "least two non-highway alternatives must be evaluated with the same "
        "rigor as the capacity project",
        "If a multimodal option scores better on climate, the highway expansion "
        "is statutorily ineligible",
        "Political viability: TRANSFORMATIVE but faces strongest opposition",
    ]
    add_bullets(slide, bullets, top=Inches(2.5), height=Inches(4.5),
                font_size=Pt(16))

    add_slide_number(slide, 10)

    add_speaker_notes(slide,
        "This is the long game. It fundamentally restructures how California "
        "decides what gets funded — not by tweaking the scoring at the margins, "
        "but by establishing a hard floor. If your project makes climate worse, "
        "it doesn't get state money. Full stop. Virginia and Massachusetts have "
        "shown this is legally defensible and politically survivable — but it will "
        "require building a broader coalition than Scenario 1 to get there."
    )

    # ================================================================
    # SLIDE 11 — EQUITY AND HEALTH DATA
    # ================================================================
    slide = prs.slides.add_slide(blank_layout)
    set_slide_bg(slide, BG_COLOR)

    add_title(slide, "The Stakes: Who Bears the Burden Today")
    add_headline(slide,
                 "The communities closest to California's busiest freeways face "
                 "the worst air quality, the highest emissions exposure, and the "
                 "fewest transportation alternatives.")

    bullets = [
        "309 census tracts statewide qualify as \"hotspots\" — combining high "
        "VMT (Vehicle Miles Traveled) and high pollution burden",
        "These hotspots are concentrated along I-710, I-105, SR-99, and I-80 — "
        "corridors that run directly through low-income communities and "
        "communities of color",
        "DAC (Disadvantaged Community) tracts average 23.4 miles/day of driving "
        "vs. 22.5 for non-DAC tracts — a modest mean difference that masks "
        "severe corridor-level disparities",
        "Note: per-capita VMT can appear lower in dense urban corridors even "
        "when absolute pollution burden is highest. The Central Valley shows "
        "this pattern — lower per-capita VMT but concentrated freight and "
        "agricultural traffic exposure",
        "Reformed investment — transit, walking infrastructure, infill housing "
        "— delivers the greatest health gains in precisely these communities",
    ]
    add_bullets(slide, bullets, width=Inches(7.2), top=Inches(2.5),
                height=Inches(4.5), font_size=Pt(16))

    add_image_placeholder(
        slide,
        Inches(8.8), Inches(2.8), Inches(3.9), Inches(3.5),
        "[MAP: California with hotspot corridors\n"
        "highlighted — I-710, I-105, SR-99, I-80\n"
        "— overlaid with DAC tract boundaries]"
    )

    add_slide_number(slide, 11)

    add_speaker_notes(slide,
        "I want to be transparent about a methodological choice here. We used "
        "per-capita VMT as our primary metric, which can actually undercount "
        "burden in places like the Central Valley, where absolute freight traffic "
        "is enormous but spread across a smaller population. The 309 hotspot "
        "number is conservative. The human reality — elevated asthma rates, "
        "cardiovascular disease, premature death near these corridors — is "
        "well-documented in the literature and should not be obscured by the "
        "averages."
    )

    # ================================================================
    # SLIDE 12 — CLOSING AND HONEST TENSION
    # ================================================================
    slide = prs.slides.add_slide(blank_layout)
    set_slide_bg(slide, BG_COLOR)

    add_title(slide,
              "What We're Asking For — And What We're Not Promising")
    add_headline(slide,
                 "Scenario 1 alone won't hit California's 2045 targets. But it "
                 "breaks the pattern of consequence-free inaction — and that's "
                 "where transformation starts.")

    card_top = Inches(2.5)
    card_h = Inches(4.3)
    card_w = Inches(5.6)
    gap = Inches(0.4)
    total_w = card_w * 2 + gap
    start_left = (SLIDE_W - total_w) / 2

    add_card(slide,
             start_left, card_top, card_w, card_h,
             "The Honest Tension",
             "Will any of this close the gap by 2035? Not on its own.\n\n"
             "California's climate targets require structural changes to land "
             "use, transit investment, and pricing that go well beyond any "
             "single bill.\n\n"
             "What these reforms do is stop actively making the problem worse — "
             "and create the accountability infrastructure that bigger reforms "
             "can build on.",
             title_color=CORAL)

    add_card(slide,
             start_left + card_w + gap, card_top, card_w, card_h,
             "The Ask",
             "- For NRDC: Deploy the three-scenario framework in SB 1087 "
             "stakeholder briefings this session. Start with Scenario 1.\n\n"
             "- For California: Insert VMT accountability language into SB 1087's "
             "touch-points at Government Code and Streets & Highways Code.\n\n"
             "- For everyone: Stop treating planning documents as accomplishments. "
             "Plans are not investments. Investments are investments.",
             title_color=TEAL)

    add_slide_number(slide, 12)

    add_speaker_notes(slide,
        "I want to end with honesty. Someone in the room is probably thinking: "
        "'Even if all three scenarios pass, does California hit its targets?' And "
        "the answer is: not automatically. These reforms are necessary but not "
        "sufficient. What they do is stop the hemorrhaging — stop funding projects "
        "that actively undermine the plans we've already written. That's not "
        "nothing. That's the foundation. The ask I'd leave you with is simple: "
        "the next time you hear that a region 'has a plan' to reduce emissions, "
        "ask what happens if they don't follow it. Right now, the answer is "
        "nothing. These reforms change that answer."
    )

    return prs


# ── Main ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    try:
        output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   "rethinking_sb375_final.pptx")
        prs = build_presentation()
        prs.save(output_path)
        print(f"✅  Presentation saved successfully: {output_path}")
        print(f"    Slides: {len(prs.slides)}")
        print("    Speaker notes: present on all 12 slides")
    except Exception as e:
        print(f"❌  Error generating presentation: {e}")
        raise
