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
    size=36
    if FONT['B'].text_length(title,fontsize=size)>1214:
        raise ValueError(('Title too long',title))
    text(24,13,title,size,'B',WHITE)
    for x,c in [(0,DARK),(W/3,NAVY),(2*W/3,BLUE)]:rect(x,695,W/3,25,c)
    text(0,696,'Tín & Trung',13,'B',WHITE,width=W/3,align='center')
    text(W/3,696,'RepGuard · Cập nhật tiến độ',13,'B',WHITE,width=W/3,align='center')
    text(2*W/3+15,696,'10/11/2026',13,'B',WHITE,width=210,align='center')
    text(1160,696,f'{len(doc)} / 10',13,'B',WHITE,width=95,align='right')
    names.append(filename)

SLIDES.mkdir(parents=True,exist_ok=True)
TMP.mkdir(parents=True,exist_ok=True)
ref=fitz.open(REFERENCE)
images=ref[2].get_images(full=True)
full=[x for x in images if x[2]==1600 and x[3]==900]
assert len(full)==1
background=ref.extract_image(full[0][0])['image']
v6=json.loads((ROOT/'results/specbridge_v6/offline_results.json').read_text())
assert v6['receipt_audit']=='PASS' and v6['actual_model_calls']==144
assert [v6['workflows'][k]['passed'] for k in ['A','B','AA','BB','AB','BA']]==[18,19,21,21,19,20]
assert v6['execution_replay_matches']==144
assert 720+288+113+v6['actual_model_calls']==1265
names=[]

# 01: Agenda. Keep the academic, sparse numbered structure from the template.
new_slide('Nội dung báo cáo','01_agenda.png')
block(65,119,1150,'Cập nhật sau báo cáo 27–28/10','Từ kết quả thực nghiệm đến câu hỏi nghiên cứu và bước xác nhận tiếp theo.')
numbered(92,265,1,'Tiến độ đã hoàn tất','Bốn bối cảnh đánh giá; hệ thống kiểm chứng mới.')
numbered(92,418,2,'Kết quả và bài học','Kiểm chéo, lỗi dữ liệu và giới hạn phép chấm.')
numbered(690,265,3,'Hướng nghiên cứu','Phần đã có và bằng chứng còn cần bổ sung.',width=450)
numbered(690,418,4,'Kế hoạch tiếp theo','Phân công Tín và Trung; điều kiện chạy tiếp.',width=450)
note('Kỳ báo cáo: sau bản cập nhật cuối tháng 10 đến 10/11/2026.')

# 02: All counts are incremental, never cumulative old corpus counts.
new_slide('Tiến độ mới kể từ báo cáo trước','02_tien_do_moi.png')
text(75,112,'1.265',53,'B',BLUE)
text(265,128,'phản hồi mô hình mới · 4 bối cảnh đánh giá',28,'B',width=915)
line(75,205,1205,205,LINE)
items=[('720','Kiểm bằng chứng','120 cặp · 24 nhóm',BLUE),('288','Hỏi đáp báo cáo','24 câu · 2 profiles',GREEN),('113','Workspace dữ liệu','6 task · 36 trajectory',ORANGE),('144','SQL có chỉ định','12 task · 24 trường hợp',PURPLE)]
for i,(count,title,desc,c) in enumerate(items):
    x=75+i*290
    circle(x+17,250,7,c)
    if i<3:line(x+24,250,x+290,250,LINE,2)
    text(x,280,count,43,'B',c,width=265)
    text(x,346,title,24,'B',width=270)
    text(x,386,desc,19,color=GRAY,width=270)
text(76,464,'Phát triển song song',23,'B',BLUE)
text(76,505,'Lớp kiểm ràng buộc + nguồn + bằng chứng bàn giao',30,'B',width=1130)
takeaway('Trọng tâm mới: kiểm rõ yêu cầu, dữ liệu và trạng thái bằng chứng.')
note('Số phản hồi không đồng nghĩa số task độc lập. Không tính lại 18.064 phản hồi MMLU-Pro và 560 phản hồi repair cũ.')

