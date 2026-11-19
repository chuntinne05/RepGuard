"""Create all10 English PNG slides using the existing academic design.

PYTHONPATH=/private/tmp/repguard-pdf-deps:/private/tmp/repguard-chart-deps:. \
  .venv/bin/python -m research_ops.presentations.build_progress_20261110_en
"""
from pathlib import Path
import hashlib
import json
import re
import zipfile
from PIL import Image
import pymupdf as fitz

from . import progress_slide_canvas as c

ROOT=c.ROOT
OUT=ROOT/'output/status_update_2026-11-10'
SLIDES=OUT/'slides_en'
ASSETS=ROOT/'tmp/status_update_2026-11-10/english_assets'
SLIDES.mkdir(parents=True,exist_ok=True)
ASSETS.mkdir(parents=True,exist_ok=True)
c.start()
text,rect,line,circle,arrow=c.text,c.rect,c.line,c.circle,c.arrow
numbered,block,panel,note,takeaway=c.numbered,c.block,c.panel,c.note,c.takeaway
new_slide=c.new_slide
BLUE,NAVY,DARK,INK,GRAY,LIGHT,LINE,GREEN,MINT,PURPLE,LAVENDER,ORANGE,CREAM,RED,ROSE,WHITE=(
    c.BLUE,c.NAVY,c.DARK,c.INK,c.GRAY,c.LIGHT,c.LINE,c.GREEN,c.MINT,c.PURPLE,c.LAVENDER,c.ORANGE,c.CREAM,c.RED,c.ROSE,c.WHITE)

# Reuse the audited Matplotlib plots. Crop the plotting panels only; titles,
# takeaways and caveats are typeset in the slide's Latin Modern Sans theme.
chart_receipt=json.loads((OUT/'charts_en/chart_sources_and_checks.json').read_text())
for item in chart_receipt['outputs']:
    p=OUT/'charts_en'/item['file']
    assert c.sha(p)==item['sha256']
with Image.open(OUT/'charts_en/slide_03_cross_model_vs_self_review_EN.png') as im:
    im.crop((0,324,3200,1440)).save(ASSETS/'chart03_panel.png')
with Image.open(OUT/'charts_en/slide_08_latest_sql_pilot_EN.png') as im:
    im.crop((0,297,3200,1350)).save(ASSETS/'chart08_panel.png')
v6=json.loads((ROOT/'docs/reports/2026-11-10/specbridge_v6_offline_results.json').read_text())
assert [v6['workflows'][w]['passed'] for w in ['A','B','AA','BB','AB','BA']]==[18,19,21,21,19,20]

# 01
new_slide('Agenda','01_agenda_EN.png')
block(65,119,1150,'Update Since the 27–28 October Report',
      'From experimental results to the research question and next validation steps.')
numbered(92,265,1,'Completed Work','Four evaluation settings; a new verification layer.')
numbered(92,418,2,'Results and Lessons Learned','Cross-model review, data errors and grading limitations.')
numbered(690,265,3,'Research Direction','Existing foundations and evidence still needed.',width=450)
numbered(690,418,4,'Next Steps','Tasks for Tín and Trung; conditions for proceeding.',width=450)
note('Reporting period: from the late-October update through 10 November 2026.')

# 02
new_slide('Progress Since the Previous Report','02_progress_since_last_report_EN.png')
text(75,112,'1,265',53,'B',BLUE)
text(265,128,'new model responses · 4 evaluation settings',28,'B',width=915)
line(75,205,1205,205,LINE)
items=[('720','Evidence Sufficiency','120 pairs · 24 groups',BLUE),
       ('288','Financial Report QA','24 questions · 2 prompt profiles',GREEN),
       ('113','Data Workspace','6 tasks · 36 trajectories',ORANGE),
       ('144','SQL with Specified\nInterpretations','12 tasks · 24 cases',PURPLE)]
for i,(count,title,scope,color) in enumerate(items):
    x=75+i*290
    circle(x+17,250,7,color)
    if i<3:line(x+24,250,x+290,250,LINE,2)
    text(x,280,count,43,'B',color,width=265)
    text(x,350,title,23,'B',width=270)
    text(x,427,scope,18,color=GRAY,width=270)
text(76,483,'Parallel Development',23,'B',BLUE)
text(76,522,'Constraint and source verification + evidence for agent handoffs',28,'B',width=1130)
takeaway('New focus: explicitly verify requirements, data and evidence status.')
note('Responses are not independent tasks. Excludes the previous 18,064 MMLU-Pro responses and 560 repair responses.')

