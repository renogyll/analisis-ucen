"""
generar_grupo_selecto.py  — v2
4 slides: análisis del grupo de alta intensidad formativa (50 docentes).

  Slide 1 — Perfil: barras apiladas T/D/P por docente (sin funnel)
  Slide 2 — B2 SAT:   trayectoria individual 2023→2024→2025 + media vs control
  Slide 3 — B3 Notas: trayectoria individual 2023→2024→2025 + media vs control
  Slide 4 — B4 EDD:   trayectoria individual 2022→2023→2024→2025 + media vs control
"""
import sys; sys.stdout.reconfigure(encoding="utf-8")
import os, zipfile
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.patches import Patch
from PIL import Image as PILImage
from pptx import Presentation
from pptx.util import Emu, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from config import CASCADE

# ── Paths ──────────────────────────────────────────────────────────────────────
REPO     = Path(__file__).resolve().parents[4]
SCRATCH  = REPO / "outputs" / "scratch"
OUT_DIR  = REPO / "outputs" / "scratch" / "selecto_slides"
OUT_PPTX = REPO / "outputs" / "pptx" / "GRUPO_SELECTO_v7.pptx"
FONDOTIPO = os.path.join(REPO, "assets", "Fondotipop.pptx")
COMP = Path(CASCADE) / "complementarios"
for d in [SCRATCH, OUT_DIR, OUT_PPTX.parent]:
    os.makedirs(d, exist_ok=True)

# ── Assets ─────────────────────────────────────────────────────────────────────
BG_PATH   = SCRATCH / "fondotipo_image1.jpg"
LOGO_PATH = SCRATCH / "fondotipo_image2.png"
for path, zname in [(BG_PATH,"ppt/media/image1.jpg"),(LOGO_PATH,"ppt/media/image2.png")]:
    if not os.path.exists(path):
        with zipfile.ZipFile(FONDOTIPO) as z:
            with open(path,"wb") as f: f.write(z.read(zname))

with PILImage.open(BG_PATH) as _im:
    _rgb = _im.convert("RGB"); _iw,_ih = _rgb.size
    _nh = int(_iw/(16/9)); _y0 = min(int(_ih*0.12),_ih-_nh)
    bg_arr = np.array(_rgb.crop((0,_y0,_iw,_y0+_nh)))

with PILImage.open(LOGO_PATH) as _logo:
    logo_arr = np.array(_logo.convert("RGBA")).astype(np.float32)/255.0

H_GRAD=600; grad=np.zeros((H_GRAD,1,4),dtype=np.float32)
for _r in range(H_GRAD):
    _t=_r/(H_GRAD-1)
    _st=[(0.00,(0,33,71)),(0.54,(0,70,128)),(1.00,(144,171,196))]
    for _i in range(len(_st)-1):
        _t0,_c0=_st[_i]; _t1,_c1=_st[_i+1]
        if _t0<=_t<=_t1:
            _s=(_t-_t0)/(_t1-_t0)
            grad[_r,0]=[(_c0[0]+_s*(_c1[0]-_c0[0]))/255,
                        (_c0[1]+_s*(_c1[1]-_c0[1]))/255,
                        (_c0[2]+_s*(_c1[2]-_c0[2]))/255,0.82]; break

# ── Layout ─────────────────────────────────────────────────────────────────────
SW,SH=13.333,7.5; SW_EMU=12192000; SH_EMU=6858000
PIC_L,PIC_T,PIC_W,PIC_H=786581,1125000,10599174,3720000
TITLE_L,TITLE_T,TITLE_W,TITLE_H=PIC_L,185000,PIC_W,710000
POP_L,POP_T,POP_W,POP_H=PIC_L,845000,9000000,255000
LOGO_L,LOGO_T,LOGO_W,LOGO_H=9813773,656354,1756626,697725
CTITLE_T=PIC_T+38000; CTITLE_W=PIC_W-400000; CTITLE_H=280000

def _ex(e): return e/SW_EMU
def _ey(e): return e/SH_EMU
def _fig_rect(l,t,w,h): return (l,1-t-h,w,h)

PIC_RECT  = _fig_rect(_ex(PIC_L),_ey(PIC_T),_ex(PIC_W),_ey(PIC_H))
LOGO_RECT = _fig_rect(_ex(LOGO_L),_ey(LOGO_T),_ex(LOGO_W),_ey(LOGO_H))

COL_SEL="#52C97A"; COL_CTRL="#FFB74D"; DARK_BG="#0A0F18"
COL_T="#5C9BD6"; COL_D="#A5D6A7"; COL_P="#FFB74D"

# Colores por etapa (PRE / DURANTE / POST)
COL_PRE  = "#E8C547"   # dorado — baseline (claramente distinto de DURANTE)
COL_DUR  = "#5C9BD6"   # azul — durante formación
COL_POST = "#52C97A"   # verde — resultado post
STAGE_COLS = {"PRE": COL_PRE, "DURANTE": COL_DUR, "POST": COL_POST}

COL_LINE_TALLER = "white"    # línea conectora talleres
COL_LINE_DIPLO  = "#FFB74D"  # línea conectora diplomados (naranja distinguible)

STAGES   = ["PRE", "DURANTE", "POST"]
X_STAGES = np.arange(3)

# ── matplotlib ─────────────────────────────────────────────────────────────────
SHARED_BG = str(OUT_DIR/"_background.png")

