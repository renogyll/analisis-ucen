"""
shared/pptx_helpers.py
Plantilla visual UCEN compartida: fondo con degradado + logo, título, bajada
(descripción de universo/población) y punteo numerado al pie.

Reemplaza el bloque de ~100 líneas que cada script de P3 copiaba y pegaba
individualmente (carga de Fondotipop.pptx, degradado, helpers de texto,
constantes de layout) — acá vive una sola vez.

CONVENCIONES (2026-08-01, pedido explícito de la contraparte) — aplican a
todos los productos:
  - Cualquier mención de un tamaño de muestra en leyendas, punteos o bajadas
    se escribe "N°=", nunca "n=" — ej. `label=f"Hombre  (N°={n_hombre})"`.
  - La bajada (`subtitulo()`) NO debe mencionar el nombre del archivo/CSV
    fuente (ej. nada de "Fuente: docentes_jornada.csv") — es un detalle interno
    de la generación, no aporta nada para la contraparte. Sí describir el
    universo/población en palabras (ej. "Universo: 624 docentes Jornada").

Uso típico (un script por sub-tema en products/<producto>/<carpeta>/<subtema>/):

    import sys; sys.stdout.reconfigure(encoding="utf-8")  # evita UnicodeEncodeError en consola Windows
    from pathlib import Path
    ROOT = Path(__file__).resolve().parents[4]   # ajustar según profundidad real
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "shared"))
    from config import CASCADE
    from pptx_helpers import UcenSlideKit
    from pptx import Presentation
    from pptx.util import Emu

    kit = UcenSlideKit(out_dir=Path(__file__).parent)
    kit.ensure_bg()

    prs = Presentation()
    prs.slide_width, prs.slide_height = Emu(kit.SW_EMU), Emu(kit.SH_EMU)

    fig = kit.new_chart_fig()
    ax = kit.chart_axes(fig)
    # ... dibujar el gráfico en ax ...
    chart_path = kit.save_chart(fig, "mi_grafico.png")

    sl = kit.new_slide(prs)
    kit.pic(sl, prs, kit.SHARED_BG)          # fondo, a pantalla completa
    kit.pic_chart(sl, prs, chart_path)       # gráfico, en su caja real (más chico y centrado)
    kit.title(sl, "Título de la diapositiva")
    kit.subtitulo(sl, "Universo: 624 docentes Jornada  ·  513 con dato disponible")
    kit.punteo_numerado(sl, ["Primer hallazgo...", "Segundo hallazgo..."])
    prs.save(OUT_PPTX)
"""
import os
import zipfile
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from PIL import Image as PILImage
from pptx.util import Emu, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
import sys
sys.path.insert(0, str(_ROOT))
from config import ASSETS

FONDOTIPO = os.path.join(ASSETS, "Fondotipop.pptx")