# 03: Matplotlib forest plot, preserving primary contrast and confidence bounds.
new_slide('First Two Studies: Cross-Model Advantage Is Unclear','03_cross_model_vs_self_review_EN.png')
text(75,107,'Cross-Model Review − Self-Review',29,'B',width=1125)
text(75,151,'Balanced average across both directions · percentage points · 95% confidence intervals',21,color=GRAY,width=1125)
c.current.insert_image(fitz.Rect(65,194,1215,595.075),filename=str(ASSETS/'chart03_panel.png'))
rect(65,604,1150,39,LIGHT)
text(79,607,'Both intervals include zero; reputation learning remains on hold.',23,'B',BLUE,width=1122)
note('Source: cycle01 and ARQA cycle02, 9 Nov. Separate studies; no pooled effect. Financial Report QA uses the checklist contrast.')

# 04
new_slide('Real Data Workspaces: Measure Task Completion Too','04_real_data_workspaces_EN.png')
text(75,112,'113 responses',39,'B',BLUE)
text(460,126,'6 tasks · 36 trajectories · CSV / JSON / SQLite / PDF',23,'B',width=735)
text(75,200,'Output outcomes across all 36 trajectories',24,'B')
x=75
for count,color in [(9,GREEN),(14,ORANGE),(13,GRAY)]:
    width=1130*count/36
    rect(x,259,width,74,color)
    text(x,271,str(count),32,'B',WHITE,width=width,align='center')
    x+=width
for x,title,body,color in [
    (75,'Match the reference','Correct under strict\nrelation matching.',GREEN),
    (460,'Table produced, no match','Distinguish content, interpretation\nand output-shape errors.',ORANGE),
    (845,'No final table','Source discovery, budget or\noutput-length issues remain.',GRAY)]:
    text(x,365,title,24,'B',color,width=345)
    text(x,418,body,22,width=345)
takeaway('Distinguish “unfinished” from “output produced but requirements not met.”')
note('Adapted DataSpace tasks; diagnostic results from two collection blocks affected by interruptions. Not an official confirmatory score.')

# 05
new_slide('Three Error Types to Distinguish','05_three_error_types_EN.png')
for i,(x,title,color) in enumerate([(70,'Wrong Attribute',BLUE),(465,'Unresolved Interpretation',PURPLE),(860,'Extra Output Column',ORANGE)]):
    circle(x+15,137,15,color)
    text(x,121,str(i+1),18,'B',WHITE,width=30,align='center')
    text(x+43,119,title,24,'B',color,width=310)
text(75,202,'Fund manager nationality',23,'B',width=330)
panel(75,261,330,66,'Person name / fund name',ROSE,RED)
text(84,339,'Used as a proxy for nationality',19,color=RED,width=315)
arrow(240,378,240,414,GRAY)
panel(75,430,330,66,'Nationality + correct join',MINT,GREEN)
text(75,520,'Verify the field and the join.',20,width=335)
text(470,202,'“Fund abbreviation”',23,'B',width=330)
panel(470,273,330,63,'SecuAbbr',LAVENDER,PURPLE)
text(470,349,'or',22,color=GRAY,width=330,align='center')
panel(470,399,330,63,'ChiNameAbbr',LAVENDER,PURPLE)
text(470,500,'Interpretation needs adjudication.',20,width=330)
text(865,202,'Correct names; extra ID',23,'B',width=330)
rect(865,273,330,49,LIGHT)
text(880,280,'Procedure name',20,'B')
text(1083,280,'ID',20,'B',RED)
line(1060,273,1060,428,LINE)
for y in [331,370,409]:
    line(881,y+13,1037,y+13,BLUE,3)
    line(1085,y+13,1168,y+13,RED,3)
text(865,468,'Strict relation: no match',20,'B',ORANGE,width=330)
text(865,509,'Keep the original score.',20,width=330)
takeaway('Correctness requires clear requirements and evidence tied to the right sources.')
note('Tasks 380 / 371 / 44; development analysis, no independent semantic adjudication. Gold references are not revised to fit model outputs.')