def _bg_fig():
    fig=plt.figure(figsize=(SW,SH),facecolor="#101820")
    for z,arr in [(0,bg_arr),(1,grad)]:
        ax=fig.add_axes([0,0,1,1],zorder=z)
        ax.imshow(arr,extent=[0,1,0,1],aspect="auto",origin="upper"); ax.axis("off")
    al=fig.add_axes([LOGO_RECT[0],LOGO_RECT[1],LOGO_RECT[2],LOGO_RECT[3]],zorder=10,facecolor="none")
    al.imshow(logo_arr,aspect="auto"); al.axis("off"); al.patch.set_visible(False)
    return fig

def _tr_fig():
    fig=plt.figure(figsize=(SW,SH),facecolor="none"); fig.patch.set_facecolor("none"); return fig

def _ensure_bg():
    if not os.path.exists(SHARED_BG):
        fig=_bg_fig(); plt.savefig(SHARED_BG,dpi=150,facecolor=fig.get_facecolor()); plt.close()

def _save(fig,name):
    path=str(OUT_DIR/name)
    plt.savefig(path,dpi=150,facecolor="none",transparent=True); plt.close(); return path

def _ax_style(ax):
    ax.tick_params(axis="x",colors="white",labelsize=9.5,length=0)
    ax.tick_params(axis="y",colors="#AAAAAA",labelsize=9,length=0)
    for sp in ax.spines.values(): sp.set_edgecolor("white"); sp.set_alpha(0.25); sp.set_linewidth(0.7)
    ax.yaxis.grid(True,color="white",alpha=0.07,linewidth=0.5)
    ax.set_axisbelow(True); ax.set_facecolor("none")

# ── pptx ───────────────────────────────────────────────────────────────────────
def _new_sl(prs): return prs.slides.add_slide(prs.slide_layouts[6])
def _pic(sl,path,prs): sl.shapes.add_picture(path,Emu(0),Emu(0),prs.slide_width,prs.slide_height)
def _txt(sl,text,left,top,width,height,fs=12,bold=False,italic=False,
         color="#FFFFFF",align=PP_ALIGN.LEFT,wrap=True,lspc=0,font_name=None):
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
def _T(sl,text,fs=18): _txt(sl,text,TITLE_L,TITLE_T,TITLE_W,TITLE_H,fs=fs,bold=True,align=PP_ALIGN.CENTER)
def _POP(sl,text): _txt(sl,text,POP_L,POP_T,POP_W,POP_H,fs=7.5,italic=True,color="#C8DCF0")
def _CT(sl,text): _txt(sl,text,PIC_L+400000,CTITLE_T,CTITLE_W,CTITLE_H,fs=9,color="#FFFFFF",font_name="Calibri")

# ── Datos ───────────────────────────────────────────────────────────────────────
print("Cargando datos…")
p3ev = pd.read_csv(Path(CASCADE)/"04_formados_p3"/"p3_918.csv", encoding="utf-8-sig")
p3ev["rut_key"] = p3ev["rut_key"].astype(str).str.strip()
p3ev["apto_p3"] = p3ev["apto_p3"].astype(str).str.upper().isin(["TRUE","1"])

scatter = pd.read_csv(COMP/"scatter_sat_notas.csv", encoding="utf-8-sig")
scatter["rut_docente"] = scatter["rut_docente"].astype(str).str.strip()
scatter["formado"] = scatter["formado"].astype(str).str.upper().isin(["TRUE","1","SI","SÍ","YES"])
scatter["year"] = scatter["periodo"].str[:4].astype(int)

edd = pd.read_csv(COMP/"evaluacion_jefes.csv", encoding="utf-8-sig")
edd["rut_key"] = edd["rut_key"].astype(str).str.strip()
edd["edd_pct"] = pd.to_numeric(edd["edd_total"],errors="coerce")*100
edd["edd_num"] = pd.to_numeric(edd["edd_total"],errors="coerce")
edd["year"] = pd.to_numeric(edd["anio_evaluacion"],errors="coerce").astype("Int64")

# B2 control: control_918.csv (docentes con SAT pero sin formación P3)
ctrl_b2 = pd.read_csv(COMP/"control_918.csv", encoding="utf-8-sig")
ctrl_b2["rut_key"] = ctrl_b2["rut_key"].astype(str).str.strip()

# B4 control: universo_base sin formación P3, con EDD válida
base_df = pd.read_csv(Path(CASCADE)/"00_base"/"nomina_x_dotacion.csv",
                      encoding="utf-8-sig")
base_df["rut_key"] = base_df["rut_key"].astype(str).str.strip()
ruts_universo_base = set(base_df["rut_key"])

# ── Grupo Selecto ───────────────────────────────────────────────────────────────
inst = p3ev.groupby("rut_key").agg(
    n_inst   =("tipo_formacion","count"),
    apto_p3  =("apto_p3","max"),
    nombre   =("nombre","first"),
    jerarquia=("jerarquia","first"),
    facultad =("unidad_facultad","first"),
).reset_index()

# Conteo por tipo de formación por docente
tipo_cnt = (p3ev.groupby(["rut_key","tipo_formacion"]).size()
              .unstack(fill_value=0)
              .reindex(columns=["TALLER","DIPLOMADO","PROYECTO"],fill_value=0))

