"""
Genera 2 slides en 1 PPTX — trazabilidad individual + media grupal:
  Slide 1 (Bloque III): Evolución Nota Promedio Alumnos — Aptos P3 vs Control B3
  Slide 2 (Bloque IV):  Evolución EDD             — Aptos P3 vs Control B4
Salida: outputs/pptx/DIAPO_evolucion_trazabilidad.pptx
"""
import sys; sys.stdout.reconfigure(encoding="utf-8")
import os, zipfile
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import matplotlib.lines as mlines
import pandas as pd
from PIL import Image as PILImage
from pptx import Presentation
from pptx.util import Emu, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
import pathlib

# ── Rutas ─────────────────────────────────────────────────────────────────────
BASE    = os.path.dirname(os.path.abspath(__file__))
REPO    = str(pathlib.Path(BASE).parents[1])
CASCADE = os.path.join(REPO, "data", "cascade")
COMP    = os.path.join(CASCADE, "complementarios")

APTOS_CSV  = os.path.join(CASCADE, "05_aptos_p3",  "p3_sat_zscore.csv")
SCAT_CSV   = os.path.join(COMP,                    "scatter_sat_notas.csv")
EDD_CSV    = os.path.join(COMP,                    "evaluacion_jefes.csv")
P918_CSV   = os.path.join(CASCADE, "04_formados_p3","p3_918.csv")
D918_CSV   = os.path.join(CASCADE, "03_jerarquizados","docente_918.csv")
FONDOTIPO  = (r"c:\Users\r.gonzalez_fluxsolar.LAPTOP-FLUX-ECO"
              r"\Downloads\Analisis_UCEN_v2\Fondotipop.pptx")
OUT_PPTX   = os.path.join(REPO, "outputs", "pptx", "DIAPO_evolucion_trazabilidad.pptx")
OUT_DIR    = os.path.join(BASE, "dark_slides_v3")
SCRATCH    = os.path.join(REPO, "outputs", "scratch")
os.makedirs(OUT_DIR, exist_ok=True); os.makedirs(SCRATCH, exist_ok=True)

# ── Assets ─────────────────────────────────────────────────────────────────────
BG_PATH   = os.path.join(SCRATCH, "fondotipo_image1.jpg")
LOGO_PATH = os.path.join(SCRATCH, "fondotipo_image2.png")
for path, zname in [(BG_PATH,"ppt/media/image1.jpg"),(LOGO_PATH,"ppt/media/image2.png")]:
    if not os.path.exists(path):
        with zipfile.ZipFile(FONDOTIPO) as z:
            with open(path,"wb") as f: f.write(z.read(zname))

with PILImage.open(BG_PATH) as _im:
    _rgb = _im.convert("RGB"); _iw,_ih = _rgb.size
    _nh  = int(_iw/(16/9)); _y0 = min(int(_ih*0.12),_ih-_nh)
    bg_arr = np.array(_rgb.crop((0,_y0,_iw,_y0+_nh)))
with PILImage.open(LOGO_PATH) as _logo:
    logo_arr = np.array(_logo.convert("RGBA")).astype(np.float32)/255.0

H_GRAD = 600; grad = np.zeros((H_GRAD,1,4),dtype=np.float32)
for _r in range(H_GRAD):
    _t = _r/(H_GRAD-1)
    _stops = [(0.00,(0,33,71)),(0.54,(0,70,128)),(1.00,(144,171,196))]
    for _i in range(len(_stops)-1):
        _t0,_c0=_stops[_i]; _t1,_c1=_stops[_i+1]
        if _t0<=_t<=_t1:
            _s=(_t-_t0)/(_t1-_t0)
            grad[_r,0]=[(_c0[0]+_s*(_c1[0]-_c0[0]))/255,
                         (_c0[1]+_s*(_c1[1]-_c0[1]))/255,
                         (_c0[2]+_s*(_c1[2]-_c0[2]))/255,0.82]; break

