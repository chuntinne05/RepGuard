"""Render the two requested standalone English charts using Matplotlib.

Run with the isolated plotting dependencies on PYTHONPATH and a writable
MPLCONFIGDIR. Reads frozen results; never modifies or reruns experiments.
"""
from pathlib import Path
import hashlib
import json

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.ticker import FuncFormatter
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'output/status_update_2026-11-10/charts_en'
OUT.mkdir(parents=True,exist_ok=True)
BLUE = '#1E4E79'
PURPLE = '#7056A5'
GRAY = '#64717C'
INK = '#202A35'
MUTED = '#65717E'
GRID = '#DDE4EC'

plt.rcParams.update({
    'font.family':'DejaVu Sans', 'font.size':16,
    'text.color':INK, 'axes.labelcolor':INK,
    'xtick.color':MUTED,'ytick.color':MUTED,
    'axes.edgecolor':GRID, 'axes.linewidth':1,
    'figure.facecolor':'white','savefig.facecolor':'white',
    'axes.unicode_minus':True,
})

def read(relative):
    return json.loads((ROOT/relative).read_text())

v1_path='docs/reports/2026-11-09/verification_v1_summary.json'
v2_path='docs/reports/2026-11-09/arqa_v2_results.json'
v6_path='docs/reports/2026-11-10/specbridge_v6_offline_results.json'
v1,v2,v6=(read(x) for x in (v1_path,v2_path,v6_path))
assert v6['receipt_audit']=='PASS'

def base(title,subtitle):
    fig=plt.figure(figsize=(16,9),dpi=200)
    fig.text(.055,.94,title,fontsize=27,weight='bold',color=BLUE,va='top')
    fig.text(.055,.875,subtitle,fontsize=15.5,color=MUTED,va='top')
    return fig

