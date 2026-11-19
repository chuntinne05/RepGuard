"""Draw the requested ten PNG slides, matching the supplied Beamer reference.

PNG-only deliverable. PyMuPDF supplies vector drawing, Unicode typesetting and
rasterization; no presentation/PDF file is exported. All results are read-only.
Run with PYTHONPATH pointing at the isolated PyMuPDF dependency directory.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import math
import os
import re
import shutil
import zipfile

import pymupdf as fitz

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'output/status_update_2026-11-10'
SLIDES = OUT / 'slides'
TMP = ROOT / 'tmp/status_update_2026-11-10'
REFERENCE = Path('/Users/trinhtrantrungtin/Downloads/DACN_27_10_Group8.pdf')
FONTDIR = Path('/usr/local/texlive/2025basic/texmf-dist/fonts/opentype/public/lm')
FONTS = {k:FONTDIR/f'lmsans10-{v}.otf' for k,v in [('R','regular'),('B','bold'),('I','oblique')]}
FONT = {k:fitz.Font(fontfile=str(p)) for k,p in FONTS.items()}
W,H = 1280,720
BLUE = (0.118,0.306,0.475)
NAVY = (0.088,0.229,0.356)
DARK = (0.059,0.153,0.237)
INK = (0.10,0.13,0.17)
GRAY = (0.38,0.42,0.46)
LIGHT = (0.909,0.923,0.936)
LINE = (0.80,0.84,0.88)
GREEN = (0.16,0.46,0.38)
MINT = (0.87,0.95,0.90)
PURPLE = (0.43,0.35,0.65)
LAVENDER = (0.93,0.90,0.97)
ORANGE = (0.73,0.39,0.15)
CREAM = (0.99,0.94,0.85)
RED = (0.69,0.25,0.24)
ROSE = (0.98,0.90,0.89)
WHITE = (1,1,1)

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

doc = fitz.open()
text_log = []
current = None

def rect(x,y,w,h,fill=WHITE,stroke=None,width=1):
    current.draw_rect(fitz.Rect(x,y,x+w,y+h),color=stroke,fill=fill,width=width)

def line(x1,y1,x2,y2,color=LINE,width=1,dash=None):
    current.draw_line((x1,y1),(x2,y2),color=color,width=width,dashes=dash)

def circle(x,y,r,fill=BLUE,stroke=None,width=1):
    current.draw_circle((x,y),r,color=stroke,fill=fill,width=width)

def wrap(text,size,width,font='R'):
    lines=[]
    for para in text.split('\n'):
        row=''
        for word in para.split():
            nxt=(row+' '+word).strip()
            if FONT[font].text_length(nxt,fontsize=size) > width and row:
                lines.append(row);row=word
            else:row=nxt
        lines.append(row)
    return lines

def text(x,y,value,size=24,font='R',color=INK,width=None,align='left',leading=1.27):
    """Coordinates are the top of the actual font metric box."""
    rows=wrap(str(value),size,width,font) if width else str(value).split('\n')
    for i,row in enumerate(rows):
        missing={c for c in row if not FONT[font].has_glyph(ord(c))}
        if missing:
            raise ValueError(('Unsupported glyph',font,missing,row))
        length=FONT[font].text_length(row,fontsize=size)
        dx=0
        if align=='center':dx=((width or 0)-length)/2
        elif align=='right':dx=(width or 0)-length
        yy=y+i*size*leading
        baseline=yy+FONT[font].ascender*size
        current.insert_text((x+dx,baseline),row,fontname=font,fontsize=size,color=color)
        bounds=(x+dx,yy,x+dx+length,baseline-FONT[font].descender*size)
        if bounds[0] < -0.1 or bounds[2] > W+0.1 or bounds[1] < -0.1 or bounds[3] > H+0.1:
            raise ValueError(('Text outside canvas',len(doc),row,bounds))
        if width is not None and length > width+0.1:
            raise ValueError(('Unbreakable overflow',len(doc),row,length,width))
        text_log.append({'slide':len(doc),'text':row,'size':size,'box':[round(z,2) for z in bounds]})
    return y+len(rows)*size*leading

def arrow(x1,y1,x2,y2,color=BLUE,width=1.8):
    line(x1,y1,x2,y2,color,width)
    a=math.atan2(y2-y1,x2-x1)
    for d in (-.45,.45):
        line(x2,y2,x2-10*math.cos(a+d),y2-10*math.sin(a+d),color,width)

def numbered(x,y,n,label,subtitle=None,width=490):
    circle(x,y+18,15,BLUE)
    text(x-15,y+3,str(n),18,'B',WHITE,width=30,align='center')
    text(x+35,y,label,27,'B',width=width)
    if subtitle:text(x+35,y+44,subtitle,22,color=GRAY,width=width)

def block(x,y,w,title,body,body_size=23):
    rect(x+4,y+4,w,92,fill=(.86,.87,.88))
    rect(x,y,w,37,NAVY)
    rect(x,y+37,w,55,LIGHT)
    text(x+13,y+1,title,25,'B',WHITE,width=w-26)
    text(x+13,y+41,body,body_size,width=w-26)

def panel(x,y,w,h,title,fill=LIGHT,title_color=BLUE):
    rect(x,y,w,h,fill,LINE,.8)
    text(x+15,y+10,title,22,'B',title_color,width=w-30)

def note(value):
    text(65,653,value,14,color=GRAY,width=1150)

def takeaway(value):
    rect(65,587,1150,49,LIGHT)
    text(79,592,value,23,'B',BLUE,width=1122)

def new_slide(title,filename):
    global current
    current=doc.new_page(width=W,height=H)
    for key,path in FONTS.items():current.insert_font(fontname=key,fontfile=str(path))
    # Reuse the reference's decorative background, never its research content.
    current.insert_image(current.rect,stream=background)
    # The title band covers the top university logo. Remove the bottom logo.
    rect(1200,635,80,60,WHITE)
    rect(0,0,W,76.8,BLUE)
    size=35
    if FONT['B'].text_length(title,fontsize=size)>1214:
        raise ValueError(('Title too long',title))
    text(24,13,title,size,'B',WHITE)
    for x,c in [(0,DARK),(W/3,NAVY),(2*W/3,BLUE)]:rect(x,695,W/3,25,c)
    text(0,696,'Tín & Trung',13,'B',WHITE,width=W/3,align='center')
    text(W/3,696,'RepGuard · Progress Update',13,'B',WHITE,width=W/3,align='center')
    text(2*W/3+15,696,'10 Nov 2026',13,'B',WHITE,width=210,align='center')
    text(1160,696,f'{len(doc)} / 10',13,'B',WHITE,width=95,align='right')
    names.append(filename)



def start():
    global background, names
    ref=fitz.open(REFERENCE)
    full=[x for x in ref[2].get_images(full=True) if x[2]==1600 and x[3]==900]
    assert len(full)==1
    background=ref.extract_image(full[0][0])["image"]
    names=[]
    ref.close()
