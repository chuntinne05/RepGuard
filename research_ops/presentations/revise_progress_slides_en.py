"""Ten revised English PNG slides: natural prose and blue/black/white only.

MPLCONFIGDIR=/private/tmp/repguard-matplotlib-cache \
PYTHONPATH=/private/tmp/repguard-pdf-deps:/private/tmp/repguard-chart-deps:. \
  .venv/bin/python -m research_ops.presentations.revise_progress_slides_en
"""
import io
import json
import zipfile
from pathlib import Path

import pymupdf as fitz
from PIL import Image, ImageOps
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.font_manager import FontProperties, fontManager

from . import progress_slide_canvas as c

ROOT=c.ROOT
OUT=ROOT/'output/status_update_2026-11-10/english_revised'
SLIDES=OUT/'slides'
ASSETS=OUT/'charts'
for p in (OUT,SLIDES,ASSETS):p.mkdir(parents=True,exist_ok=True)
BLUE=(.118,.306,.475)
BLACK=(.055,.055,.055)
WHITE=(1,1,1)
PALE=tuple(.93+.07*v for v in BLUE)
BHEX='#1E4E79'
c.start()

# Keep the triangular background, bringing every decorative pixel into the
# same blue hue. Unrelated logos remain covered by the title/footer and mask.
bg=Image.open(io.BytesIO(c.background)).convert('RGB')
bg=ImageOps.colorize(ImageOps.grayscale(bg),black=BHEX,white='white')
buf=io.BytesIO();bg.save(buf,format='PNG');c.background=buf.getvalue()

def text(x,y,value,size=24,font='R',color=BLACK,width=None,align='left',leading=1.34):
    return c.text(x,y,value,size,font,color,width,align,leading)

rect,line,circle=c.rect,c.line,c.circle

def rule(x1,y1,x2,y2,width=1):line(x1,y1,x2,y2,BLUE,width)

def arrow(x1,y1,x2,y2):c.arrow(x1,y1,x2,y2,BLUE,1.7)

def page(title,name):
    c.current=c.doc.new_page(width=1280,height=720)
    for key,path in c.FONTS.items():c.current.insert_font(fontname=key,fontfile=str(path))
    c.current.insert_image(c.current.rect,stream=c.background)
    rect(1200,630,80,60,WHITE)
    rect(0,0,1280,76.8,BLUE)
    assert c.FONT['B'].text_length(title,fontsize=35)<1214
    text(24,13,title,35,'B',WHITE)
    rect(0,690,1280,30,BLUE)
    text(22,693,'Tín & Trung',16,'B',WHITE)
    text(440,693,'RepGuard · Progress Update',16,'B',WHITE,width=400,align='center')
    text(1000,693,'10 Nov 2026',16,'R',WHITE)
    text(1200,693,f'{len(c.doc)} / 10',16,'B',WHITE,width=60,align='right')
    c.names.append(name)

def numbered(x,y,n,title,body,width=490):
    circle(x,y+18,15,BLUE)
    text(x-15,y+3,str(n),18,'B',WHITE,width=30,align='center')
    text(x+35,y,title,27,'B',width=width)
    text(x+35,y+49,body,23,width=width)

def box(x,y,w,h,title,body=None):
    rect(x,y,w,h,WHITE,BLUE,1.2)
    text(x+14,y+10,title,22,'B',BLUE,width=w-28)
    if body:text(x+14,y+52,body,20,width=w-28)

def image_plot(name,y,width=1150):
    with Image.open(ASSETS/name) as im:height=width*im.height/im.width
    c.current.insert_image(fitz.Rect(65,y,65+width,y+height),filename=str(ASSETS/name))
    return y+height

# Charts use fill, outlines and hatching in one color rather than extra accents.
for path in c.FONTS.values():fontManager.addfont(str(path))
FP=FontProperties(fname=str(c.FONTS['R']))
plt.rcParams.update({'font.family':FP.get_name(),'font.size':22,'text.color':'black',
    'axes.labelcolor':'black','xtick.color':'black','ytick.color':'black',
    'axes.edgecolor':BHEX,'figure.facecolor':'white','savefig.facecolor':'white',
    'hatch.color':BHEX,'hatch.linewidth':1.1})
v1=json.loads((ROOT/'docs/reports/2026-11-09/verification_v1_summary.json').read_text())
v2=json.loads((ROOT/'docs/reports/2026-11-09/arqa_v2_results.json').read_text())
v6=json.loads((ROOT/'docs/reports/2026-11-10/specbridge_v6_offline_results.json').read_text())
delta=[v1['primary_cross_minus_self_pp'],100*v2['contrasts']['checklist']['delta']]
ci=[v1['claim_cluster_bootstrap95_pp'],[100*x for x in v2['contrasts']['checklist']['ci95']]]