class UcenSlideKit:
    """Plantilla visual UCEN (fondo + título + bajada + punteo numerado).

    Una instancia por carpeta de salida (out_dir) — el fondo generado se
    cachea ahí como `_background.png` para no recalcularlo en cada corrida.
    """

    # ── Layout ──────────────────────────────────────────────────────────────
    # SW/SH en pulgadas; el resto en EMU (914400 EMU = 1 pulgada).
    # CONTENT_* = ancho de texto (título/bajada/punteo) — franja amplia, fija.
    # CHART_*   = caja del gráfico — más angosta y centrada, independiente del
    #             ancho de texto (así el gráfico se ve "más chico y centrado"
    #             sin angostar el título/bajada/punteo).
    SW, SH = 13.333, 7.5
    SW_EMU, SH_EMU = 12192000, 6858000
    _IN = 914400  # 1 pulgada en EMU

    CONTENT_L, CONTENT_W = 786581, 10599174   # franja de texto (título/bajada/punteo)
    LOGO_L, LOGO_T, LOGO_W, LOGO_H = 9813773, 656354, 1756626, 697725

    TITLE_L, TITLE_T, TITLE_W, TITLE_H = CONTENT_L, int(0.30 * _IN), CONTENT_W, int(0.50 * _IN)

    # Gap título→bajada == gap bajada→gráfico == 0.55" (misma constante _GAP_TB
    # para las dos, a pedido expreso del usuario — "mantener la distancia
    # igualitaria de título con gráfico"). Gráfico y punteo corridos más abajo
    # (2026-08-01, 2do ajuste) para usar todo el alto de la diapositiva.
    _GAP_TB = int(0.55 * _IN)
    POP_L, POP_W, POP_H = CONTENT_L, CONTENT_W, int(0.30 * _IN)
    POP_T = TITLE_T + TITLE_H + _GAP_TB

    CHART_W = int(9.5 * _IN)
    CHART_L = (SW_EMU - CHART_W) // 2                      # centrado horizontal
    CHART_T = POP_T + POP_H + _GAP_TB
    CHART_H = int(3.3 * _IN)

    BUL_L, BUL_W = CONTENT_L, CONTENT_W
    BUL_T = CHART_T + CHART_H + int(0.65 * _IN)             # gap gráfico→punteo
    BUL_H = int(1.10 * _IN)

    # Alias retrocompatibles (algunos scripts ya usan PIC_*)
    PIC_L, PIC_T, PIC_W, PIC_H = CHART_L, CHART_T, CHART_W, CHART_H

    def __init__(self, out_dir):
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.SHARED_BG = str(self.out_dir / "_background.png")
        self._bg_arr = None
        self._logo_arr = None
        self._grad = None

    # ── Fracciones matplotlib para figuras transparentes superpuestas ─────────
    def _ex(self, e): return e / self.SW_EMU
    def _ey(self, e): return e / self.SH_EMU
    def _fig_rect(self, l, t, w, h): return (l, 1 - t - h, w, h)

    def chart_rect(self, pad=0.0):
        """Rectángulo (l, b, w, h) en fracción de figura para el área del gráfico."""
        r = self._fig_rect(self._ex(self.PIC_L), self._ey(self.PIC_T),
                            self._ex(self.PIC_W), self._ey(self.PIC_H))
        if pad:
            return (r[0] + pad, r[1] + pad, r[2] - 2 * pad, r[3] - 2 * pad)
        return r

    # ── Fondo UCEN (extrae assets de Fondotipop.pptx, cachea en out_dir) ──────
    def _load_assets(self):
        if self._bg_arr is not None:
            return
        bg_path = self.out_dir / "_fondotipo_bg.jpg"
        logo_path = self.out_dir / "_fondotipo_logo.png"
        for path, zname in [(bg_path, "ppt/media/image1.jpg"),
                             (logo_path, "ppt/media/image2.png")]:
            if not path.exists():
                with zipfile.ZipFile(FONDOTIPO) as z:
                    with open(path, "wb") as f:
                        f.write(z.read(zname))

        with PILImage.open(bg_path) as im:
            rgb = im.convert("RGB"); iw, ih = rgb.size
            nh = int(iw / (16 / 9)); y0 = min(int(ih * 0.12), ih - nh)
            self._bg_arr = np.array(rgb.crop((0, y0, iw, y0 + nh)))

        with PILImage.open(logo_path) as logo:
            self._logo_arr = np.array(logo.convert("RGBA")).astype(np.float32) / 255.0

        h_grad = 600
        grad = np.zeros((h_grad, 1, 4), dtype=np.float32)
        stops = [(0.00, (0, 33, 71)), (0.54, (0, 70, 128)), (1.00, (144, 171, 196))]
        for r in range(h_grad):
            t = r / (h_grad - 1)
            for i in range(len(stops) - 1):
                t0, c0 = stops[i]; t1, c1 = stops[i + 1]
                if t0 <= t <= t1:
                    s = (t - t0) / (t1 - t0)
                    grad[r, 0] = [(c0[0] + s * (c1[0] - c0[0])) / 255,
                                  (c0[1] + s * (c1[1] - c0[1])) / 255,
                                  (c0[2] + s * (c1[2] - c0[2])) / 255, 0.82]
                    break
        self._grad = grad

    def _bg_fig(self):
        self._load_assets()
        logo_rect = self._fig_rect(self._ex(self.LOGO_L), self._ey(self.LOGO_T),
                                    self._ex(self.LOGO_W), self._ey(self.LOGO_H))
        fig = plt.figure(figsize=(self.SW, self.SH), facecolor="#101820")
        fig.patch.set_facecolor("#101820")
        for z, arr in [(0, self._bg_arr), (1, self._grad)]:
            ax = fig.add_axes([0, 0, 1, 1], zorder=z)
            ax.imshow(arr, extent=[0, 1, 0, 1], aspect="auto", origin="upper")
            ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
        al = fig.add_axes(logo_rect, zorder=10, facecolor="none")
        al.imshow(self._logo_arr, aspect="auto"); al.axis("off"); al.patch.set_visible(False)
        return fig

    def ensure_bg(self):
        """Genera y cachea `_background.png` en out_dir si no existe todavía."""
        if not os.path.exists(self.SHARED_BG):
            fig = self._bg_fig()
            plt.savefig(self.SHARED_BG, dpi=150, facecolor=fig.get_facecolor())
            plt.close(fig)

    # ── Figuras de gráfico (transparentes, se superponen sobre el fondo) ──────
    def new_fig(self):
        """[modo legacy] Figura del tamaño completo de la diapositiva — usar
        junto con `chart_rect()` + `pic()`. Deja mucho margen transparente
        alrededor del gráfico en el PNG resultante; para un PNG ajustado al
        contenido (recomendado) usar `new_chart_fig()` + `pic_chart()`."""
        fig = plt.figure(figsize=(self.SW, self.SH), facecolor="none")
        fig.patch.set_facecolor("none")
        return fig

    def new_chart_fig(self):
        """Figura transparente del tamaño real de la caja del gráfico (CHART_W ×
        CHART_H), no de la diapositiva completa. El PNG queda ajustado al
        contenido — usar junto con `chart_axes()` + `pic_chart()`."""
        w_in = self.CHART_W / self._IN
        h_in = self.CHART_H / self._IN
        fig = plt.figure(figsize=(w_in, h_in), facecolor="none")
        fig.patch.set_facecolor("none")
        return fig

    def chart_axes(self, fig, left=0.075, right=0.02, top=0.06, bottom=0.16):
        """Ejes dentro de la figura creada con `new_chart_fig()`. Márgenes
        asimétricos por defecto — dejan espacio para xlabel/xticklabels
        (bottom) e ylabel/yticklabels (left) sin que se corten."""
        return fig.add_axes([left, bottom, 1 - left - right, 1 - top - bottom],
                             facecolor="none", zorder=5)

    def save_chart(self, fig, name):
        path = str(self.out_dir / name)
        plt.savefig(path, dpi=150, facecolor="none", transparent=True)
        plt.close(fig)
        return path

    # ── Helpers python-pptx ────────────────────────────────────────────────────
    def new_slide(self, prs):
        return prs.slides.add_slide(prs.slide_layouts[6])

    def pic(self, sl, prs, path):
        """Imagen a pantalla completa (para el fondo `SHARED_BG`)."""
        sl.shapes.add_picture(path, Emu(0), Emu(0), prs.slide_width, prs.slide_height)

    def pic_chart(self, sl, prs, chart_path):
        """Coloca el PNG del gráfico (generado con `new_chart_fig()`) en su
        posición y tamaño reales (CHART_L/T/W/H) — más chico y centrado,
        no a pantalla completa."""
        sl.shapes.add_picture(chart_path, Emu(self.CHART_L), Emu(self.CHART_T),
                               Emu(self.CHART_W), Emu(self.CHART_H))

    def txt(self, sl, text, left, top, width, height, fs=12, bold=False, italic=False,
            color="#FFFFFF", align=PP_ALIGN.LEFT, wrap=True, lspc=0, font_name="Calibri"):
        txb = sl.shapes.add_textbox(Emu(left), Emu(top), Emu(width), Emu(height))
        tf = txb.text_frame; tf.word_wrap = wrap
        for i, line in enumerate(str(text).split("\n")):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.alignment = align
            if lspc > 0 and i > 0:
                p.space_before = Pt(lspc)
            run = p.add_run(); run.text = line
            run.font.size = Pt(fs); run.font.bold = bold; run.font.italic = italic
            if font_name:
                run.font.name = font_name
            r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
            run.font.color.rgb = RGBColor(r, g, b)

    def title(self, sl, text, fs=20):
        """Título de la diapositiva."""
        self.txt(sl, text, self.TITLE_L, self.TITLE_T, self.TITLE_W, self.TITLE_H,
                  fs=fs, bold=True, color="#FFFFFF", align=PP_ALIGN.CENTER)

    def subtitulo(self, sl, text):
        """Bajada explicativa de universo/población, bajo el título.
        No mencionar el nombre del archivo/CSV fuente (ej. "Fuente: x.csv") —
        es un detalle interno, no aporta nada para la contraparte."""
        self.txt(sl, text, self.POP_L, self.POP_T, self.POP_W, self.POP_H,
                  fs=10, italic=True, color="#C8DCF0", font_name="Calibri")

    def punteo_numerado(self, sl, items, fs=13):
        """Lista numerada (1. 2. ...) al pie de la diapositiva."""
        txb = sl.shapes.add_textbox(Emu(self.BUL_L), Emu(self.BUL_T),
                                     Emu(self.BUL_W), Emu(self.BUL_H))
        tf = txb.text_frame; tf.word_wrap = True
        for i, item in enumerate(items):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.space_after = Pt(6); p.alignment = PP_ALIGN.LEFT
            run = p.add_run(); run.text = f"{i + 1}.  {item}"
            run.font.size = Pt(fs)
            run.font.name = "Calibri"
            run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