selecto_df = (inst[(inst["n_inst"]>=3) & inst["apto_p3"]]
              .join(tipo_cnt, on="rut_key")
              .sort_values("n_inst", ascending=False)
              .reset_index(drop=True))
selecto_ruts  = set(selecto_df["rut_key"])
all_form_ruts = set(p3ev["rut_key"])

# Año inicio/fin real de formación por docente del grupo selecto
yr_range = (p3ev[p3ev["rut_key"].isin(selecto_ruts)]
            .groupby("rut_key")["anio_evento"]
            .agg(yr_min="min", yr_max="max")
            .reset_index())
yr_range["yr_min"] = yr_range["yr_min"].astype(int)
yr_range["yr_max"] = yr_range["yr_max"].astype(int)

# Límites a nivel de PERÍODO para staging semestral (evita colisión año==periodo cuando
# taller 2025-S1 tiene POST en 2025-S2 = mismo año calendario)
def _norm_bl(p):
    p = str(p).strip()
    return p + "-02" if len(p) == 4 else p   # "2023" → "2023-02"

def _norm_res(p):
    p = str(p).strip()
    return p + "-01" if len(p) == 4 else p   # "2025" → "2025-01"

_p3_sel = p3ev[p3ev["rut_key"].isin(selecto_ruts) & p3ev["apto_p3"]].copy()
_p3_sel["bl_per"]  = _p3_sel["periodo_baseline"].apply(_norm_bl)
_p3_sel["res_per"] = _p3_sel["periodo_resultado"].apply(_norm_res)
per_range = (_p3_sel.groupby("rut_key")
             .agg(min_baseline=("bl_per","min"), max_resultado=("res_per","max"))
             .reset_index())

# Controles correctos por bloque
ctrl_ruts_b2  = set(ctrl_b2["rut_key"].unique())          # B2: 569 con SAT
ctrl_ruts_b3  = set(scatter[~scatter["formado"]]["rut_docente"].unique())  # B3: 539 scatter
ctrl_ruts_b4  = set(                                       # B4: universo_base sin P3 con EDD
    edd[edd["rut_key"].isin(ruts_universo_base) &
        ~edd["rut_key"].isin(all_form_ruts) &
        edd["edd_num"].notna()]["rut_key"].unique())

print(f"  Grupo Selecto: {len(selecto_df)} docentes")
print(f"  Control B2 (SAT):   {len(ctrl_ruts_b2)}")
print(f"  Control B3 (Notas): {len(ctrl_ruts_b3)}")
print(f"  Control B4 (EDD):   {len(ctrl_ruts_b4)}")

# ── Pivots por etapa individual PRE / DURANTE / POST ───────────────────────────
def _pivot_staged(df, rut_col, val_col, selecto_ruts, is_annual=False):
    """
    Clasifica cada observación como PRE/DURANTE/POST.
    is_annual=True  → staging por año (EDD), usa yr_range.
    is_annual=False → staging por periodo semestral (SAT/Notas), usa per_range.
    """
    sub = df[df[rut_col].isin(selecto_ruts)].copy()

    if is_annual:
        yr  = yr_range.rename(columns={"rut_key": rut_col})
        sub = sub.merge(yr[[rut_col, "yr_min", "yr_max"]], on=rut_col, how="left")
        def _stage(r):
            y, lo, hi = r["year"], r["yr_min"], r["yr_max"]
            if pd.isna(lo) or pd.isna(hi): return None
            if y < lo:  return "PRE"
            if y > hi:  return "POST"
            return "DURANTE"
    else:
        pr  = per_range.rename(columns={"rut_key": rut_col})
        sub = sub.merge(pr[[rut_col, "min_baseline", "max_resultado"]], on=rut_col, how="left")
        def _stage(r):
            p, bl, res = r["periodo"], r["min_baseline"], r["max_resultado"]
            if pd.isna(bl) or pd.isna(res): return None
            if p <= bl:  return "PRE"
            if p >= res: return "POST"
            return "DURANTE"

    sub["stage"] = sub.apply(_stage, axis=1)
    sub = sub[sub["stage"].notna()]
    piv = (sub.groupby([rut_col, "stage"])[val_col]
              .mean().unstack("stage")
              .reindex(columns=STAGES))
    # Solo docentes con datos en PRE *y* POST — sin ambos no hay trayectoria completa
    return piv[piv["PRE"].notna() & piv["POST"].notna()]


def _ctrl_means_sat(df, rut_col, val_col, ctrl_ruts):
    """Control SAT/Notas: 2023→PRE, 2024→DURANTE, 2025→POST."""
    sub = df[df[rut_col].isin(ctrl_ruts)]
    ym  = sub.groupby("year")[val_col].mean()
    return np.array([ym.get(2023, np.nan), ym.get(2024, np.nan), ym.get(2025, np.nan)])


def _ctrl_means_edd(df, rut_col, val_col, ctrl_ruts):
    """Control EDD: 2022→PRE, media(2023+2024)→DURANTE, 2025→POST."""
    sub = df[df[rut_col].isin(ctrl_ruts)]
    ym  = sub.groupby("year")[val_col].mean()
    pre  = ym.get(2022, np.nan)
    vals_dur = [v for v in [ym.get(2023, np.nan), ym.get(2024, np.nan)] if not np.isnan(v)]
    dur  = np.mean(vals_dur) if vals_dur else np.nan
    post = ym.get(2025, np.nan)
    return np.array([pre, dur, post])