# 06
new_slide('Verification and Handoff Layer Implemented','06_verification_and_handoff_EN.png')
text(75,110,'Host-Managed Constraints + Source Catalog',27,'B',BLUE,width=1125)
text(75,153,'Verification layer implemented; the diagram shows its integration flow with agents.',21,color=GRAY,width=1125)
for x,w,title,body,fill,color in [
    (75,235,'SQL Generator','Actual draft',LIGHT,BLUE),
    (375,235,'Verification Layer','Query + source',MINT,GREEN),
    (675,235,'Reviewer Agent','Receives evidence',LAVENDER,PURPLE),
    (975,230,'Re-execution','Output artifact',CREAM,ORANGE)]:
    panel(x,215,w,94,title,fill,color)
    text(x+15,265,body,19,width=w-30)
for xa,xb in [(310,375),(610,675),(910,975)]:arrow(xa+8,261,xb-8,261)
for x,title,fill,color in [(380,'Met',MINT,GREEN),(563,'Violated',ROSE,RED),(746,'Unresolved',CREAM,ORANGE)]:
    rect(x,348,173,46,fill)
    text(x,354,title,19,'B',color,width=173,align='center')
line(75,433,1205,433,LINE)
for x,value,label in [(75,'29','New tests'),(470,'87','Scoped tests passed'),(865,'20/20','Byte-identical SQL replays')]:
    text(x,461,value,42,'B',BLUE,width=335)
    text(x,521,label,23,width=335)
takeaway('Reproducible component implemented; error-correction gains need a separate experiment.')
note('V5 supports a SQL subset; development contracts need independent review. Reproducing 20/20 outputs does not mean 20/20 correct answers.')

# 07
new_slide('Evaluation Setup for New Databases','07_evaluation_on_new_databases_EN.png')
text(75,111,'204 tasks · 12 databases',34,'B',BLUE)
text(75,163,'Pinned SpecBridge revision · split by database',21,color=GRAY)
x=75
for count,color,tc in [(45,BLUE,WHITE),(67,(.59,.79,.72),INK),(92,(.78,.73,.87),INK)]:
    width=1130*count/204
    rect(x,225,width,65,color)
    text(x,237,str(count),28,'B',tc,width=width,align='center')
    x+=width
for x,title,body in [(75,'Development','45 tasks · opened'),(415,'Validation','67 tasks · not yet evaluated'),(795,'Reserved','92 tasks · not yet evaluated')]:
    text(x,306,title,23,'B',BLUE,width=330)
    text(x,344,body,21,color=GRAY,width=330)
line(75,399,1205,399,LINE)
text(75,425,'90/90',42,'B',GREEN)
text(280,431,'Reference SQL queries passed grader qualification',25,'B',width=875)
text(280,476,'Controls rejected: wrong interpretation / extra row / missing output.',20,width=875)
takeaway('Pin grader and engine: 1 task’s score changed between SQLite 3.42 and 3.51.')
note('Qualification checks the grader. 74/90 reference queries contain CTEs or multiple query scopes, not fully covered by the current V5 checker.')

# 08: Matplotlib bar plot, zero-based y-axis, all six workflows retained.
new_slide('Latest SQL Pilot: Self-Review Scored Higher','08_latest_sql_pilot_EN.png')
text(75,107,'12 tasks × 2 specified interpretations = 24 cases',27,'B',width=1125)
text(75,151,'3 development databases · 144 model responses · audit PASS',21,color=GRAY,width=1125)
c.current.insert_image(fitz.Rect(65,198,1215,576.42),filename=str(ASSETS/'chart08_panel.png'))
takeaway('Cross-model review − self-review: −6.25 percentage points, averaged across both directions.')
note('Development only; no held-out confirmation or V5 checker test. A=Qwen; B=Gemma. Variants depend on 12 tasks; same call cap is not equal cost.')

# 09
new_slide('Research Question for Further Validation','09_research_question_EN.png')
rect(65,116,1150,101,LIGHT)
text(82,128,'Do verified handoffs improve correction accuracy',29,'B',BLUE,width=1110)
text(82,169,'with the same sources, tools and budget?',29,'B',BLUE,width=1110)
text(80,259,'Existing Foundations',27,'B',BLUE)
text(80,311,'• Source-traceable error bank\n• Verifier + reproducible execution logs',23,width=470,leading=1.8)
text(658,259,'Isolating the Added Benefit',27,'B',BLUE,width=540)
text(658,311,'• Self-review / neutral recheck\n• Correct / shuffled diagnostic feedback\n• Same checker; new-source validation',23,width=545,leading=1.8)
line(80,480,1200,480,LINE)
text(80,503,'Measure',23,'B',BLUE)
text(270,503,'Correct completion · rescues/harms · false stops · coverage · total cost',23,width=930)
takeaway('Target contributions: adjudicated error bank + tooling + controlled evidence.')
note('Contracts/handoffs have close prior work. Novelty not established; strong baselines, independent adjudication and user evaluation remain missing.')