def export(fig,name):
    # Keep the requested 16:9 canvas; do not use a tight crop.
    fig.canvas.draw()
    renderer=fig.canvas.get_renderer()
    for item in fig.findobj(matplotlib.text.Text):
        if not item.get_visible() or not item.get_text():continue
        bounds=item.get_window_extent(renderer)
        if not (bounds.x0>=-1 and bounds.y0>=-1 and bounds.x1<=3201 and bounds.y1<=1801):
            raise ValueError(('Text clipped',name,item.get_text(),bounds.bounds))
    p=OUT/name
    fig.savefig(p,dpi=200)
    with Image.open(p) as im:
        assert im.size==(3200,1800)
        im.verify()
    plt.close(fig)
    return {'file':p.name,'size':[3200,1800],'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}

# Slide03: primary contrasts, not the most favorable workflow or secondary arm.
delta=[v1['primary_cross_minus_self_pp'],100*v2['contrasts']['checklist']['delta']]
ci=[v1['claim_cluster_bootstrap95_pp'],[100*x for x in v2['contrasts']['checklist']['ci95']]]
fig=base('Cross-Model Review vs. Self-Review',
         'Balanced average across both model directions | 95% cluster-bootstrap confidence intervals')
ax=fig.add_axes([.325,.345,.43,.39])
ax.set_xlim(-5,10);ax.set_ylim(-.65,1.65)
ax.set_xticks([-5,0,5,10]);ax.set_yticks([])
ax.xaxis.set_major_formatter(FuncFormatter(lambda x,pos: f'+{x:g}' if x>0 else (f'−{abs(x):g}' if x<0 else '0')))
ax.grid(axis='x',color=GRID,linewidth=1,zorder=0)
ax.axvline(0,color=GRAY,lw=1.6,ls=(0,(4,4)),zorder=1)
for side in ['top','right','left']:ax.spines[side].set_visible(False)
ax.tick_params(axis='x',length=0,pad=12,labelsize=16)
for y,point,(low,high) in zip([1,0],delta,ci):
    ax.errorbar(point,y,xerr=[[point-low],[high-point]],fmt='o',
                color=BLUE,ecolor=BLUE,markersize=11,elinewidth=3.1,
                capsize=9,capthick=2,zorder=3)
ax.set_xlabel('Cross-model review − self-review (percentage points)',fontsize=16,labelpad=44)
for y,title,scope in [(1,'Evidence Sufficiency','120 pairs · 24 claim groups'),(0,'Financial Report QA','Checklist · 24 questions · 24 source groups')]:
    yy=fig.transFigure.inverted().transform(ax.transData.transform((0,y)))[1]
    fig.text(.055,yy+.022,title,fontsize=20,weight='bold',va='center')
    fig.text(.055,yy-.032,scope,fontsize=13.2,color=MUTED,va='center')
    index=0 if y==1 else 1
    fig.text(.80,yy+.022,f'{delta[index]:+.2f} pp',fontsize=22,weight='bold',color=BLUE,va='center')
    low,high=ci[index]
    interval=f'[{low:+.2f}, {high:+.2f}]'.replace('-', '−')
    fig.text(.80,yy-.032,interval,fontsize=16,color=MUTED,va='center')
fig.text(.80,.785,'Difference [95% CI]',fontsize=14,color=MUTED)
ax.text(0,-.24,'← Favors self-review',transform=ax.transAxes,fontsize=14,color=MUTED,ha='left')
ax.text(1,-.24,'Favors cross-model review →',transform=ax.transAxes,fontsize=14,color=MUTED,ha='right')
fig.text(.055,.16,'Both 95% confidence intervals include zero.',fontsize=21,weight='bold',color=BLUE)
fig.text(.055,.095,'Separate studies; no pooled effect estimate. Reputation learning remains on hold.',fontsize=14,color=MUTED)
fig.text(.055,.048,'Source: cycle01 and ARQA cycle02 | 9 November 2026',fontsize=12.5,color=MUTED)
outputs=[export(fig,'slide_03_cross_model_vs_self_review_EN.png')]

# Slide08: all six workflows, zero-based count axis, no invented uncertainty.
workflows=['A','B','AA','BB','AB','BA']
correct=[v6['workflows'][w]['passed'] for w in workflows]
totals=[v6['workflows'][w]['cases'] for w in workflows]
assert correct==[18,19,21,21,19,20] and totals==[24]*6
gap=100*((correct[4]+correct[5])-(correct[2]+correct[3]))/(2*24)
assert gap==100*v6['balanced_cross_minus_self_descriptive']==-6.25
fig=base('Latest SQL Pilot: Correct Cases by Workflow',
         '12 tasks × 2 specified interpretations = 24 cases | 3 development databases | 144 model responses')
ax=fig.add_axes([.075,.30,.85,.43])
positions=[0,1,2.5,3.5,5,6]
colors=[GRAY,GRAY,BLUE,BLUE,PURPLE,PURPLE]
bars=ax.bar(positions,correct,color=colors,width=.65,zorder=3)
ax.set_ylim(0,24);ax.set_yticks([0,6,12,18,24]);ax.set_xlim(-.65,6.65)
ax.set_xticks(positions,workflows,fontsize=19,weight='bold')
ax.tick_params(axis='x',length=0,pad=12);ax.tick_params(axis='y',length=0,pad=10,labelsize=15)
ax.set_ylabel('Correct cases (out of 24)',fontsize=16,labelpad=14)
ax.grid(axis='y',color=GRID,linewidth=1,zorder=0)
for side in ['top','right','left']:ax.spines[side].set_visible(False)
for bar,value in zip(bars,correct):
    ax.text(bar.get_x()+bar.get_width()/2,value+.55,f'{value}/24',
            fontsize=18,weight='bold',color=bar.get_facecolor(),ha='center',va='bottom')
fig.legend(handles=[Patch(facecolor=GRAY,label='Direct generation'),Patch(facecolor=BLUE,label='Self-review'),
                    Patch(facecolor=PURPLE,label='Cross-model review')],
           loc='upper left',bbox_to_anchor=(.066,.817),ncol=3,frameon=False,
           fontsize=15,handlelength=1.1,columnspacing=2.0)
ax.set_xlabel('Workflow',fontsize=16,labelpad=13)
fig.text(.055,.17,'Cross-model review − self-review: −6.25 percentage points',fontsize=21,weight='bold',color=PURPLE)
fig.text(.055,.123,'Balanced average across both directions; descriptive development-set result.',fontsize=14,color=MUTED)
fig.text(.055,.080,'A = Qwen; B = Gemma. Variants are dependent within 12 tasks; equal call ceilings do not imply equal actual cost.',fontsize=12.3,color=MUTED)
fig.text(.055,.043,'No held-out-source confirmation. This pilot does not test the V5 checker.',fontsize=12.8,color=MUTED)
outputs.append(export(fig,'slide_08_latest_sql_pilot_EN.png'))

receipt={
 'library':'Matplotlib','library_version':matplotlib.__version__,
 'format':'PNG','size':[3200,1800],'aspect_ratio':'16:9','language':'English',
 'sources':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in (v1_path,v2_path,v6_path)},
 'slide03':{'balanced_cross_minus_self_pp':delta,'cluster_bootstrap95_pp':ci,'pooled_effect':False},
 'slide08':{'workflows':workflows,'correct':correct,'denominators':totals,'cross_minus_self_pp':gap,
            'scope':'Development pilot;12tasks/24dependent variants/3databases; not V5 checker efficacy'},
 'outputs':outputs,'checks':{'text_within_canvas':'PASS','png_size':'PASS','source_values':'PASS'},
}
(OUT/'chart_sources_and_checks.json').write_text(json.dumps(receipt,indent=2))
print(json.dumps(outputs,indent=2))