fig=plt.figure(figsize=(16,4.6),dpi=200)
ax=fig.add_axes([.35,.18,.41,.68])
ax.set_xlim(-5,10);ax.set_ylim(-.6,1.6);ax.set_yticks([])
ax.set_xticks([-5,0,5,10],['−5','0','+5','+10'],fontsize=21)
ax.grid(axis='x',color=BHEX,alpha=.12,lw=1)
ax.axvline(0,color='black',ls=(0,(4,4)),lw=1.2)
for side in ['top','right','left']:ax.spines[side].set_visible(False)
ax.spines['bottom'].set_alpha(.25)
ax.tick_params(axis='x',length=0,pad=10)
for i,y in enumerate([1,0]):
    lo,hi=ci[i]
    ax.errorbar(delta[i],y,xerr=[[delta[i]-lo],[hi-delta[i]]],fmt='o',color=BHEX,
                elinewidth=2.8,markersize=10,capsize=8,capthick=2)
    yy=fig.transFigure.inverted().transform(ax.transData.transform((0,y)))[1]
    fig.text(.025,yy+.04,['Evidence checking','Financial report QA'][i],fontsize=24,weight='bold',va='center')
    fig.text(.025,yy-.065,['120 pairs / 24 groups','24 questions / 24 groups'][i],fontsize=21,va='center')
    fig.text(.80,yy+.04,f'{delta[i]:+.2f} pp',fontsize=25,weight='bold',color=BHEX,va='center')
    fig.text(.80,yy-.065,f'[{lo:.2f}, +{hi:.2f}]'.replace('-', '−'),fontsize=22,va='center')
fig.text(.80,.91,'95% confidence interval',fontsize=20)
fig.text(.35,.015,'Cross-model review − self-review (percentage points)',fontsize=21)
fig.savefig(ASSETS/'03_review_comparison.png',dpi=200);plt.close(fig)

values=[v6['workflows'][w]['passed'] for w in ['A','B','AA','BB','AB','BA']]
assert values==[18,19,21,21,19,20]
fig=plt.figure(figsize=(16,4.8),dpi=200)
ax=fig.add_axes([.075,.15,.89,.68])
pos=[0,1,2.5,3.5,5,6]
for i,(x,v) in enumerate(zip(pos,values)):
    group=i//2
    ax.bar(x,v,width=.65,facecolor=BHEX if group==1 else 'white',edgecolor=BHEX,
           hatch='///' if group==2 else None,lw=1.6,zorder=3)
    ax.text(x,v+.45,f'{v}/24',ha='center',va='bottom',fontsize=24,weight='bold',color=BHEX)
ax.set_xlim(-.65,6.65);ax.set_ylim(0,24)
ax.set_xticks(pos,['A','B','AA','BB','AB','BA'],fontsize=23,weight='bold')
ax.set_yticks([0,6,12,18,24],['0','6','12','18','24'],fontsize=21)
ax.set_ylabel('Correct cases',fontsize=22,labelpad=12)
ax.tick_params(axis='both',length=0,pad=8)
ax.grid(axis='y',color=BHEX,alpha=.12,zorder=0)
for side in ['top','right','left']:ax.spines[side].set_visible(False)
ax.spines['bottom'].set_alpha(.25)
fig.legend(handles=[Patch(facecolor='white',edgecolor=BHEX,label='Direct answer'),
                    Patch(facecolor=BHEX,edgecolor=BHEX,label='Self-review'),
                    Patch(facecolor='white',edgecolor=BHEX,hatch='///',label='Cross-model review')],
           loc='upper left',bbox_to_anchor=(.073,1.025),ncol=3,frameon=False,fontsize=22,columnspacing=2)
fig.savefig(ASSETS/'08_sql_results.png',dpi=200);plt.close(fig)

# 01
page('Agenda','01_agenda.png')
rect(65,115,1150,38,BLUE)
text(80,116,'Progress since the October report',25,'B',WHITE)
rect(65,153,1150,57,PALE)
text(80,158,'Four studies, a working verification layer, and a plan for the next experiments.',23,width=1120)
numbered(92,258,1,'Work completed','What we ran, what we built, and how we moved beyond checking only the final answer.')
numbered(92,450,2,'What we learned','What the results tell us about review, task completion and the way answers are judged.')
numbered(690,258,3,'Research direction','How we plan to test whether verification feedback helps agents correct their work.',width=450)
numbered(690,450,4,'Next steps','What Tín and Trung will prepare before the next comparison.',width=450)
text(75,628,'The main question is how agents can check and pass on analytical work more reliably.',23,width=1130)