pivot_sat  = _pivot_staged(scatter, "rut_docente", "sat",           selecto_ruts, is_annual=False)
pivot_nota = _pivot_staged(scatter, "rut_docente", "nota_promedio", selecto_ruts, is_annual=False)
pivot_edd  = _pivot_staged(edd,     "rut_key",     "edd_pct",       selecto_ruts, is_annual=True)

ctrl_sat   = _ctrl_means_sat(scatter, "rut_docente", "sat",           ctrl_ruts_b2)
ctrl_nota  = _ctrl_means_sat(scatter, "rut_docente", "nota_promedio", ctrl_ruts_b3)
ctrl_edd   = _ctrl_means_edd(edd,     "rut_key",     "edd_pct",       ctrl_ruts_b4)

print(f"  Pivot SAT:  {len(pivot_sat)} doc | Notas: {len(pivot_nota)} | EDD: {len(pivot_edd)}")

# ── Quintiles por SAT PRE: 3 mejores + 3 peores por quintil (1D + 2T) ─────────
_piv3 = pivot_sat[
    pivot_sat["PRE"].notna() & pivot_sat["DURANTE"].notna() & pivot_sat["POST"].notna()
].copy()
_piv3["delta"] = _piv3["POST"] - _piv3["PRE"]

_ruts_diplo_pool  = set(selecto_df[selecto_df["DIPLOMADO"] > 0]["rut_key"])
_ruts_taller_pool = set(selecto_df[selecto_df["DIPLOMADO"] == 0]["rut_key"])
_piv3["diplo"]   = _piv3.index.map(lambda r: str(r) in _ruts_diplo_pool)
_piv3["quintil"] = pd.qcut(_piv3["PRE"], 5, labels=[1,2,3,4,5])

mejores_ruts = set()
peores_ruts  = set()

for _qn in range(1, 6):
    _qdf  = _piv3[_piv3["quintil"] == _qn]
    _qd   = _qdf[_qdf["diplo"]].sort_values("delta", ascending=False)
    _qt   = _qdf[~_qdf["diplo"]].sort_values("delta", ascending=False)
    # Mejores: 1D + 2T (rellena con T si no hay D)
    _m_d  = _qd.head(1).index.tolist()
    _m_t  = _qt.head(2 + (1 - len(_m_d))).index.tolist()
    mejores_ruts |= set(_m_d + _m_t)
    # Peores: 1D + 2T (menores deltas)
    _qd_a = _qdf[_qdf["diplo"]].sort_values("delta", ascending=True)
    _qt_a = _qdf[~_qdf["diplo"]].sort_values("delta", ascending=True)
    _p_d  = _qd_a.head(1).index.tolist()
    _p_t  = _qt_a.head(2 + (1 - len(_p_d))).index.tolist()
    peores_ruts |= set(_p_d + _p_t)

all_sel_ruts = mejores_ruts | peores_ruts
_delta_all   = _piv3["delta"]

selecto_df = (selecto_df[selecto_df["rut_key"].isin(all_sel_ruts)]
              .copy()
              .assign(delta_sat=lambda df: df["rut_key"].map(_delta_all),
                      grupo=lambda df: df["rut_key"].apply(
                          lambda r: "Mejor" if r in mejores_ruts else "Peor"))
              .sort_values(["grupo","delta_sat"], ascending=[True,False])
              .reset_index(drop=True))
selecto_ruts = all_sel_ruts

# Pivots globales y por grupo
pivot_sat  = pivot_sat.loc[ [r for r in pivot_sat.index  if str(r) in all_sel_ruts]]
pivot_nota = pivot_nota.loc[[r for r in pivot_nota.index if str(r) in all_sel_ruts]]
pivot_edd  = pivot_edd.loc[ [r for r in pivot_edd.index  if str(r) in all_sel_ruts]]

piv_sat_mejor  = pivot_sat.loc[ [r for r in pivot_sat.index  if str(r) in mejores_ruts]]
piv_sat_peor   = pivot_sat.loc[ [r for r in pivot_sat.index  if str(r) in peores_ruts]]
piv_nota_mejor = pivot_nota.loc[[r for r in pivot_nota.index if str(r) in mejores_ruts]]
piv_nota_peor  = pivot_nota.loc[[r for r in pivot_nota.index if str(r) in peores_ruts]]
piv_edd_mejor  = pivot_edd.loc[ [r for r in pivot_edd.index  if str(r) in mejores_ruts]]
piv_edd_peor   = pivot_edd.loc[ [r for r in pivot_edd.index  if str(r) in peores_ruts]]

n_mejor = len(piv_sat_mejor); n_peor = len(piv_sat_peor)
print(f"  Quintiles: {n_mejor} mejores + {n_peor} peores = {n_mejor+n_peor} seleccionados")


# ── Ruts selecto con trayectoria completa PRE+POST por bloque ──────────────────
selecto_ruts_pp_sat  = set(pivot_sat.index)
selecto_ruts_pp_nota = set(pivot_nota.index)
selecto_ruts_pp_edd  = set(pivot_edd.index)

print(f"  Doc. con PRE+POST SAT:   {len(selecto_ruts_pp_sat)}")
print(f"  Doc. con PRE+POST Notas: {len(selecto_ruts_pp_nota)}")
print(f"  Doc. con PRE+POST EDD:   {len(selecto_ruts_pp_edd)}")