# 03: Scientific forest plot, labels contain the exact reported intervals.
new_slide('Hai vòng đầu: lợi thế kiểm chéo chưa rõ','03_kiem_cheo_va_tu_kiem.png')
text(75,113,'Chênh lệch kiểm chéo − tự kiểm',29,'B',width=1100)
text(75,160,'Trung bình cân bằng hai hướng · điểm phần trăm · CI 95%',20,color=GRAY)
x0,x1=450,1000
def xp(v):return x0+(v+5)/15*(x1-x0)
for tick in [-5,0,5,10]:
    line(xp(tick),238,xp(tick),495,LINE if tick else GRAY,1 if tick else 1.5,'[4 4]' if tick==0 else None)
    text(xp(tick)-30,506,f'{tick:+}' if tick else '0',19,color=GRAY,width=60,align='center')
for y,label,desc,lo,hi in [(300,'Kiểm bằng chứng','120 cặp / 24 nhóm',-.4167,4.59375),(430,'Hỏi đáp báo cáo','24 câu / 24 nhóm',-4.1667,8.3333)]:
    text(80,y-36,label,25,'B',width=345)
    text(80,y+7,desc,20,color=GRAY,width=345)
    line(xp(lo),y,xp(hi),y,BLUE,4)
    for value in [lo,hi]:line(xp(value),y-10,xp(value),y+10,BLUE,2)
    circle(xp(2.0833),y,8,BLUE)
    text(1030,y-35,'+2,08',29,'B',BLUE,width=170)
    ss=f'[{lo:.2f}; +{hi:.2f}]'.replace('.',',').replace('-', '−')
    text(1030,y+7,ss,18,color=GRAY,width=180)
text(459,546,'← Tự kiểm tốt hơn',18,color=GRAY)
text(790,546,'Kiểm chéo tốt hơn →',18,color=GRAY)
takeaway('Cả hai khoảng tin cậy đi qua 0; chưa mở rộng học reputation.')
note('Nguồn: cycle01 và ARQA cycle02, 09/11. Hai nghiên cứu riêng; không gộp để suy ra một hiệu quả chung.')

# 04: Three disjoint outcomes, never call the 27 nonmatches business errors.
new_slide('Workspace thật: cần đo cả việc hoàn thành','04_workspace_that.png')
text(75,112,'113 phản hồi',39,'B',BLUE)
text(460,126,'6 task · 36 trajectory · CSV / JSON / SQLite / PDF',23,'B',width=735)
text(75,200,'Kết quả đầu ra trên toàn bộ 36 trajectory',24,'B')
segments=[(9,GREEN),(14,ORANGE),(13,GRAY)]
x=75
for n,c in segments:
    width=1130*n/36
    rect(x,259,width,74,c)
    text(x,271,str(n),32,'B',WHITE,width=width,align='center')
    x+=width
for x,n,title,desc,c in [(75,9,'Khớp reference','Đúng theo phép chấm\nstrict relation.',GREEN),(460,14,'Có bảng, chưa khớp','Cần phân loại lỗi nội dung,\ncách hiểu và hình dạng.',ORANGE),(845,13,'Chưa có bảng cuối','Tìm nguồn, budget hoặc\nđộ dài đầu ra còn vướng.',GRAY)]:
    text(x,365,title,24,'B',c,width=345)
    text(x,418,desc,22,width=345)
takeaway('Tách “chưa hoàn tất” khỏi “có đầu ra nhưng chưa đúng yêu cầu”.')
note('DataSpace đã thích nghi; tổng hợp chẩn đoán từ 2 block có gián đoạn. Không phải score xác nhận chính thức.')

