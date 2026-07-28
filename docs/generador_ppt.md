# Especificaciones de Formato — Diapositivas Dark UCEN

Documento de referencia para generar diapositivas con gráfico directo sobre fondo oscuro,
usando el template UCEN (Fondotipop.pptx como fuente de fondo y logo).

Implementación de referencia: `UNIVERSO_918/NOTEBOOKS/poc_slide_facultad_dark.py`

---

## 1. Fuentes de activos

| Asset | Origen | Ruta en archivo ZIP |
|---|---|---|
| Foto de fondo (B&N edificio) | `Fondotipop.pptx` | `ppt/media/image1.jpg` |
| Logo UCEN (blanco/transparente) | `Fondotipop.pptx` | `ppt/media/image2.png` |

Extracción con zipfile estándar de Python. Guardar en scratchpad local para reusar.

---

## 2. Tamaño del slide y sistema de coordenadas

```python
SW, SH = 13.333, 7.5  # pulgadas (PowerPoint estándar 16:9)

# EMU → fracción de figura
def ex(emu): return emu / 12192000   # ancho
def ey(emu): return emu / 6858000    # alto

# Conversión top-left (PPTX) → bottom-left (matplotlib)
def fig_rect(l, t, w, h): return (l, 1 - t - h, w, h)
```

---

## 3. Layout — posiciones de elementos (en EMU)

| Elemento | Left | Top | Width | Height |
|---|---|---|---|---|
| Título diapositiva | 786 582 | 250 608 | 10 599 174 | 553 998 |
| Etiqueta población | 786 582 | 820 000 | 10 599 174 | 290 000 |
| Área gráfico (PIC) | 786 581 | 1 125 000 | 10 599 174 | 3 720 000 |
| Área bullets (BUL) | 786 581 | 4 870 000 | 10 599 174 | 1 870 000 |
| Logo UCEN | 9 813 773 | 656 354 | 1 756 626 | 697 725 |

```python
TITLE_L, TITLE_T, TITLE_W, TITLE_H = ex(786582),  ey(250608),  ex(10599174), ey(553998)
POP_L,   POP_T,   POP_W,   POP_H   = ex(786582),  ey(820000),  ex(10599174), ey(290000)
PIC_L,   PIC_T,   PIC_W,   PIC_H   = ex(786581),  ey(1125000), ex(10599174), ey(3720000)
BUL_L,   BUL_T,   BUL_W,   BUL_H   = ex(786581),  ey(4870000), ex(10599174), ey(1870000)
LOGO_L,  LOGO_T,  LOGO_W,  LOGO_H  = ex(9813773), ey(656354),  ex(1756626),  ey(697725)
```

---

## 4. Área del gráfico (dentro de PIC)

Se deja margen izquierdo (~16%) para etiquetas del eje Y, y se reduce levemente
para que el gráfico no ocupe todo el espacio y tenga borde visible:

```python
CHART_X = PIC_RECT[0] + 0.16   # margen izquierdo para etiquetas Y
CHART_W = PIC_RECT[2] - 0.16 - 0.02
CHART_Y = PIC_RECT[1] + 0.04   # margen inferior (espacio eje X)
CHART_H = PIC_RECT[3] - 0.09
```

---

## 5. Fondo — foto + gradiente navy

### 5a. Foto del edificio
```python
from PIL import Image as PILImage
with PILImage.open(BG_PATH) as _im:
    _im_rgb = _im.convert("RGB")
    _iw, _ih = _im_rgb.size
    _new_h = int(_iw / (16 / 9))         # crop 16:9
    _y0 = min(int(_ih * 0.12), _ih - _new_h)  # empezar 12% desde arriba
    _im_rgb = _im_rgb.crop((0, _y0, _iw, _y0 + _new_h))
    bg_arr = np.array(_im_rgb)
```

No se aplica colorización — la foto se usa tal cual (modo L convertido a RGB).
El tono oscuro lo provee el gradiente encima.

### 5b. Gradiente navy overlay

Extraído del slide master de `Fondotipop.pptx` (XML `<a:gradFill>`, ángulo 90°, alpha 80 000):

| Posición | Color | Hex |
|---|---|---|
| 0% (arriba) | Navy casi negro | `#002147` |
| 54% (medio) | Navy medio | `#004680` |
| 100% (abajo) | Azul acero | `#90ABC4` |