# ── Eje fijo semestral 2023-S1 → 2025-S2 ──────────────────────────────────────
# Detectar formato real de periodo desde scatter
FIXED_PERIODS = ["2023-01","2023-02","2024-01","2024-02","2025-01","2025-02"]
p2x_fp = {p: i for i, p in enumerate(FIXED_PERIODS)}

def _yr_s1(yr):
    """Índice del primer semestre del año yr en FIXED_PERIODS."""
    for i, p in enumerate(FIXED_PERIODS):
        if str(p)[:4] == str(yr): return i
    return None

def _yr_s2(yr):
    """Índice del segundo semestre del año yr en FIXED_PERIODS."""
    found = [i for i, p in enumerate(FIXED_PERIODS) if str(p)[:4] == str(yr)]
    return found[1] if len(found) >= 2 else (found[0] if found else None)


# ── Spaghetti sobre eje calendario semestral ───────────────────────────────────
def _stage_spag(ax, pivot, is_annual=False, ylabel="", show_legend=True, subtitle=""):
    """
    Eje fijo: 6 semestres 2023-S1→2025-S2 (o 4 años 2022-2025 para EDD).
    Taller  → 3 puntos (PRE/DURANTE/POST) en posiciones semestrales.
    Diplomado/Mixto → 3 puntos al centro del año (PRE/DUR/POST).
    Color = etapa.  Forma = ○ Taller / ◆ Diplomado.
    """
    from matplotlib.lines import Line2D

    def _is_diplo(rut):
        row = selecto_df[selecto_df["rut_key"] == str(rut).strip()]
        return not row.empty and row.iloc[0]["DIPLOMADO"] > 0

    def _get_yr_min(rut):
        row = yr_range[yr_range["rut_key"] == str(rut).strip()]
        return int(row.iloc[0]["yr_min"]) if not row.empty else 2024

    def _get_per_range(rut):
        row = per_range[per_range["rut_key"] == str(rut).strip()]
        if row.empty: return None, None
        return row.iloc[0]["min_baseline"], row.iloc[0]["max_resultado"]

    def _x_pos_sem(rut):
        """Retorna (x_pre, x_dur, x_post) en el eje semestral."""
        diplo = _is_diplo(rut)
        if diplo:
            # Diplomado/Mixto: 3 puntos al CENTRO del año del baseline, año intermedio y año del resultado.
            # PRE  → centro del año que contiene min_baseline  (ej. "2023-02" → año 2023 → x=0.5)
            # DUR  → centro del año siguiente                  (ej. año 2024 → x=2.5)
            # POST → centro del año que contiene max_resultado (ej. "2025-01" → año 2025 → x=4.5)
            bl, res = _get_per_range(rut)
            yr_bl  = int(str(bl)[:4])  if bl  else _get_yr_min(rut)
            yr_res = int(str(res)[:4]) if res else yr_bl + 2
            yr_dur = yr_bl + 1

            def _yr_center(yr):
                s1 = _yr_s1(yr); s2 = _yr_s2(yr)
                if s1 is not None and s2 is not None: return (s1 + s2) / 2.0
                if s1 is not None: return float(s1)
                # Fuera del eje: extrapolar
                return (yr - int(str(FIXED_PERIODS[0])[:4])) * 2 + 0.5

            return _yr_center(yr_bl), _yr_center(yr_dur), _yr_center(yr_res)
        else:
            # Taller: posiciones en el eje semestral derivadas de per_range
            bl, res = _get_per_range(rut)
            n_fp = len(FIXED_PERIODS)
            x_pre  = float(p2x_fp[bl])  if bl  in p2x_fp else -0.5
            x_post = float(p2x_fp[res]) if res in p2x_fp else float(n_fp - 0.5)
            x_dur  = (x_pre + x_post) / 2.0
            return x_pre, x_dur, x_post

    def _x_pos_ann(rut):
        """Para EDD (anual): PRE, DURANTE, POST en años consecutivos."""
        yr   = _get_yr_min(rut)
        yrs  = [2022, 2023, 2024, 2025]
        idx  = yrs.index(yr) if yr in yrs else 2
        return float(idx - 1), float(idx), float(idx + 1)

    n_fp = len(FIXED_PERIODS)

    n = 0
    for rut, row in pivot.iterrows():
        vals = {"PRE":    float(row.get("PRE",    np.nan)),
                "DURANTE":float(row.get("DURANTE",np.nan)),
                "POST":   float(row.get("POST",   np.nan))}
        if np.isnan(vals["PRE"]) or np.isnan(vals["POST"]): continue

        if is_annual:
            x_pre, x_dur, x_post = _x_pos_ann(rut)
            diplo = False
        else:
            x_pre, x_dur, x_post = _x_pos_sem(rut)
            diplo = _is_diplo(rut)

        mkr = "D" if diplo else "o"
        msz = 62  if diplo else 55

        pts = [(x_pre, vals["PRE"], "PRE")]
        if not np.isnan(vals["DURANTE"]):
            pts.append((x_dur, vals["DURANTE"], "DURANTE"))
        pts.append((x_post, vals["POST"], "POST"))

        # Descartar si algún punto cae fuera del rango visible del eje
        n_fp = len(FIXED_PERIODS)
        if any(x < -0.4 or x > n_fp - 0.6 for x, _, _ in pts):
            continue

        # Línea conectora: naranja para diplomados, blanca tenue para talleres
        lc     = COL_LINE_DIPLO if diplo else COL_LINE_TALLER
        lalpha = 0.60          if diplo else 0.42
        lw     = 1.6           if diplo else 1.9
        ax.plot([p[0] for p in pts], [p[1] for p in pts],
                color=lc, alpha=lalpha, linewidth=lw, zorder=2)

        # Puntos coloreados por etapa
        for xp, v, stage in pts:
            ax.scatter(xp, v, color=STAGE_COLS[stage], marker=mkr, s=msz,
                       alpha=0.88, zorder=3, linewidths=0.5, edgecolors="white")
        n += 1

    if is_annual:
        yrs_lbl = [2022, 2023, 2024, 2025]
        ax.set_xlim(-0.5, 3.5)
        ax.set_xticks(range(4))
        ax.set_xticklabels([str(y) for y in yrs_lbl], fontsize=11, color="white")
        # líneas guía en años de formación típica
        for xi in [1, 2]:
            ax.axvline(x=xi, color="white", alpha=0.10, linewidth=1, linestyle="--")
    else:
        ax.set_xlim(-0.5, n_fp - 0.5)
        ax.set_xticks(range(n_fp))
        def _lbl_fp(p):
            s = str(p)
            if len(s) >= 6 and s[4] in "-/": return s[:4]+"\nS"+s[5:].lstrip("0")
            return s
        ax.set_xticklabels([_lbl_fp(p) for p in FIXED_PERIODS], fontsize=10, color="white")
        # Líneas punteadas en centros de año: zona Diplomado
        for i in range(0, n_fp - 1, 2):
            ax.axvline(x=i + 0.5, color="white", alpha=0.12, linewidth=1, linestyle="--")

    ax.tick_params(axis="x", length=0, pad=6)
    _ax_style(ax)
    if ylabel: ax.set_ylabel(ylabel, color="#AAAAAA", fontsize=9)

    legend_els = [
        Line2D([0],[0], color="none", marker="o", markerfacecolor=COL_PRE,  markersize=9,
               markeredgecolor="white", markeredgewidth=0.5, label="● PRE (dorado)"),
        Line2D([0],[0], color="none", marker="o", markerfacecolor=COL_DUR,  markersize=9,
               markeredgecolor="white", markeredgewidth=0.5, label="● DURANTE (azul)"),
        Line2D([0],[0], color="none", marker="o", markerfacecolor=COL_POST, markersize=9,
               markeredgecolor="white", markeredgewidth=0.5, label="● POST (verde)"),
        Line2D([0],[0], color=COL_LINE_TALLER, linewidth=1.5, alpha=0.5, marker="o",
               markerfacecolor="#AAAAAA", markersize=7, markeredgecolor="none", label="○ Taller"),
        Line2D([0],[0], color=COL_LINE_DIPLO,  linewidth=1.8, alpha=0.8, marker="D",
               markerfacecolor="#AAAAAA", markersize=7, markeredgecolor="none", label="◆ Diplomado"),
    ]
    if subtitle:
        ax.set_title(subtitle, color="white", fontsize=9.5, pad=4, fontfamily="Calibri")
    if show_legend:
        ax.legend(handles=legend_els, fontsize=8.5, framealpha=0.28, labelcolor="white",
                  facecolor="#101820", edgecolor="#444", loc="best", ncol=1)
    return n


