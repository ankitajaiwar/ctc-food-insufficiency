# builds brief/brief.pdf from the figures. python brief/make_brief.py
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (Image, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

INK = colors.HexColor("#0b0b0b")
GRAY = colors.HexColor("#52514e")
BLUE = colors.HexColor("#2a78d6")
BOX = colors.HexColor("#eef3fb")
RULE = colors.HexColor("#d6d5d1")

body = ParagraphStyle("body", fontName="Helvetica", fontSize=9.3, leading=12.6, textColor=INK,
                      spaceAfter=5, alignment=TA_LEFT)
small = ParagraphStyle("small", parent=body, fontSize=8, leading=10.5, textColor=GRAY, spaceAfter=3)
h1 = ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=17, leading=21, textColor=INK, spaceAfter=4)
sub = ParagraphStyle("sub", parent=body, fontSize=10.5, leading=14, textColor=GRAY, spaceAfter=2)
h2 = ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=11.5, leading=15, textColor=INK,
                    spaceBefore=6, spaceAfter=3)
boxh = ParagraphStyle("boxh", fontName="Helvetica-Bold", fontSize=10, leading=13, textColor=BLUE, spaceAfter=4)
bullet = ParagraphStyle("bullet", parent=body, leftIndent=11, bulletIndent=0, spaceAfter=4)


def bullets(items, style=bullet):
    return [Paragraph(t, style, bulletText="•") for t in items]


def box(title, items):
    inner = [Paragraph(title, boxh)] + bullets(items)
    t = Table([[inner]], colWidths=[7.0 * inch])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), BOX),
                           ("LEFTPADDING", (0, 0), (-1, -1), 12), ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                           ("TOPPADDING", (0, 0), (-1, -1), 9), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    return t


def fig(path, width, caption):
    img = Image(path)
    img.drawWidth, img.drawHeight = width, width * img.imageHeight / img.imageWidth
    return KeepTogether([img, Paragraph(caption, small), Spacer(1, 4)])


def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(RULE)
    canvas.line(0.75 * inch, 0.6 * inch, 7.75 * inch, 0.6 * inch)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(GRAY)
    canvas.drawString(0.75 * inch, 0.42 * inch, "Child Tax Credit payments and food insufficiency  |  Ankita Singh, PhD")
    canvas.drawRightString(7.75 * inch, 0.42 * inch, str(doc.page))
    canvas.restoreState()


s = []
s.append(Paragraph("Monthly Child Tax Credit Payments Reduced Food Hardship, Most for Families With the Least", h1))
s.append(Paragraph("Evidence from the Census Household Pulse Survey, 2021–2022", sub))
s.append(Paragraph("Ankita Singh, PhD  ·  November 2026", small))
s.append(Spacer(1, 6))

s.append(box("Key findings", [
    "While the monthly payments were arriving (July–December 2021), the share of families with children who "
    "<b>sometimes or often did not have enough to eat fell by about 2.4 to 3.1 percentage points</b> compared with "
    "families without children. That is roughly a <b>one-fifth drop</b>.",
    "The drop was largest for families earning under $35,000 (about 7 points), Hispanic families, families with "
    "three or more children, and families without a college graduate. Families earning $75,000–$150,000 saw "
    "almost no change.",
    "The improvement faded in the months after the payments stopped and was gone by spring 2022.",
]))

s.append(Paragraph("Background", h2))
s.append(Paragraph(
    "For 2021 only, the American Rescue Plan Act raised the Child Tax Credit from $2,000 per child to $3,600 for "
    "each child under 6 and $3,000 for each child aged 6 to 17. It also made the credit fully refundable, so "
    "families with little or no earnings could receive the full amount; under prior law, the credit grew with "
    "earnings. For the first time, the IRS paid half of the credit in advance, as monthly deposits of up to $300 "
    "per young child and $250 per older child, from July 15 to December 15, 2021. Families received the rest when "
    "they filed their 2021 taxes. The expansion expired after 2021, and no monthly payments followed.", body))
s.append(Paragraph(
    "This brief asks two questions: did the monthly payments reduce food hardship, and which families gained "
    "the most?", body))

s.append(Paragraph("Finding 1: Food hardship fell as soon as payments began, then returned after they ended", h2))
s.append(Paragraph(
    "The Census Bureau's Household Pulse Survey asked adults every few weeks whether their household had "
    "enough to eat in the past seven days. I compared families with children, who received the payments, with "
    "families without children, who did not, before, during, and after the payment months. The figure shows how "
    "the gap between the two groups moved over time.", body))
s.append(fig("figures/event_study_150K.png", 6.4 * inch,
             "Each point compares households with and without children (income under $150,000) to the same "
             "comparison in early March 2021. Lower values mean families with children were doing relatively better. "
             "Vertical lines show 95 percent confidence intervals."))