# 05: Three error categories illustrated, with no reconstructed fake SQL.
new_slide('Ba kiểu lỗi cần được tách riêng','05_ba_kieu_loi.png')
cols=[(70,'Sai thuộc tính',BLUE),(465,'Cách hiểu còn mở',PURPLE),(860,'Thừa cột đầu ra',ORANGE)]
for i,(x,title,c) in enumerate(cols):
    circle(x+15,137,15,c)
    text(x,121,str(i+1),18,'B',WHITE,width=30,align='center')
    text(x+43,119,title,26,'B',c,width=310)
text(75,202,'Quốc tịch người quản lý',23,'B',width=330)
panel(75,261,330,66,'Tên người / tên quỹ',ROSE,RED)
text(84,339,'Đã được dùng làm proxy',19,color=RED,width=315)
arrow(240,378,240,414,GRAY)
panel(75,430,330,66,'Nationality + đúng join',MINT,GREEN)
text(75,520,'Cần kiểm trường và liên kết.',20,width=335)
text(470,202,'“Fund abbreviation”',23,'B',width=330)
panel(470,273,330,63,'SecuAbbr',LAVENDER,PURPLE)
text(470,349,'hay',22,color=GRAY,width=330,align='center')
panel(470,399,330,63,'ChiNameAbbr',LAVENDER,PURPLE)
text(470,500,'Cần thẩm định cách hiểu.',20,width=330)
text(865,202,'Chuỗi tên đúng, dư ID',23,'B',width=330)
rect(865,273,330,49,LIGHT)
text(880,280,'Tên thủ tục',20,'B')
text(1083,280,'ID',20,'B',RED)
line(1060,273,1060,428,LINE)
for yy in [331,370,409]:
    line(881,yy+13,1037,yy+13,BLUE,3)
    line(1085,yy+13,1168,yy+13,RED,3)
text(865,468,'Strict relation: không khớp',20,'B',ORANGE,width=330)
text(865,509,'Giữ nguyên điểm gốc.',20,width=330)
takeaway('Kiểm tính đúng đòi hỏi yêu cầu rõ và bằng chứng gắn đúng nguồn.')
note('Task 380 / 371 / 44; phân tích phát triển, chưa có thẩm định ngữ nghĩa độc lập. Không sửa gold theo model.')

# 06: Implemented architecture, checker is host owned and not a semantic oracle.
new_slide('Đã xây lớp kiểm chứng và bàn giao','06_lop_kiem_chung.png')
text(75,110,'Ràng buộc do hệ thống quản lý + catalog nguồn',27,'B',BLUE,width=1125)
text(75,153,'Đã có lớp kiểm; sơ đồ dưới là luồng tích hợp với tác tử.',21,color=GRAY,width=1125)
boxes=[(75,215,235,94,'Tác tử tạo SQL','Bản nháp thực tế',LIGHT,BLUE),(375,215,235,94,'Lớp kiểm','Query + nguồn',MINT,GREEN),(675,215,235,94,'Tác tử phản biện','Nhận bằng chứng',LAVENDER,PURPLE),(975,215,230,94,'Thực thi lại','Artifact đầu ra',CREAM,ORANGE)]
for x,y,w,h,title,body,c,tc in boxes:
    panel(x,y,w,h,title,c,tc)
    text(x+15,y+50,body,19,width=w-30)
for xa,xb in [(310,375),(610,675),(910,975)]:arrow(xa+8,261,xb-8,261)
statuses=[(380,'Đạt',MINT,GREEN),(563,'Vi phạm',ROSE,RED),(746,'Chưa đủ căn cứ',CREAM,ORANGE)]
for x,title,c,tc in statuses:
    rect(x,348,173,46,c)
    text(x,354,title,19,'B',tc,width=173,align='center')
line(75,433,1205,433,LINE)
for x,n,label in [(75,'29','tests mới'),(470,'87','scoped tests đạt'),(865,'20/20','SQL tái lập bytes')]:
    text(x,461,n,42,'B',BLUE,width=335)
    text(x,521,label,23,width=335)