# 02
page('What we have done since the last report','02_work_completed.png')
text(75,106,'1,265',51,'B',BLUE)
text(270,126,'new responses across four studies',29,'B',width=920)
rule(75,200,1205,200)
for i,(n,title,scope) in enumerate([
    ('720','Evidence checking','120 pairs · 24 groups'),
    ('288','Financial report QA','24 questions · 2 prompts'),
    ('113','Data workspaces','6 tasks · 36 runs'),
    ('144','SQL with specified\ninterpretations','12 tasks · 24 cases')]):
    x=75+i*290
    circle(x+10,231,6,BLUE)
    if i<3:rule(x+17,231,x+290,231)
    text(x,254,n,43,'B',BLUE,width=270)
    text(x,320,title,23,'B',width=270)
    text(x,399,scope,21,width=270)
text(75,468,'We started with evidence checking and report questions, then moved to agents working with files and databases. This gave us examples of both reasoning errors and failures to finish a task.',24,width=1130)
text(75,587,'Alongside these runs, we built a checker that links each SQL query to its source data and the requirements it is meant to satisfy.',24,width=1130)

# 03
page('Does using a different reviewer help?','03_cross_model_vs_self_review.png')
text(75,107,'We compared asking a model to check its own answer with asking the other model to review it.',24,width=1130)
image_plot('03_review_comparison.png',184)
text(75,545,'Both studies found an average gain of about 2 percentage points, but the confidence intervals include zero. We do not yet have clear evidence that switching models improves review.',24,width=1130)
text(75,634,'These results are why we have kept reputation learning on hold.',24,width=1130)

# 04
page('What happened when agents worked with real files','04_workspace_results.png')
text(75,107,'We connected the agents to CSV, JSON, SQLite and PDF files, then examined 36 runs across six tasks.',24,width=1130)
x=75
for count,kind in [(9,'solid'),(14,'outline'),(13,'hatch')]:
    w=1130*count/36
    rect(x,209,w,75,BLUE if kind=='solid' else WHITE,BLUE,1.3)
    if kind=='hatch':
        for xx in range(int(x)+8,int(x+w)-12,15):rule(xx,267,xx+12,225,.8)
        rect(x+w/2-28,224,56,44,WHITE)
    text(x,220,str(count),32,'B',WHITE if kind=='solid' else BLUE,width=w,align='center')
    x+=w
for x,title,body in [
    (75,'Matched the reference','The submitted table matched the expected rows and columns.'),
    (460,'Returned a different table','These outputs needed closer review: the issue could be the chosen field, interpretation or table shape.'),
    (845,'No final table','The agent stopped without a final table, often after spending its budget searching or generating output.')]:
    text(x,316,title,24,'B',BLUE,width=345)
    text(x,372,body,23,width=345)
text(75,556,'The key distinction is between failing to finish and finishing with a result that needs checking. We use the traces to understand which problem occurred before deciding how another agent could help.',24,width=1130)

# 05
page('Three cases we looked at more closely','05_three_cases.png')
for i,(x,title) in enumerate([(70,'Wrong attribute'),(465,'Unclear meaning'),(860,'Extra output column')]):
    circle(x+15,137,15,BLUE)
    text(x,121,str(i+1),18,'B',WHITE,width=30,align='center')
    text(x+43,119,title,25,'B',BLUE,width=310)
text(75,190,'Fund manager nationality',23,'B',width=330)
box(75,249,330,57,'Person name / fund name')
arrow(240,319,240,353)
box(75,366,330,57,'Nationality + correct join')
text(75,456,'We asked for nationality. The query used names as a proxy, even though a Nationality field was available in the source.',23,width=335)
text(470,190,'“Fund abbreviation”',23,'B',width=330)
box(470,249,330,57,'SecuAbbr')
text(470,316,'or',23,width=330,align='center')
box(470,366,330,57,'ChiNameAbbr')
text(470,456,'The source had two plausible abbreviation columns. We need to settle the intended meaning before deciding which answer is correct.',23,width=335)
text(865,190,'Correct names; extra ID',23,'B',width=330)
rect(865,249,330,49,PALE)
text(878,255,'Procedure name',21,'B')
text(1087,255,'ID',21,'B')
rule(1065,249,1065,421)
for y in [322,362,402]:
    rule(880,y+12,1042,y+12,2)
    rule(1088,y+12,1170,y+12,2)