# ── Slide 1 — Perfil ─────────────────────────────────────────────────────────
def slide_perfil(prs):
    fig=_tr_fig()
    L=PIC_RECT[0]; W=PIC_RECT[2]

    # Área extendida: desde justo bajo POP hasta casi fondo de slide
    ax=fig.add_axes([L+0.02, 0.04, W-0.06, 0.84], facecolor="none", zorder=5)

    N=len(selecto_df)
    y=np.arange(N)

    # Barras apiladas T → D → P
    nt=selecto_df["TALLER"].values
    nd=selecto_df["DIPLOMADO"].values
    np_=selecto_df["PROYECTO"].values

    ax.barh(y[::-1], nt,           height=0.72, color=COL_T, alpha=0.90, label="T  Taller",    edgecolor="none")
    ax.barh(y[::-1], nd, left=nt,  height=0.72, color=COL_D, alpha=0.90, label="D  Diplomado", edgecolor="none")
    ax.barh(y[::-1], np_,left=nt+nd,height=0.72,color=COL_P, alpha=0.90, label="P  Proyecto",  edgecolor="none")

    # Etiqueta total al final
    for i,tot in enumerate(selecto_df["n_inst"]):
        ax.text(tot+0.08, N-1-i, str(tot),
                va="center",ha="left",fontsize=8,fontweight="bold",color="white",
                path_effects=[pe.withStroke(linewidth=2,foreground=DARK_BG)])

    # Marcas de instancia dentro de barra (cada unidad)
    for i,(nt_i,nd_i,np_i) in enumerate(zip(nt,nd,np_)):
        yi=N-1-i
        # Separadores sutiles entre segmentos
        for xb in [nt_i, nt_i+nd_i]:
            if 0<xb<nt_i+nd_i+np_i:
                ax.axvline(x=xb,ymin=(yi-0.36)/N,ymax=(yi+0.36)/N,
                           color="#101820",linewidth=0.8,zorder=6)

    # Nombres en eje Y: "Nombre Apellido"
    def _short(n):
        parts=str(n).title().split()
        return f"{parts[0]} {parts[-1]}" if len(parts)>=2 else parts[0]

    lbls=[_short(n) for n in selecto_df["nombre"]]
    ax.set_yticks(y)
    ax.set_yticklabels(lbls[::-1], fontsize=7.5, color="white", fontweight="normal")
    ax.tick_params(axis="y",length=0,pad=4)
    ax.tick_params(axis="x",colors="#AAAAAA",labelsize=8.5,length=0)
    ax.set_xlim(0, selecto_df["n_inst"].max()*1.20)
    ax.set_ylim(-0.6, N-0.4)
    ax.set_xlabel("Nº de instancias formativas", color="#AAAAAA", fontsize=9)
    for sp in ax.spines.values(): sp.set_edgecolor("white"); sp.set_alpha(0.20); sp.set_linewidth(0.6)
    ax.xaxis.grid(True,color="white",alpha=0.07,linewidth=0.5)
    ax.set_axisbelow(True); ax.set_facecolor("none")

    # Leyenda con abreviaciones
    handles=[Patch(facecolor=COL_T,alpha=0.9,label="T  Taller"),
             Patch(facecolor=COL_D,alpha=0.9,label="D  Diplomado"),
             Patch(facecolor=COL_P,alpha=0.9,label="P  Proyecto")]
    ax.legend(handles=handles,fontsize=9,framealpha=0.28,labelcolor="white",
              facecolor="#101820",edgecolor="#444",loc="lower right",ncol=3)

    _ensure_bg()
    sl=_new_sl(prs); _pic(sl,SHARED_BG,prs); _pic(sl,_save(fig,"sel_perfil.png"),prs)
    _T(sl,"Grupo Selecto — Muestra por Quintil SAT Baseline: Mejores y Peores (3 por quintil)")
    _POP(sl,f"nº {N} docentes  ·  5 quintiles SAT PRE  ·  3 docentes/quintil: 1 Diplomado + 2 Talleres  ·  "
            f"Barras: azul=T (Taller), verde=D (Diplomado), naranja=P (Proyecto)")
    _CT(sl,"Ordenado de mayor a menor nº de instancias  ·  Cada segmento = instancias de ese tipo  ·  "
           f"Mixtos (≥2 tipos): {(selecto_df[['DIPLOMADO','PROYECTO']].sum(axis=1)>0).sum()} docentes")
    print(f"  ✓ Slide 1 — Perfil ({N} docentes)")