# ── Layout ─────────────────────────────────────────────────────────────────────
SW,SH     = 13.333,7.5
SW_EMU    = 12192000; SH_EMU = 6858000
PIC_L,PIC_T,PIC_W,PIC_H = 786581,1125000,10599174,3720000
BUL_L,BUL_T,BUL_W,BUL_H = 786581,4870000,10599174,1870000
LOGO_L,LOGO_T,LOGO_W,LOGO_H = 9813773,656354,1756626,697725
TITLE_L,TITLE_T,TITLE_W,TITLE_H = PIC_L,185000,PIC_W,710000
POP_L,POP_T,POP_W,POP_H = PIC_L,845000,9000000,255000

def _ex(e): return e/SW_EMU
def _ey(e): return e/SH_EMU
def _fig_rect(l,t,w,h): return (l,1-t-h,w,h)

PIC_RECT  = _fig_rect(_ex(PIC_L),_ey(PIC_T),_ex(PIC_W),_ey(PIC_H))
LOGO_RECT = _fig_rect(_ex(LOGO_L),_ey(LOGO_T),_ex(LOGO_W),_ey(LOGO_H))

CHART_X = PIC_RECT[0]+0.08; CHART_Y = PIC_RECT[1]+0.04
CHART_W = PIC_RECT[2]-0.12; CHART_H = PIC_RECT[3]-0.09
CTITLE_L = int(CHART_X*SW_EMU); CTITLE_T = PIC_T+38000
CTITLE_W = int((PIC_RECT[0]+PIC_RECT[2]-CHART_X+0.02)*SW_EMU); CTITLE_H = 295000
SHARED_BG = os.path.join(OUT_DIR,"_background.png")

COL_AP = "#5C9BD6"; COL_CT = "#FFB74D"

# ── Helpers matplotlib ─────────────────────────────────────────────────────────
def _bg_fig():
    fig = plt.figure(figsize=(SW,SH),facecolor="#101820")
    fig.patch.set_facecolor("#101820")
    for z,arr in [(0,bg_arr),(1,grad)]:
        ax=fig.add_axes([0,0,1,1],zorder=z)
        ax.imshow(arr,extent=[0,1,0,1],aspect="auto",origin="upper")
        ax.set_xlim(0,1); ax.set_ylim(0,1); ax.axis("off")
    al=fig.add_axes([LOGO_RECT[0],LOGO_RECT[1],LOGO_RECT[2],LOGO_RECT[3]],zorder=10,facecolor="none")
    al.imshow(logo_arr,aspect="auto"); al.axis("off"); al.patch.set_visible(False)
    return fig

def _tr_fig():
    fig=plt.figure(figsize=(SW,SH),facecolor="none"); fig.patch.set_facecolor("none"); return fig

def _save_bg(fig,name):
    path=os.path.join(OUT_DIR,name); fig.savefig(path,dpi=150,facecolor=fig.get_facecolor()); plt.close(fig); return path

def _save_ch(fig,name):
    path=os.path.join(OUT_DIR,name); fig.savefig(path,dpi=150,facecolor="none",transparent=True); plt.close(fig); return path

def _style(ax,ylabel=None):
    ax.tick_params(axis="x",colors="white",labelsize=9,length=0,rotation=15)
    ax.tick_params(axis="y",colors="#AAAAAA",labelsize=9,length=0)
    for sp in ax.spines.values(): sp.set_edgecolor("white"); sp.set_alpha(0.30); sp.set_linewidth(0.8)
    ax.yaxis.grid(True,color="white",alpha=0.07,linewidth=0.5); ax.set_axisbelow(True)
    if ylabel: ax.set_ylabel(ylabel,color="#AAAAAA",fontsize=9)

def _ensure_bg():
    if not os.path.exists(SHARED_BG):
        fig=_bg_fig(); _save_bg(fig,"_background.png"); print("  bg generado")

# ── Helpers pptx ───────────────────────────────────────────────────────────────
def _new_sl(prs): return prs.slides.add_slide(prs.slide_layouts[6])
def _pic(sl,path,prs): sl.shapes.add_picture(path,Emu(0),Emu(0),prs.slide_width,prs.slide_height)