takeaway('Đã có component tái lập; hiệu quả sửa lỗi còn cần thực nghiệm riêng.')
note('V5: SQL subset; contract phát triển cần thẩm định độc lập. 20/20 tái lập không đồng nghĩa 20/20 đáp án đúng.')

# 07: Separate preparation / reference qualification from any model performance.
new_slide('Nền đánh giá trên database mới','07_chuan_bi_danh_gia.png')
text(75,111,'204 task · 12 database',34,'B',BLUE)
text(75,163,'Nguồn SpecBridge đã pin · chia theo database',21,color=GRAY)
xx=75
for count,c,tc in [(45,BLUE,WHITE),(67,(.59,.79,.72),INK),(92,(.78,.73,.87),INK)]:
    ww=1130*count/204
    rect(xx,225,ww,65,c)
    text(xx,237,str(count),28,'B',tc,width=ww,align='center')
    xx+=ww
for x,title,body in [(75,'Development','45 task · đã mở'),(415,'Validation','67 task · chưa chạy'),(795,'Reserved','92 task · chưa chạy')]:
    text(x,306,title,23,'B',BLUE,width=330)
    text(x,344,body,21,color=GRAY,width=330)
line(75,399,1205,399,LINE)
text(75,425,'90/90',42,'B',GREEN)
text(280,431,'Reference SQL qua qualification',25,'B',width=875)
text(280,476,'Kiểm soát: sai cách hiểu / thêm hàng / thiếu đầu ra đều bị loại.',20,width=875)
takeaway('Khóa cả bộ chấm và engine: 1 task đổi kết quả giữa SQLite 3.42 và 3.51.')
note('Qualification là kiểm tra bộ chấm. 74/90 reference có CTE/nhiều scope, vượt độ phủ đầy đủ hiện tại của checker V5.')

# 08: Newly audited results. No CI or confirmatory claim is invented.
new_slide('Pilot SQL mới nhất: tự kiểm đạt cao hơn','08_ket_qua_sql_moi_nhat.png')
text(75,107,'12 task × 2 cách hiểu chỉ định = 24 trường hợp',27,'B',width=1125)
text(75,151,'3 database development · 144 phản hồi · audit PASS',21,color=GRAY)
plot_left,plot_top,plot_bottom=115,238,498
plot_right=895
for tick in [0,6,12,18,24]:
    yy=plot_bottom-tick/24*(plot_bottom-plot_top)
    line(plot_left,yy,plot_right,yy,LINE,.8)
    text(65,yy-12,str(tick),16,color=GRAY,width=36,align='right')
values=[v6['workflows'][k]['passed'] for k in ['A','B','AA','BB','AB','BA']]
colors=[GRAY,GRAY,BLUE,BLUE,PURPLE,PURPLE]
labels=['A','B','AA','BB','AB','BA']
for i,(value,c,label) in enumerate(zip(values,colors,labels)):
    x=146+i*125
    hh=value/24*(plot_bottom-plot_top)
    rect(x,plot_bottom-hh,64,hh,c)
    text(x-15,plot_bottom-hh-44,f'{value}/24',22,'B',c,width=94,align='center')
    text(x-15,511,label,20,'B',width=94,align='center')
for x,label,c in [(125,'Trực tiếp',GRAY),(375,'Tự kiểm',BLUE),(625,'Kiểm chéo',PURPLE)]:
    text(x,550,label,20,'B',c,width=230,align='center')
text(945,262,'−6,25',45,'B',PURPLE,width=260)
text(945,322,'điểm phần trăm',23,width=260)
text(945,375,'Kiểm chéo − tự kiểm\nTrung bình hai hướng',20,color=GRAY,width=270)
takeaway('Kết quả development; chưa xác nhận trên nguồn giữ lại, chưa thử checker V5.')
note('A=Qwen; B=Gemma. 24 biến thể phụ thuộc theo 12 task. Cùng trần 2 calls chưa đồng nghĩa cùng chi phí thực.')