```python
H_GRAD = 600
grad   = np.zeros((H_GRAD, 1, 4), dtype=np.float32)
stops  = [(0.00, (0x00, 0x21, 0x47)),
          (0.54, (0x00, 0x46, 0x80)),
          (1.00, (0x90, 0xAB, 0xC4))]
for row in range(H_GRAD):
    t = row / (H_GRAD - 1)
    for i in range(len(stops) - 1):
        t0, c0 = stops[i]; t1, c1 = stops[i + 1]
        if t0 <= t <= t1:
            s = (t - t0) / (t1 - t0)
            r = c0[0] + s*(c1[0]-c0[0])
            g = c0[1] + s*(c1[1]-c0[1])
            b = c0[2] + s*(c1[2]-c0[2])
            grad[row, 0] = [r/255, g/255, b/255, 0.82]   # 82% opacidad
            break
```

### 5c. Capas en la figura

```python
fig = plt.figure(figsize=(SW, SH), facecolor="#101820")  # dk1 del tema UCEN
fig.patch.set_facecolor("#101820")

ax_bg = fig.add_axes([0, 0, 1, 1], zorder=0)
ax_bg.imshow(bg_arr, extent=[0,1,0,1], aspect="auto", origin="upper")
ax_bg.set_xlim(0,1); ax_bg.set_ylim(0,1); ax_bg.axis("off")

ax_gd = fig.add_axes([0, 0, 1, 1], zorder=1)
ax_gd.imshow(grad, extent=[0,1,0,1], aspect="auto", origin="upper")
ax_gd.set_xlim(0,1); ax_gd.set_ylim(0,1); ax_gd.axis("off")
```

---

## 6. Elementos de texto superpuestos

### 6a. Título de la diapositiva
- Posición: centrado horizontalmente, verticalmente a `(1.0 + CHART_Y + CHART_H + 0.020) / 2 + 0.018`
- Fuente: Arial 20pt bold, color **blanco**
- Sin recuadro (no title bar)

```python
_title_y = (1.0 + CHART_Y + CHART_H + 0.020) / 2 + 0.018
fig.text(T_RECT[0] + T_RECT[2] / 2, _title_y,
         "Título de la Diapositiva",
         ha="center", va="center", fontsize=20, fontweight="bold",
         color="white", transform=fig.transFigure, zorder=4)
```

### 6b. Logo UCEN (esquina superior derecha)
- Usar `image2.png` (letras blancas JCEN sobre transparente)
- Posición exacta del slide master

```python
LOGO_RECT = fig_rect(LOGO_L, LOGO_T, LOGO_W, LOGO_H)
ax_logo = fig.add_axes([LOGO_RECT[0], LOGO_RECT[1], LOGO_RECT[2], LOGO_RECT[3]],
                        zorder=10, facecolor="none")
ax_logo.imshow(logo_arr, aspect="auto"); ax_logo.axis("off")
ax_logo.patch.set_visible(False)
```

### 6c. Etiqueta de población
- Fuente: Arial 7.5pt italic, color `#C8DCF0`
- Alineada al borde izquierdo del área PIC

```python
POP_Y = 1 - POP_T - POP_H / 2
fig.text(PIC_RECT[0], POP_Y,
         "Universo: N Aptos  ·  detalle  ·  SAT disponible ...",
         ha="left", va="center", fontsize=7.5, fontstyle="italic",
         color="#C8DCF0", transform=fig.transFigure, zorder=4)
```

### 6d. Título del gráfico
- Una línea en blanco (no bold), justo encima del área del chart
- Fuente: Arial 10pt, color blanco

```python
fig.text(CHART_X - 0.005, CHART_Y + CHART_H + 0.008,
         "Título del gráfico — Universo (n=X con dato)",
         ha="left", va="bottom", fontsize=10, color="white",
         transform=fig.transFigure, zorder=7)
```

---

## 7. Gráfico de barras horizontales

- Fondo transparente (sin caja blanca): `facecolor="none"`
- Borde blanco sutil en los 4 lados: `edgecolor="white", alpha=0.35, linewidth=0.9`
- Paleta adaptada para fondo oscuro (colores brillantes/claros)