# ── Splits por modalidad ──────────────────────────────────────────────────────
# Diplomado (incluyendo mixtos) vs Taller puro
ruts_diplo   = set(selecto_df[selecto_df["DIPLOMADO"] > 0]["rut_key"])
ruts_taller  = set(selecto_df[selecto_df["DIPLOMADO"] == 0]["rut_key"])

def _filter_pivot(piv, ruts_sub):
    """Devuelve el pivot filtrado a los ruts del subgrupo."""
    idx = [r for r in piv.index if str(r).strip() in ruts_sub]
    return piv.loc[idx]


# ── Slides 2-4 — generalizadas (reciben pivot filtrado y etiqueta) ─────────────
def slide_sat(prs, piv, grupo=""):
    fig=_tr_fig(); L,_,W,_=PIC_RECT
    ax=fig.add_axes([L+0.06, 0.09, W-0.10, 0.76],facecolor="none",zorder=5)
    n=_stage_spag(ax, piv, ylabel="SAT (nota 1–7)")
    _ensure_bg()
    tag = f" — {grupo}" if grupo else ""
    sl=_new_sl(prs); _pic(sl,SHARED_BG,prs); _pic(sl,_save(fig,f"sel_sat_{grupo}.png"),prs)
    _T(sl,f"Bloque II — SAT Grupo Selecto{tag}: Trayectoria Individual PRE / DURANTE / POST (nº {n} docentes)")
    _POP(sl,f"Cada línea = 1 docente  ·  Color: Gris=PRE · Azul=DURANTE · Verde=POST  ·  "
            f"Forma: ○=Taller · ◆=Diplomado  ·  Etapas según año real de formación P3 de cada docente")
    _CT(sl,"SAT satisfacción alumno-docente (1–7)  ·  Solo docentes con datos en PRE y POST  ·  "
           "Datos: scatter_sat_notas.csv")
    print(f"  ✓ Slide SAT{tag} ({n} líneas)")


def slide_notas(prs, piv, grupo=""):
    fig=_tr_fig(); L,_,W,_=PIC_RECT
    ax=fig.add_axes([L+0.06, 0.09, W-0.10, 0.76],facecolor="none",zorder=5)
    n=_stage_spag(ax, piv, ylabel="Nota promedio alumnos (1–7)")
    _ensure_bg()
    tag = f" — {grupo}" if grupo else ""
    sl=_new_sl(prs); _pic(sl,SHARED_BG,prs); _pic(sl,_save(fig,f"sel_notas_{grupo}.png"),prs)
    _T(sl,f"Bloque III — Notas Alumnos Grupo Selecto{tag}: Trayectoria Individual PRE / DURANTE / POST (nº {n} docentes)")
    _POP(sl,f"Cada línea = 1 docente  ·  Color: Gris=PRE · Azul=DURANTE · Verde=POST  ·  "
            f"Forma: ○=Taller · ◆=Diplomado  ·  Etapas según año real de formación P3 de cada docente")
    _CT(sl,"Nota promedio alumnos (1–7) por sección  ·  Solo docentes con datos en PRE y POST  ·  "
           "Excluye secciones <7 alumnos y asig. práctica/tesis")
    print(f"  ✓ Slide Notas{tag} ({n} líneas)")