def _txt(sl,text,left,top,width,height,fs=12,bold=False,italic=False,color="#FFFFFF",
         align=PP_ALIGN.LEFT,wrap=True,lspc=0,font_name=None):
    txb=sl.shapes.add_textbox(Emu(left),Emu(top),Emu(width),Emu(height))
    tf=txb.text_frame; tf.word_wrap=wrap
    for i,line in enumerate(str(text).split("\n")):
        p=tf.paragraphs[0] if i==0 else tf.add_paragraph()
        p.alignment=align
        if lspc>0 and i>0: p.space_before=Pt(lspc)
        run=p.add_run(); run.text=line
        run.font.size=Pt(fs); run.font.bold=bold; run.font.italic=italic
        if font_name: run.font.name=font_name
        r,g,b=int(color[1:3],16),int(color[3:5],16),int(color[5:7],16)
        run.font.color.rgb=RGBColor(r,g,b)

def _T(sl,text,fs=18): _txt(sl,text,TITLE_L,TITLE_T,TITLE_W,TITLE_H,fs=fs,bold=True,color="#FFFFFF",align=PP_ALIGN.CENTER)
def _CT(sl,text): _txt(sl,text,CTITLE_L,CTITLE_T,CTITLE_W,CTITLE_H,fs=9,color="#FFFFFF",font_name="Calibri")
def _POP(sl,text): _txt(sl,text,POP_L,POP_T,POP_W,POP_H,fs=7.5,italic=True,color="#C8DCF0")

def _BUL(sl,items,fs=11.5):
    txb=sl.shapes.add_textbox(Emu(BUL_L),Emu(BUL_T),Emu(BUL_W),Emu(BUL_H))
    tf=txb.text_frame; tf.word_wrap=True
    for i,item in enumerate(items):
        p=tf.paragraphs[0] if i==0 else tf.add_paragraph()
        p.space_after=Pt(5); p.alignment=PP_ALIGN.LEFT
        run=p.add_run(); run.text=f"{i+1}.  {item}"
        run.font.size=Pt(fs); run.font.color.rgb=RGBColor(0xFF,0xFF,0xFF)

# ── Función spaghetti + media ──────────────────────────────────────────────────
def _spaghetti(ax, pivot_ap, pivot_ct, xs, ylabel, ylim=None):
    """Líneas individuales + media grupal para dos grupos sobre eje x dado."""
    x_idx = list(range(len(xs)))

    # Spaghetti Aptos P3
    for _, row in pivot_ap.iterrows():
        vals = row.values.astype(float)
        mask = ~np.isnan(vals)
        if mask.sum() >= 2:
            xi = [x_idx[j] for j in range(len(xs)) if mask[j]]
            yi = vals[mask]
            ax.plot(xi, yi, color=COL_AP, alpha=0.09, lw=0.9, zorder=2)

    # Spaghetti Control
    for _, row in pivot_ct.iterrows():
        vals = row.values.astype(float)
        mask = ~np.isnan(vals)
        if mask.sum() >= 2:
            xi = [x_idx[j] for j in range(len(xs)) if mask[j]]
            yi = vals[mask]
            ax.plot(xi, yi, color=COL_CT, alpha=0.09, lw=0.9, zorder=2)

    # Media Aptos P3
    mean_ap = pivot_ap.mean(skipna=True).values
    ax.plot(x_idx, mean_ap, color=COL_AP, lw=2.8, marker="o", markersize=8,
            label=f"Aptos P3  (nº {len(pivot_ap)})", zorder=5)
    for xi, yi in zip(x_idx, mean_ap):
        if not np.isnan(yi):
            ax.text(xi, yi+0.04, f"{yi:.2f}", ha="center", va="bottom",
                    fontsize=8, fontweight="bold", color=COL_AP,
                    path_effects=[pe.withStroke(linewidth=1.5,foreground="#0A0F18")], zorder=6)

    # Media Control
    mean_ct = pivot_ct.mean(skipna=True).values
    ax.plot(x_idx, mean_ct, color=COL_CT, lw=2.8, marker="s", markersize=8,
            linestyle="--", label=f"Control  (nº {len(pivot_ct)})", zorder=5)
    for xi, yi in zip(x_idx, mean_ct):
        if not np.isnan(yi):
            ax.text(xi, yi-0.04, f"{yi:.2f}", ha="center", va="top",
                    fontsize=8, fontweight="bold", color=COL_CT,
                    path_effects=[pe.withStroke(linewidth=1.5,foreground="#0A0F18")], zorder=6)

    ax.set_xticks(x_idx); ax.set_xticklabels(xs)
    if ylim: ax.set_ylim(ylim)
    _style(ax, ylabel=ylabel)
    leg = ax.legend(fontsize=9, framealpha=0.25, labelcolor="white",
                    facecolor="#101820", edgecolor="#555", loc="upper left")