```python
PALETTE_DARK = ["#5C9BD6","#64B5F6","#80DEEA","#A5D6A7",
                "#FFB74D","#CE93D8","#90A4AE","#F48FB1"]

ax = fig.add_axes([CHART_X, CHART_Y, CHART_W, CHART_H],
                  facecolor="none", zorder=5)
ax.barh(y[::-1], vals, color=PALETTE_DARK[:n], height=0.58,
        edgecolor="none", alpha=0.90)

# Etiquetas de valor con sombra oscura para legibilidad
import matplotlib.patheffects as pe
ax.text(v + max_val*0.015, i, f"{v}  ({p:.1f}%)",
        va="center", ha="left", fontsize=10.5, fontweight="bold", color=c,
        path_effects=[pe.withStroke(linewidth=2.5, foreground="#0A0F18")])

# Etiquetas eje Y en blanco
ax.set_yticklabels(labels[::-1], fontsize=10.5, fontweight="bold", color="white")
ax.tick_params(axis="y", length=0, pad=8)
ax.tick_params(axis="x", colors="#AAAAAA", labelsize=9)

# Borde blanco sutil
for sp in ax.spines.values():
    sp.set_visible(True); sp.set_edgecolor("white")
    sp.set_alpha(0.35); sp.set_linewidth(0.9)

ax.set_xlim(0, max(vals) * 1.35)
ax.xaxis.grid(True, color="white", alpha=0.07, linewidth=0.5, zorder=0)
ax.set_axisbelow(True)
```

---

## 8. Bullets — área inferior

- Bounded exactamente: izquierda = `PIC_L`, derecha = `CHART_X + CHART_W`
- Fuente: Arial 11.5pt, color blanco
- Wrap con `textwrap` a 130 chars para que las líneas llenen el ancho sin cortar palabras
- Axes con `clip_on=True` para que el texto no exceda el borde derecho

```python
import textwrap

BUL_BOTTOM = 1 - BUL_T - BUL_H
BUL_AX_W   = CHART_X + CHART_W - PIC_L
ax_bul = fig.add_axes([PIC_L, BUL_BOTTOM, BUL_AX_W, BUL_H],
                      facecolor="none", zorder=6)
ax_bul.set_xlim(0,1); ax_bul.set_ylim(0,1)
ax_bul.axis("off"); ax_bul.patch.set_visible(False)

WRAP_W    = 130
line_h_ax = 0.023 / BUL_H
gap_ax    = 0.012 / BUL_H
cur_y_ax  = 1.0 - (0.040 / BUL_H)

bullets = [
    "1.  Texto del primer hallazgo con datos concretos y referencia.",
    "2.  Texto del segundo hallazgo.",
    "3.  Texto del tercer hallazgo.",
]

for text in bullets:
    wrapped = textwrap.wrap(text, width=WRAP_W, subsequent_indent="    ")
    for line in wrapped:
        ax_bul.text(0.0, cur_y_ax, line,
                    ha="left", va="top", fontsize=11.5, color="white",
                    transform=ax_bul.transAxes, clip_on=True)
        cur_y_ax -= line_h_ax
    cur_y_ax -= gap_ax
```

---

## 9. Exportación

```python
# Sin bbox_inches="tight" para respetar exactamente el tamaño del slide
plt.savefig("salida.pdf", format="pdf", dpi=150, facecolor=fig.get_facecolor())
plt.savefig("salida.png", format="png", dpi=150, facecolor=fig.get_facecolor())
plt.close()
```

---

## 10. Paleta de colores del tema UCEN

| Rol | Nombre | Hex |
|---|---|---|
| Fondo base (dk1) | Navy casi negro | `#101820` |
| Acento 1 (barra título v. claro) | Azul acero | `#90ABC4` |
| Texto oscuro (dk2) | Azul navy | `#004680` |
| Highlight | Azul brillante | `#0072E6` |
| Texto pop tag | Azul claro | `#C8DCF0` |

---

## 11. Checklist de una nueva diapositiva dark

- [ ] Extraer `image1.jpg` y `image2.png` de `Fondotipop.pptx`
- [ ] Figura facecolor `#101820`, capa foto + capa gradiente navy
- [ ] Título en blanco bold, centrado en la zona superior
- [ ] Logo UCEN (image2.png) en esquina superior derecha
- [ ] Etiqueta de población en itálica `#C8DCF0`
- [ ] Título del gráfico: una línea blanca sobre el chart
- [ ] Gráfico con `facecolor="none"`, borde blanco sutil, paleta PALETTE_DARK
- [ ] Bullets en axes acotado `[PIC_L → CHART_X+CHART_W]`, textwrap 130 chars, 11.5pt
- [ ] Exportar sin `bbox_inches="tight"`