text(865,456,'The names and their order were correct, but an extra ID column caused a mismatch with the expected table.',23,width=335)
text(75,639,'These cases call for different fixes, rather than a single “wrong answer” category.',23,width=1130)

# 06
page('Building checks into the handoff','06_handoff_checker.png')
text(75,107,'We have implemented a checker for SQL queries. It compares the query with the source schema and system-defined requirements, then reports what is satisfied, violated or unresolved.',24,width=1130)
text(75,209,'The review loop we will test next',24,'B',BLUE)
for x,w,title,body in [(75,235,'SQL agent','Writes a query'),(375,235,'Checker','Checks source use'),
                        (675,235,'Reviewer','Reads the findings'),(975,230,'Re-execution','Runs the revised SQL')]:
    box(x,262,w,100,title,body)
for xa,xb in [(310,375),(610,675),(910,975)]:arrow(xa+8,310,xb-8,310)
for x,label in [(388,'Met'),(568,'Violated'),(748,'Unresolved')]:
    rect(x,391,160,42,WHITE,BLUE,1)
    text(x,394,label,21,'B',BLUE,width=160,align='center')
for x,n,label in [(75,'29','New tests'),(470,'87','Tests passed in the scoped suite'),(865,'20/20','SQL outputs reproduced\nbyte for byte')]:
    text(x,460,n,40,'B',BLUE,width=335)
    text(x,518,label,22,width=335)
text(75,602,'The tests cover source binding and handoff consistency. Replaying old SQL reproduced the same output bytes; the next experiment will test whether the checker helps agents correct their work.',23,width=1130)

# 07
page('Preparing a broader SQL evaluation','07_broader_evaluation.png')
text(75,107,'We prepared 204 SpecBridge tasks across 12 databases and split them by database, so we can develop on one group before evaluating on the others.',24,width=1130)
x=75
for count,kind in [(45,'solid'),(67,'hatch'),(92,'outline')]:
    w=1130*count/204
    rect(x,217,w,65,BLUE if kind=='solid' else WHITE,BLUE,1.2)
    if kind=='hatch':
        for xx in range(int(x)+8,int(x+w)-12,15):rule(xx,267,xx+12,231,.7)
        rect(x+w/2-29,228,58,43,WHITE)
    text(x,226,str(count),29,'B',WHITE if kind=='solid' else BLUE,width=w,align='center')
    x+=w
for x,title,body in [(75,'45 for development','Used in the current pilot'),(415,'67 for validation','For the next comparison'),(795,'92 set aside','Kept for final evaluation')]:
    text(x,306,title,24,'B',BLUE,width=335)
    text(x,348,body,22,width=335)
rule(75,405,1205,405)
text(75,438,'90/90',42,'B',BLUE)
text(280,432,'Reference queries matched as expected',26,'B',width=905)
text(280,480,'We also tested wrong interpretations and missing or extra rows. These checks confirmed that the grader rejected the cases it should reject.',23,width=920)
text(75,589,'One task changed score between SQLite versions, so we fixed the execution engine before running the models. The next technical step is to extend the checker to more complex SQL.',23,width=1130)

# 08
page('Self-review did better in the SQL pilot','08_sql_pilot.png')
text(75,107,'We tested Qwen (A) and Gemma (B) on 12 SQL tasks, each with two requested interpretations. The six workflows produced 144 responses in total.',24,width=1130)
image_plot('08_sql_results.png',196)
text(75,564,'Both self-review workflows solved 21 of 24 cases. Cross-model review solved 19 and 20, which was 6.25 percentage points lower on average in this pilot.',24,width=1130)
text(75,644,'We will now test whether specific verification feedback changes this result.',23,width=1130)

# 09
page('Where we take the research next','09_research_direction.png')
rect(65,113,1150,100,PALE)
text(82,123,'Can verification feedback help agents repair an analysis',29,'B',BLUE,width=1110)
text(82,166,'more reliably than asking them to check it again?',29,'B',BLUE,width=1110)
text(75,258,'What we can already study',27,'B',BLUE,width=510)
text(75,314,'We have real traces showing wrong fields, ambiguous requests and incomplete outputs.',24,width=500)
text(75,435,'The checker records why a query meets or breaks a requirement, and what still needs review.',24,width=500)
text(665,258,'What we need to compare',27,'B',BLUE,width=535)
for n,y,body in [(1,314,'Review without diagnostic feedback.'),(2,391,'Review with the checker’s findings.'),(3,468,'Review with shuffled findings.')]:
    text(665,y,str(n)+'.',24,'B',BLUE)
    text(705,y,body,24,width=495)