s.append(Paragraph(
    "Before mid-March 2021, the gap was steady. It dipped when the $1,400-per-person stimulus checks arrived "
    "(those checks also paid families for each child) and returned to its earlier level by early summer. In the "
    "first survey after the first CTC payment in July, the gap dropped sharply, and it stayed lower through "
    "December. Across the payment months, food insufficiency among families with children fell by "
    "2.4 to 3.1 percentage points relative to families without children, depending on which earlier period "
    "is used as the baseline. Before the payments, about 14 percent of these families were food-insufficient. "
    "After the payments ended, the gap closed gradually and was back at its pre-payment level by May 2022.", body))

s.append(Paragraph("Finding 2: Families with the least gained the most", h2))
s.append(Paragraph(
    "The biggest improvements went to families who were most likely to go without enough food to begin with. "
    "Among families earning under $35,000, about one in three was food-insufficient before the payments; the "
    "payments lowered that by roughly 7 percentage points. The drop was also large for Hispanic families (5 points), "
    "families with three or more children (6 points, consistent with larger payments for larger families), and "
    "families without a college graduate (4 points). Families earning $75,000–$150,000, and families with a "
    "college graduate, saw almost no change, likely because few of them were struggling to afford food in the "
    "first place.", body))
s.append(fig("figures/subgroups_brief.png", 5.0 * inch,
               "Each point is a separate comparison within one group. Points further left mean a "
               "larger drop in food hardship. Lines show 95 percent confidence intervals."))
s.append(Paragraph(
    "A machine-learning method (a causal forest) that considers all of these characteristics together reached the "
    "same conclusion. I tested it on a half of the data it had not seen. The quarter of families it predicted would "
    "benefit most showed a 5-point drop, while the other three quarters showed little change. Most families in that "
    "top quarter had incomes under $35,000.", body))

s.append(Paragraph("What this means for policy", h2))
s.extend(bullets([
    "<b>Regular cash reached families quickly.</b> The drop appeared in the first survey after the first deposit, "
    "within about three weeks. For families on the edge, the timing of support matters as well as its size.",
    "<b>Full refundability shaped who benefited.</b> The largest gains went to the lowest-income families, who "
    "would have received a partial credit or none under the prior earnings-based rules. Decisions about how the "
    "credit phases in with earnings largely determine its effect on food hardship.",
    "<b>Temporary support brought temporary relief.</b> Food hardship returned within months of the last payment. "
    "Policymakers weighing short-term versus ongoing support should expect the effects to last about as long as "
    "the payments do.",
    "<b>This brief does not weigh everything that matters.</b> It does not assess cost, effects on work, or other "
    "outcomes such as housing or health, which other studies have examined and which belong in any full assessment.",
]))

s.append(Paragraph("How confident can we be?", h2))
s.append(Paragraph(
    "The results line up with earlier studies using the same survey (Shafer et al., 2022; Parolin et al., 2021). "
    "When I repeated their comparisons, I found similar effects: a 4.5-point drop between the surveys just before "
    "and just after the first payment, versus their 3.7, and a 7.0-point drop for families under $35,000, versus "
    "their 7.5. The main estimate holds with all income levels included and with the Census Bureau's recommended "
    "method for calculating survey uncertainty. A similar drop shows up in another measure, difficulty paying "
    "usual household expenses.", body))
s.append(Paragraph(
    "There are limits. The survey asks different people each round, response rates are low, and answers are "
    "self-reported. Families with and without children may have been affected differently by other changes in "
    "2021, such as expanded SNAP benefits, free school meals, and the end of extra unemployment benefits in "
    "September. The extended data from early 2021 help rule out the stimulus checks as an explanation, but not "
    "every other policy change. The income question also changed from 2019 to 2020 income just as the payments "
    "began; results that include all incomes are similar.", body))

s.append(Paragraph("Data and methods", h2))
s.append(Paragraph(
    "U.S. Census Bureau Household Pulse Survey public use files, weeks 22–45 (January 2021 to May 2022), "
    "1.69 million adult responses. Main sample: households with incomes under $150,000 (761,268 responses). "
    "Weighted difference-in-differences and event-study regressions with survey-week and state fixed effects and "
    "demographic controls; standard errors are clustered by state and checked with replicate weights. "
    "Heterogeneity: subgroup regressions and causal forests validated on held-out data. Code and full results: "
    "github.com/ankitajaiwar/ctc-food-insufficiency.", small))
s.append(Paragraph(
    "References: Parolin, Z., Ananat, E., Collyer, S., Curran, M., & Wimer, C. (2021). The initial effects of the "
    "expanded Child Tax Credit on material hardship. NBER Working Paper 29285. Shafer, P. R., Gutiérrez, K. M., "
    "Ettinger de Cuba, S., Bovell-Ammon, A., & Raifman, J. (2022). Association of the implementation of Child Tax "
    "Credit advance payments with food insufficiency in US households. JAMA Network Open, 5(1), e2143296. "
    "IRS, 2021 Child Tax Credit frequently asked questions.", small))

doc = SimpleDocTemplate("brief/brief.pdf", pagesize=letter, leftMargin=0.75 * inch, rightMargin=0.75 * inch,
                        topMargin=0.65 * inch, bottomMargin=0.8 * inch,
                        title="Monthly Child Tax Credit Payments Reduced Food Hardship", author="Ankita Singh")
doc.build(s, onFirstPage=footer, onLaterPages=footer)