# 09: Candidate question and a concrete design, no asserted novelty.
new_slide('Câu hỏi nghiên cứu cần xác nhận tiếp','09_huong_nghien_cuu.png')
rect(65,116,1150,101,LIGHT)
text(82,128,'Bàn giao có kiểm chứng có giúp sửa đúng hơn,',29,'B',BLUE,width=1110)
text(82,169,'khi cùng nguồn, công cụ và ngân sách?',29,'B',BLUE,width=1110)
text(80,259,'Đã có nền tảng',27,'B',BLUE)
text(80,311,'• Bộ lỗi có thể truy về nguồn\n• Lớp kiểm + log thực thi tái lập',23,width=470,leading=1.8)
text(658,259,'Cần chứng minh phần lợi ích riêng',27,'B',BLUE,width=540)
text(658,311,'• Tự kiểm / phản hồi trung tính\n• Diagnostic đúng / xáo trộn\n• Cùng checker; xác nhận nguồn mới',23,width=545,leading=1.8)
line(80,480,1200,480,LINE)
text(80,503,'Đo kết quả',23,'B',BLUE)
text(270,503,'Đúng việc · sửa/hại · dừng sai · coverage · tổng chi phí',23,width=930)
takeaway('Contribution mục tiêu: bộ lỗi đã thẩm định + công cụ + bằng chứng có đối chứng.')
note('Contracts/handoff đã có prior gần. Novelty chưa chốt; còn thiếu baseline mạnh, thẩm định độc lập và người dùng.')

# 10: Proposed ownership, not an attribution of historical contributions.
new_slide('Phân công công việc tiếp theo','10_phan_cong_tin_trung.png')
text(75,108,'Phân công đề xuất · ưu tiên theo điều kiện sẵn sàng',23,color=GRAY)
rect(75,166,535,49,NAVY)
rect(670,166,535,49,BLUE)
text(95,169,'Tín',30,'B',WHITE)
text(690,169,'Trung',30,'B',WHITE)
for x,rows in [(85,[('01','Đo / mở rộng SQL coverage'),('02','Baseline mạnh + cùng tools/checker'),('03','Harness và log tokens / thời gian')]),(680,[('01','Source-only review + rubric'),('02','Đối chiếu contribution với prior'),('03','Tìm workflow và người dùng pilot')])]:
    for j,(n,label) in enumerate(rows):
        yy=244+j*68
        text(x,yy,n,22,'B',BLUE)
        text(x+48,yy,label,23,width=460)
text(85,468,'Đầu ra: coverage + bảng baseline tái lập',20,'B',BLUE,width=520)
text(680,468,'Đầu ra: phiếu review + workflow pilot',20,'B',BLUE,width=520)
line(75,527,1205,527,LINE)
text(75,548,'Cùng thực hiện',22,'B',BLUE)
text(300,548,'Review chéo → khóa protocol → thử cơ chế → nguồn giữ lại',23,width=895)
takeaway('Đợt tới cần bộ đánh giá rõ nghĩa và đối chứng đủ mạnh trước khi mở rộng.')
note('Chưa có người dùng tham gia. Thời điểm mở tập giữ lại phụ thuộc việc khóa cơ chế và hoàn tất kiểm tra sẵn sàng.')

# Export only images; retain geometry/text checks for reproducibility.
outputs=[]
for i,page in enumerate(doc):
    destination=SLIDES/names[i]
    pix=page.get_pixmap(matrix=fitz.Matrix(2,2),alpha=False)
    assert (pix.width,pix.height)==(2560,1440)
    pix.save(destination)
    outputs.append({'file':destination.relative_to(OUT).as_posix(),'width':pix.width,'height':pix.height,'sha256':sha(destination)})