text(75,589,'We will keep the tools and review budget the same, then repeat the comparison on new databases. We will measure correct completion, repairs, new errors and total cost.',23,width=1130)

# 10
page('Next steps for Tín and Trung','10_next_steps.png')
text(75,107,'We will first agree on what counts as a correct result, then run the next comparison with a fixed protocol.',24,width=1130)
for x,title in [(75,'Tín'),(670,'Trung')]:
    rect(x,195,535,47,BLUE)
    text(x+18,195,title,30,'B',WHITE)
for x,items in [(85,[
    'Extend the checker to handle CTEs and more complex queries.',
    'Run strong single-model, self-review and cross-model baselines with the same tools.',
    'Keep a reproducible record of outputs, token use and running time.']),
    (680,[
    'Review the source data and resolve ambiguous cases using a shared rubric.',
    'Check the proposed contribution against the closest research papers.',
    'Find analysts or students who can try a real reporting workflow.'])]:
    for i,(y,body) in enumerate(zip([266,373,480],items)):
        text(x,y,str(i+1)+'.',23,'B',BLUE)
        text(x+39,y,body,23,width=465)
text(85,570,'Deliverable: checker coverage\nand baseline results',22,'B',BLUE,width=515)
text(680,570,'Deliverable: reviewed cases\nand a pilot workflow',22,'B',BLUE,width=515)
text(75,643,'Together: review cases, freeze the protocol, then test on the databases set aside.',23,width=1130)

# Save images, data provenance, English copy and a convenient image-only ZIP.
assert len(c.doc)==10
for row in c.text_log:
    assert row['box'][3]<=681 or row['box'][1]>=690,('Body/footer overlap',row)
    if row['box'][1]<690:assert row['size']>=18,('Small body copy',row)
outputs=[]
for i,p in enumerate(c.doc):
    destination=SLIDES/c.names[i]
    pix=p.get_pixmap(matrix=fitz.Matrix(2,2),alpha=False)
    assert (pix.width,pix.height)==(2560,1440)
    pix.save(destination)
    outputs.append({'file':destination.relative_to(OUT).as_posix(),'sha256':c.sha(destination)})
sheet=fitz.Pixmap(fitz.csRGB,fitz.IRect(0,0,1600,2250),False)
sheet.clear_with(255)
for i,p in enumerate(c.doc):
    thumb=p.get_pixmap(matrix=fitz.Matrix(.625,.625),alpha=False)
    thumb.set_origin((i%2)*800,(i//2)*450);sheet.copy(thumb,thumb.irect)
sheet.save(OUT/'OVERVIEW.png')
with zipfile.ZipFile(OUT/'RepGuard_10_SLIDES_EN_REVISED.zip','w',compression=zipfile.ZIP_DEFLATED) as z:
    for name in c.names:z.write(SLIDES/name,name)
copy=[]
for n in range(1,11):
    copy.append(f'## Slide {n:02}\n')
    for row in c.text_log:
        if row['slide']==n and row['box'][1]<690:copy.append(row['text'])
    if n==3:copy.append('Chart: cross-model minus self-review, +2.08 pp in both studies; 95% CIs [−0.42, +4.59] and [−4.17, +8.33].')
    if n==8:copy.append('Chart: A18/24, B19/24, AA21/24, BB21/24, AB19/24, BA20/24.')
    copy.append('\n---\n')
(OUT/'SLIDE_CONTENT_EN.md').write_text('\n\n'.join(copy))
(OUT/'generation_receipt.json').write_text(json.dumps({
    'slide_count':10,'format':'PNG','dimensions':[2560,1440],'language':'English',
    'palette':'One blue accent, black and white; blue tints and antialiasing only',
    'changes':'Natural explanatory prose; fuller body copy; no small caveat footnotes; same slide order and academic layout',
    'numeric_results_unchanged':True,'body_text_minimum_size':18,
    'outputs':outputs,'text_layout':c.text_log,
    'sources':{p:c.sha(ROOT/p) for p in ['docs/reports/2026-11-09/verification_v1_summary.json','docs/reports/2026-11-09/arqa_v2_results.json','docs/reports/2026-11-10/specbridge_v6_offline_results.json']},
},ensure_ascii=False,indent=2))
print(json.dumps({'slides':10,'output':str(OUT),'dimensions':[2560,1440]},indent=2))