# ── Carga de datos comunes ─────────────────────────────────────────────────────
aptos  = pd.read_csv(APTOS_CSV,  encoding="utf-8-sig")
ruts_aptos     = set(aptos["rut_key"].astype(str).str.strip())
N_APTOS = len(ruts_aptos)

p918   = pd.read_csv(P918_CSV,   encoding="utf-8-sig")
ruts_todos_form = set(p918["rut_key"].astype(str).str.strip())

d918   = pd.read_csv(D918_CSV,   encoding="utf-8-sig")
ruts_917 = set(d918["rut_key"].astype(str).str.strip())

print(f"Aptos P3: {N_APTOS}  |  Todos formados: {len(ruts_todos_form)}  |  Universo 918: {len(ruts_917)}")

# ── SLIDE 1 — Nota Promedio Alumnos ───────────────────────────────────────────
scat = pd.read_csv(SCAT_CSV, encoding="utf-8-sig")
scat["rut_key"]        = scat["rut_docente"].astype(str).str.strip()
scat["nota_promedio"]  = pd.to_numeric(scat["nota_promedio"],  errors="coerce")
scat["formado"]        = scat["formado"].astype(str).str.strip().str.upper().isin(["TRUE","1","SI","SÍ","YES"])

# Agregar por docente-periodo (media de secciones)
agg = scat.groupby(["rut_key","periodo"])["nota_promedio"].mean().reset_index()
periodos_ord = sorted(agg["periodo"].unique().tolist())

agg_ap = agg[agg["rut_key"].isin(ruts_aptos)]
agg_ct = agg[~agg["rut_key"].isin(ruts_todos_form) & ~agg["rut_key"].isin(ruts_aptos)]
# control = no formados (formado=False en scatter)
ruts_ctrl_b3 = set(scat[~scat["formado"]]["rut_key"].unique())
agg_ct = agg[agg["rut_key"].isin(ruts_ctrl_b3)]

pivot_ap_nota = agg_ap.pivot_table(index="rut_key", columns="periodo", values="nota_promedio")
pivot_ct_nota = agg_ct.pivot_table(index="rut_key", columns="periodo", values="nota_promedio")
# Alinear columnas
for p in periodos_ord:
    if p not in pivot_ap_nota.columns: pivot_ap_nota[p] = np.nan
    if p not in pivot_ct_nota.columns: pivot_ct_nota[p] = np.nan
pivot_ap_nota = pivot_ap_nota[periodos_ord]
pivot_ct_nota = pivot_ct_nota[periodos_ord]

N_AP_NOTA = len(pivot_ap_nota); N_CT_NOTA = len(pivot_ct_nota)
print(f"Nota — Aptos P3 con dato: {N_AP_NOTA}  |  Control: {N_CT_NOTA}")

_ensure_bg()
fig1 = _tr_fig()
ax1  = fig1.add_axes([CHART_X, CHART_Y, CHART_W, CHART_H], facecolor="none", zorder=5)
_spaghetti(ax1, pivot_ap_nota, pivot_ct_nota, periodos_ord,
           ylabel="Nota promedio alumnos (1–7)", ylim=(1.0, 7.5))
ax1.set_title("Evolución Nota Promedio Alumnos por Período",
              color="white", fontsize=12, pad=10, fontfamily="Calibri")

# ── SLIDE 2 — EDD ─────────────────────────────────────────────────────────────
edd = pd.read_csv(EDD_CSV, encoding="utf-8-sig")
edd["rut_key"]  = edd["rut_key"].astype(str).str.strip()
edd["edd_total"] = pd.to_numeric(edd["edd_total"], errors="coerce")
edd = edd.dropna(subset=["edd_total","anio_evaluacion"])
edd["anio"] = edd["anio_evaluacion"].astype(int).astype(str)
anios_ord = sorted(edd["anio"].unique().tolist())

edd_ap = edd[edd["rut_key"].isin(ruts_aptos)]
edd_ct = edd[edd["rut_key"].isin(ruts_917) & ~edd["rut_key"].isin(ruts_todos_form)]