# Contact sheet, 2 columns x 5 rows, with a separate PNG for convenient preview.
sheet=fitz.Pixmap(fitz.csRGB,fitz.IRect(0,0,1600,2250),False)
sheet.clear_with(255)
for i,page in enumerate(doc):
    thumb=page.get_pixmap(matrix=fitz.Matrix(.625,.625),alpha=False)
    thumb.set_origin((i%2)*800,(i//2)*450)
    sheet.copy(thumb,thumb.irect)
sheet.save(OUT/'TONG_QUAN_10_SLIDE.png')

source_paths=[
 'docs/reports/2026-10-27/PRESENTATION_HANDOFF.md',
 'docs/reports/2026-11-09/VERIFICATION_CYCLE01_RESULTS_VA_QUYET_DINH.md',
 'docs/reports/2026-11-09/ARQA_CYCLE02_RESULTS_VA_QUYET_DINH.md',
 'docs/reports/2026-11-09/WORKSPACE_V4_RESULTS_VA_PATH_TIEP.md',
 'docs/reports/2026-11-09/RELATIONAL_V5_RESULTS_VA_QUYET_DINH.md',
 'docs/reports/2026-11-09/RESEARCH_STRATEGY_V5_VA_CONTRIBUTIONS.md',
 'results/specbridge_v6/offline_results.json',
 'results/specbridge_v6/registered_plan.json',
 'results/specbridge_v6/qualification_readout.json',
 'docs/reports/2026-11-10/BAO_CAO_TIEN_DO_GUI_GVHD.md',
 'docs/reports/2026-11-10/LOI_TRINH_BAY_10_SLIDE.md',
 'docs/reports/2026-11-10/specbridge_v6_offline_results.json',
]
receipt={
 'created_utc':datetime.now(timezone.utc).isoformat(),
 'output_format':'10 standalone PNG images; no title slide; no PPTX/PDF export',
 'size':[2560,1440], 'aspect_ratio':'16:9',
 'design_reference':{'path':str(REFERENCE),'sha256':sha(REFERENCE),'pages_inspected':23,
     'use':'Layout, Latin Modern Sans, palette and decorative background only; unrelated logos covered and no research content copied'},
 'fonts':{k:{'path':str(p),'sha256':sha(p)} for k,p in FONTS.items()},
 'sources':{p:sha(ROOT/p) for p in source_paths},
 'outputs':outputs,
 'automated_checks':{'canvas_bounds':'PASS','unbreakable_text_overflow':'PASS','slide_count':len(doc),'incremental_model_response_sum':1265,
     'font_glyph_coverage':'PASS','native_v6_values_match_offline_results':True,'raw_experiment_files_modified':False},
 'text_layout':text_log,
}
(OUT/'generation_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2))
report_source=ROOT/'docs/reports/2026-11-10/BAO_CAO_TIEN_DO_GUI_GVHD.md'
def rebase_link(match):
    target=match.group(1)
    if target.startswith(('http:','https:','#')):return match.group(0)
    return ']('+Path(os.path.relpath((report_source.parent/target).resolve(),OUT)).as_posix()+')'
(OUT/'BAO_CAO_TIEN_DO.md').write_text(re.sub(r'\]\(([^)]+)\)',rebase_link,report_source.read_text()))
shutil.copyfile(ROOT/'docs/reports/2026-11-10/LOI_TRINH_BAY_10_SLIDE.md',OUT/'LOI_TRINH_BAY_10_SLIDE.md')
with zipfile.ZipFile(OUT/'RepGuard_10_SLIDE_PNG_16x9.zip','w',compression=zipfile.ZIP_DEFLATED) as z:
    for name in names:z.write(SLIDES/name,name)
print(json.dumps({'slides':len(doc),'dimensions':[2560,1440],'output':str(OUT),'text_rows':len(text_log)},ensure_ascii=False))