# 10
new_slide('Next Steps and Task Allocation','10_next_steps_tin_trung_EN.png')
text(75,108,'Proposed task allocation · priorities depend on readiness',23,color=GRAY)
rect(75,166,535,49,NAVY)
rect(670,166,535,49,BLUE)
text(95,169,'Tín',30,'B',WHITE)
text(690,169,'Trung',30,'B',WHITE)
for x,rows in [(85,[('01','Measure / extend SQL coverage'),('02','Strong baselines + same tools/checker'),('03','Harness + token / timing logs')]),
               (680,[('01','Source-only review + rubric'),('02','Compare contributions with prior work'),('03','Find workflow + recruit pilot users')])]:
    for j,(number,label) in enumerate(rows):
        y=244+j*68
        text(x,y,number,22,'B',BLUE)
        text(x+48,y,label,23,width=460)
text(85,468,'Deliverables: coverage + reproducible baselines',20,'B',BLUE,width=520)
text(680,468,'Deliverables: review forms + pilot workflow',20,'B',BLUE,width=520)
line(75,527,1205,527,LINE)
text(75,548,'Joint Work',22,'B',BLUE)
text(300,548,'Peer review → freeze protocol → test mechanism → held-out sources',23,width=895)
takeaway('Next: clear evaluation requirements and strong controls before scaling up.')
note('No user participants yet. Held-out-source evaluation follows mechanism freeze and readiness checks.')

# Validate content and export full-size individual images.
assert len(c.doc)==len(c.names)==10
for row in c.text_log:
    assert row['box'][3]<=695 or row['box'][1]>=695,('Footer overlap',row)
    assert not re.search('[ăâđêôơưĂÂĐÊÔƠƯ]',row['text']),('Vietnamese residue',row['text'])
outputs=[]
for i,page in enumerate(c.doc):
    destination=SLIDES/c.names[i]
    pix=page.get_pixmap(matrix=fitz.Matrix(2,2),alpha=False)
    assert (pix.width,pix.height)==(2560,1440)
    pix.save(destination)
    outputs.append({'file':destination.relative_to(OUT).as_posix(),'width':2560,'height':1440,'sha256':c.sha(destination)})
sheet=fitz.Pixmap(fitz.csRGB,fitz.IRect(0,0,1600,2250),False)
sheet.clear_with(255)
for i,page in enumerate(c.doc):
    thumb=page.get_pixmap(matrix=fitz.Matrix(.625,.625),alpha=False)
    thumb.set_origin((i%2)*800,(i//2)*450)
    sheet.copy(thumb,thumb.irect)
sheet.save(OUT/'OVERVIEW_10_SLIDES_EN.png')
with zipfile.ZipFile(OUT/'RepGuard_10_SLIDES_EN_PNG_16x9.zip','w',compression=zipfile.ZIP_DEFLATED) as z:
    for name in c.names:z.write(SLIDES/name,name)
receipt={
    'language':'English; personal names preserved', 'size':[2560,1440], 'slide_count':10,
    'design':'Same reference background, palette, Latin Modern Sans, header and footer as the Vietnamese images',
    'content_source':{'path':'output/status_update_2026-11-10/SLIDE_CONTENT_EN.md','sha256':c.sha(OUT/'SLIDE_CONTENT_EN.md')},
    'chart_source':{'path':'output/status_update_2026-11-10/charts_en/chart_sources_and_checks.json','sha256':c.sha(OUT/'charts_en/chart_sources_and_checks.json')},
    'outputs':outputs,'text_layout':c.text_log,
    'checks':{'text_within_canvas':'PASS','glyph_coverage':'PASS','footer_separation':'PASS','Vietnamese_words_except_names':'NONE'},
    'original_Vietnamese_images_modified':False,
}
(OUT/'generation_receipt_EN.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2))
print(json.dumps({'slide_count':10,'image_size':[2560,1440],'files':[x['file'] for x in outputs]},indent=2))