def slide_edd(prs, piv, grupo=""):
    fig=_tr_fig(); L,_,W,_=PIC_RECT
    ax=fig.add_axes([L+0.06, 0.09, W-0.10, 0.76],facecolor="none",zorder=5)
    n=_stage_spag(ax, piv, is_annual=True, ylabel="EDD total (%)")
    _ensure_bg()
    tag = f" — {grupo}" if grupo else ""
    sl=_new_sl(prs); _pic(sl,SHARED_BG,prs); _pic(sl,_save(fig,f"sel_edd_{grupo}.png"),prs)
    _T(sl,f"Bloque IV — EDD Grupo Selecto{tag}: Trayectoria Individual PRE / DURANTE / POST (nº {n} docentes)")
    _POP(sl,f"Cada línea = 1 docente  ·  Color: Gris=PRE · Azul=DURANTE · Verde=POST  ·  "
            f"Forma: ○=Taller · ◆=Diplomado  ·  Etapas según año real de formación P3 de cada docente")
    _CT(sl,"EDD evaluación jefatura directa (0–100%)  ·  Solo docentes con datos en PRE y POST  ·  "
           "Datos: evaluacion_jefes.csv")
    print(f"  ✓ Slide EDD{tag} ({n} líneas)")


def slide_pareado(prs, piv_mejor, piv_peor, ylabel, titulo_bloque, slug):
    """Slide con dos gráficos side-by-side: mejores (izq) | peores (der)."""
    fig = _tr_fig()
    W2 = 0.40; gap = 0.04; L = 0.065; bot = 0.10; H = 0.74
    ax1 = fig.add_axes([L,        bot, W2, H], facecolor="none", zorder=5)
    ax2 = fig.add_axes([L+W2+gap, bot, W2, H], facecolor="none", zorder=5)
    n1 = _stage_spag(ax1, piv_mejor, ylabel=ylabel,
                     show_legend=False, subtitle="▲ Mejores por quintil SAT")
    n2 = _stage_spag(ax2, piv_peor,  ylabel="",
                     show_legend=True,  subtitle="▼ Peores por quintil SAT")
    # Igualar rango Y entre los dos gráficos
    ymin = min(ax1.get_ylim()[0], ax2.get_ylim()[0])
    ymax = max(ax1.get_ylim()[1], ax2.get_ylim()[1])
    ax1.set_ylim(ymin, ymax); ax2.set_ylim(ymin, ymax)
    _ensure_bg()
    sl = _new_sl(prs)
    _pic(sl, SHARED_BG, prs)
    _pic(sl, _save(fig, f"sel_{slug}_pareado.png"), prs)
    _T(sl, f"{titulo_bloque} — Grupo Selecto: Mejores vs Peores por Quintil SAT Baseline")
    _POP(sl, "Quintiles por SAT PRE  ·  3 docentes/quintil (1 Diplomado + 2 Talleres)  ·  "
             "Dorado=PRE · Azul=DURANTE · Verde=POST  ·  Naranja=Diplomado · Blanca=Taller")
    _CT(sl, f"Izq: nº {n1} docentes con mayor mejora SAT en su quintil  ·  "
            f"Der: nº {n2} con menor mejora SAT en su quintil")
    print(f"  ✓ Slide {slug} pareado: {n1} mejores · {n2} peores")


def _gen_pptx(ruts_sub, grupo, out_path):
    """Genera PPTX con 3 slides (SAT, Notas, EDD) filtrado al subgrupo."""
    piv_sat  = _filter_pivot(pivot_sat,  ruts_sub)
    piv_nota = _filter_pivot(pivot_nota, ruts_sub)
    piv_edd  = _filter_pivot(pivot_edd,  ruts_sub)
    _ensure_bg()
    prs = Presentation()
    prs.slide_width  = Emu(SW_EMU)
    prs.slide_height = Emu(SH_EMU)
    slide_sat(prs,   piv_sat,  grupo)
    slide_notas(prs, piv_nota, grupo)
    slide_edd(prs,   piv_edd,  grupo)
    prs.save(str(out_path))
    print(f"  ✓ Guardado: {out_path}  ({len(prs.slides)} slides)")


# ── Main ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    _ensure_bg()

    print(f"\nGenerando GRUPO_SELECTO_v7.pptx …")
    prs_all = Presentation()
    prs_all.slide_width  = Emu(SW_EMU)
    prs_all.slide_height = Emu(SH_EMU)
    slide_perfil(prs_all)
    slide_pareado(prs_all, piv_sat_mejor,  piv_sat_peor,
                  "SAT (nota 1–7)",             "Bloque II — SAT",    "sat")
    slide_pareado(prs_all, piv_nota_mejor, piv_nota_peor,
                  "Nota promedio alumnos (1–7)", "Bloque III — Notas", "notas")
    slide_pareado(prs_all, piv_edd_mejor,  piv_edd_peor,
                  "EDD total (%)",              "Bloque IV — EDD",    "edd")
    prs_all.save(str(OUT_PPTX))
    print(f"  ✓ Guardado: {OUT_PPTX}  ({len(prs_all.slides)} slides)")