pivot_ap_edd = edd_ap.pivot_table(index="rut_key", columns="anio", values="edd_total", aggfunc="mean")
pivot_ct_edd = edd_ct.pivot_table(index="rut_key", columns="anio", values="edd_total", aggfunc="mean")
for a in anios_ord:
    if a not in pivot_ap_edd.columns: pivot_ap_edd[a] = np.nan
    if a not in pivot_ct_edd.columns: pivot_ct_edd[a] = np.nan
pivot_ap_edd = pivot_ap_edd[anios_ord]
pivot_ct_edd = pivot_ct_edd[anios_ord]

N_AP_EDD = len(pivot_ap_edd); N_CT_EDD = len(pivot_ct_edd)
print(f"EDD  — Aptos P3 con dato: {N_AP_EDD}  |  Control: {N_CT_EDD}")

fig2 = _tr_fig()
ax2  = fig2.add_axes([CHART_X, CHART_Y, CHART_W, CHART_H], facecolor="none", zorder=5)
_spaghetti(ax2, pivot_ap_edd, pivot_ct_edd, anios_ord,
           ylabel="EDD Total (0–1)", ylim=(0.0, 1.10))
ax2.set_title("Evolución EDD por Año de Evaluación",
              color="white", fontsize=12, pad=10, fontfamily="Calibri")

# ── Armar PPTX ─────────────────────────────────────────────────────────────────
prs = Presentation()
prs.slide_width  = Emu(SW_EMU)
prs.slide_height = Emu(SH_EMU)

# Slide 1
sl1 = _new_sl(prs)
_pic(sl1, SHARED_BG, prs)
_pic(sl1, _save_ch(fig1,"traz_nota.png"), prs)
_T(sl1, "Bloque III — Evolución Nota Promedio Alumnos — Aptos P3 vs Control")
_POP(sl1, f"Aptos P3: nº {N_AP_NOTA} con dato de nota  ·  Control B3: nº {N_CT_NOTA}  ·  "
          f"Líneas individuales por docente + media grupal  ·  2023–2025")
_CT(sl1, f"Nota promedio de alumnos por semestre  ·  Aptos P3 (azul, nº {N_AP_NOTA})  ·  "
         f"Control sin formacion (naranja, nº {N_CT_NOTA})  ·  media calculada sobre secciones agregadas por docente")
_BUL(sl1, [
    f"Los Aptos P3 (linea azul) mantienen una nota promedio de alumnos consistentemente "
    f"superior a la del grupo control a lo largo de los {len(periodos_ord)} semestres.",
    "La dispersion individual (lineas finas) muestra alta variabilidad dentro de cada grupo, "
    "pero la media grupal permite comparar la tendencia central entre tratamiento y control.",
    "Una brecha positiva sostenida sugiere que los cursos de los Aptos P3 generan "
    "mejores resultados academicos para sus estudiantes en el tiempo.",
])

# Slide 2
sl2 = _new_sl(prs)
_pic(sl2, SHARED_BG, prs)
_pic(sl2, _save_ch(fig2,"traz_edd.png"), prs)
_T(sl2, "Bloque IV — Evolución EDD — Aptos P3 vs Control")
_POP(sl2, f"Aptos P3 con EDD: nº {N_AP_EDD}  ·  Control B4 (sin formacion, con EDD): nº {N_CT_EDD}  ·  "
          f"Líneas individuales por docente + media grupal")
_CT(sl2, f"EDD Total (escala 0–1) por anio evaluacion  ·  Aptos P3 (azul, nº {N_AP_EDD})  ·  "
         f"Control B4 sin formacion (naranja, nº {N_CT_EDD})")
_BUL(sl2, [
    f"La evolucion del EDD muestra la trayectoria de evaluacion directiva de los "
    f"{N_AP_EDD} Aptos P3 con registro EDD frente a los {N_CT_EDD} del grupo control.",
    "Las lineas individuales permiten identificar docentes con trayectorias atipicas "
    "(ascendentes o descendentes marcadas) dentro de cada grupo.",
    "La comparacion de medias grupales por anio revela si la formacion P3 se asocia "
    "con una mejora sostenida en la evaluacion de desempeno directivo.",
])

prs.save(OUT_PPTX)
print(f"\n✓ Guardado: {OUT_PPTX}")
