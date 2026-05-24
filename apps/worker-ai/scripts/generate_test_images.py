"""
Generate synthetic scanned-style contract PNGs for local testing.

Creates four PNG renders that imitate legal scans:
  - pair1_original.png  : Consulting services agreement (original)
  - pair1_amendment.png : Consulting agreement amendment
  - pair2_original.png  : NDA template (original)
  - pair2_amendment.png : NDA amendment

Usage:
    cd hry-final-aie-felipegarcia/
    python scripts/generate_test_images.py
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


# ── Fixture contract plaintext (Spanish, for OCR realism) ───────────────────

PAIR1_ORIGINAL = """\
CONTRATO DE SERVICIOS DE CONSULTORÍA

Entre las partes:
  CONTRATANTE: TechCorp S.A., con domicilio en Av. Libertador 1200, CABA.
  CONSULTOR:   DataSolutions LLC, con domicilio en Corrientes 550, CABA.

Fecha de entrada en vigor: 1 de enero de 2024.

CLÁUSULA 1 — OBJETO DEL CONTRATO
El Consultor prestará servicios de análisis de datos y desarrollo de
modelos de machine learning para el Contratante durante el período
comprendido entre el 1 de enero y el 31 de diciembre de 2024.

CLÁUSULA 2 — DURACIÓN
El presente contrato tendrá una duración de doce (12) meses, con
posibilidad de renovación automática por períodos iguales salvo
notificación escrita con 30 días de anticipación.

CLÁUSULA 3 — HONORARIOS Y CONDICIONES DE PAGO
3.1 El Contratante abonará al Consultor la suma de USD 8.000
    (ocho mil dólares estadounidenses) mensuales.
3.2 El pago se realizará dentro de los primeros 10 días hábiles
    de cada mes.
3.3 Las facturas vencidas generarán un interés del 1,5% mensual.

CLÁUSULA 4 — ENTREGABLES
El Consultor entregará mensualmente:
  a) Informe de avance del proyecto.
  b) Modelos entrenados y documentados.
  c) Código fuente en repositorio privado compartido.

CLÁUSULA 5 — RESPONSABILIDAD
El Consultor no será responsable por daños indirectos, lucro cesante
ni pérdidas consecuentes derivadas del uso de los entregables.

CLÁUSULA 6 — LEY APLICABLE
Este contrato se rige por las leyes de la República Argentina.
Cualquier controversia será resuelta ante los tribunales ordinarios
de la Ciudad Autónoma de Buenos Aires.

Firmado en Buenos Aires a los 1 días del mes de enero de 2024.

____________________          ____________________
TechCorp S.A.                 DataSolutions LLC
"""

PAIR1_AMENDMENT = """\
PRIMERA ENMIENDA AL CONTRATO DE SERVICIOS DE CONSULTORÍA

Entre las partes:
  CONTRATANTE: TechCorp S.A., con domicilio en Av. Libertador 1200, CABA.
  CONSULTOR:   DataSolutions LLC, con domicilio en Corrientes 550, CABA.

Fecha de la enmienda: 1 de julio de 2024.

Las partes acuerdan modificar el Contrato de Servicios de Consultoría
firmado el 1 de enero de 2024 (en adelante, "el Contrato Original")
en los siguientes términos:

ARTÍCULO 1 — MODIFICACIÓN DE LA CLÁUSULA 3 (HONORARIOS Y PAGOS)
La Cláusula 3 del Contrato Original queda reemplazada en su totalidad
por el siguiente texto:

  3.1 El Contratante abonará al Consultor la suma de USD 10.500
      (diez mil quinientos dólares estadounidenses) mensuales,
      a partir del 1 de agosto de 2024.
  3.2 El pago se realizará dentro de los primeros 5 días hábiles
      de cada mes (se reduce el plazo de 10 a 5 días hábiles).
  3.3 Las facturas vencidas generarán un interés del 2% mensual.
  3.4 NUEVO: El Contratante abonará un bono de desempeño del 10% del
      valor mensual si se cumplen los KPIs acordados en el Anexo A.

ARTÍCULO 2 — INCORPORACIÓN DE CLÁUSULA 5-BIS (LIMITACIÓN DE RESPONSABILIDAD)
Se incorpora una nueva cláusula 5-BIS con el siguiente texto:

  CLÁUSULA 5-BIS — TOPE DE RESPONSABILIDAD
  La responsabilidad total máxima del Consultor frente al Contratante,
  por cualquier concepto, no podrá exceder el equivalente a tres (3)
  mensualidades del honorario vigente al momento del reclamo.

ARTÍCULO 3 — VIGENCIA DE LA ENMIENDA
Las modificaciones establecidas en la presente enmienda entrarán en
vigor el 1 de agosto de 2024 y se mantendrán hasta la finalización
del Contrato Original. El resto de las cláusulas del Contrato Original
permanecen vigentes sin modificación.

Firmado en Buenos Aires a los 1 días del mes de julio de 2024.

____________________          ____________________
TechCorp S.A.                 DataSolutions LLC
"""

PAIR2_ORIGINAL = """\
ACUERDO DE CONFIDENCIALIDAD Y NO DIVULGACIÓN (NDA)

Entre las partes:
  PARTE DIVULGANTE: Innovatech S.R.L., CUIT 30-71234567-0.
  PARTE RECEPTORA:  Carlos Martínez, DNI 28.456.789.

Fecha de firma: 15 de marzo de 2024.

1. INFORMACIÓN CONFIDENCIAL
   Se considera "Información Confidencial" toda información técnica,
   comercial, financiera o estratégica divulgada por la Parte Divulgante
   a la Parte Receptora, ya sea de forma oral, escrita o digital.

2. OBLIGACIONES DE CONFIDENCIALIDAD
   La Parte Receptora se compromete a:
   a) No divulgar la Información Confidencial a terceros sin consentimiento
      escrito previo de la Parte Divulgante.
   b) Utilizar la Información Confidencial exclusivamente para los fines
      del proyecto "Plataforma de IA Generativa v2.0".
   c) Implementar medidas de seguridad razonables para proteger
      la Información Confidencial.

3. PERÍODO DE CONFIDENCIALIDAD
   Las obligaciones establecidas en este acuerdo tendrán una duración
   de dos (2) años contados desde la fecha de firma.

4. EXCLUSIONES
   No se considerará Información Confidencial aquella que:
   a) Sea o se vuelva de dominio público sin culpa de la Parte Receptora.
   b) Ya estuviera en posesión legítima de la Parte Receptora antes
      de la fecha de divulgación.

5. CONSECUENCIAS DEL INCUMPLIMIENTO
   El incumplimiento de las obligaciones del presente acuerdo dará
   derecho a la Parte Divulgante a reclamar daños y perjuicios.

6. JURISDICCIÓN
   Este acuerdo se rige por la ley argentina. Las disputas se resolverán
   en los tribunales de la Ciudad de Buenos Aires.

____________________          ____________________
Innovatech S.R.L.             Carlos Martínez
"""

PAIR2_AMENDMENT = """\
PRIMERA ENMIENDA AL ACUERDO DE CONFIDENCIALIDAD Y NO DIVULGACIÓN

Entre las partes:
  PARTE DIVULGANTE: Innovatech S.R.L., CUIT 30-71234567-0.
  PARTE RECEPTORA:  Carlos Martínez, DNI 28.456.789.

Fecha de la enmienda: 10 de septiembre de 2024.

Las partes acuerdan modificar el Acuerdo de Confidencialidad firmado
el 15 de marzo de 2024 en los siguientes términos:

ARTÍCULO 1 — MODIFICACIÓN DE LA CLÁUSULA 3 (PERÍODO DE CONFIDENCIALIDAD)
El período de confidencialidad establecido en la Cláusula 3 se extiende
de dos (2) a cinco (5) años contados desde la fecha de firma original.
Esta extensión se aplica retroactivamente desde el 15 de marzo de 2024.

ARTÍCULO 2 — MODIFICACIÓN DE LA CLÁUSULA 4 (EXCLUSIONES)
Se agrega un nuevo inciso c) a la Cláusula 4:
  c) Haya sido recibida de un tercero que no estuviera sujeto a
     obligaciones de confidencialidad respecto de dicha información.
  d) NUEVO: Deba ser divulgada por mandato legal, orden judicial o
     requerimiento de autoridad competente, siempre que la Parte
     Receptora notifique previamente a la Parte Divulgante con al
     menos 72 horas de anticipación, salvo que la ley lo prohíba.

ARTÍCULO 3 — INCORPORACIÓN DE CLÁUSULA 3-BIS (ALCANCE AMPLIADO)
Se incorpora la siguiente cláusula 3-BIS:

  CLÁUSULA 3-BIS — INFORMACIÓN DE TERCEROS
  Las obligaciones de confidencialidad se extienden a la Información
  Confidencial de terceros que la Parte Divulgante custodie o gestione
  en el marco del proyecto mencionado en la Cláusula 2(b).

ARTÍCULO 4 — CONSECUENCIAS DEL INCUMPLIMIENTO (REEMPLAZO)
La Cláusula 5 queda reemplazada por:

  En caso de incumplimiento, la Parte Receptora deberá abonar una
  penalidad de USD 50.000 (cincuenta mil dólares) por cada evento
  de divulgación no autorizada, sin perjuicio de los daños y
  perjuicios adicionales que pudieran acreditarse.

ARTÍCULO 5 — VIGENCIA
Los artículos 1 a 4 de esta enmienda entran en vigor en la fecha
de su firma. Las cláusulas no modificadas permanecen vigentes.

____________________          ____________________
Innovatech S.R.L.             Carlos Martínez
"""

# ── Raster layout ────────────────────────────────────────────────────────────
PAGE_W = 850
PAGE_H = 1100
MARGIN = 50
FONT_SIZE = 13
LINE_SPACING = 5
BG_COLOR = (255, 255, 255)
TEXT_COLOR = (20, 20, 20)


def _get_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Try common monospace fonts; fall back to PIL default bitmap font."""
    candidates = [
        "/System/Library/Fonts/Courier.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
        "cour.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except (IOError, OSError):
            continue
    return ImageFont.load_default()


def render_contract_image(text: str, output_path: Path, title: str = "") -> None:
    """
    Render contract plaintext as a PNG image.

    Args:
        text: Full contract body to paint.
        output_path: Destination PNG path.
        title: Optional console label when saving.
    """
    font = _get_font(FONT_SIZE)
    font_bold = _get_font(FONT_SIZE + 1)

    lines = text.split("\n")
    line_height = FONT_SIZE + LINE_SPACING
    total_height = max(PAGE_H, MARGIN * 2 + len(lines) * line_height + 20)

    img = Image.new("RGB", (PAGE_W, total_height), color=BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Light border suggesting a scanned page
    draw.rectangle(
        [(10, 10), (PAGE_W - 10, total_height - 10)],
        outline=(200, 200, 200),
        width=1,
    )

    y = MARGIN
    for line in lines:
        current_font = font_bold if line.isupper() and len(line) > 5 else font
        draw.text((MARGIN, y), line, fill=TEXT_COLOR, font=current_font)
        y += line_height

    # Clamp height short pages upward to PAGE_H
    final_height = min(total_height, max(PAGE_H, y + MARGIN))
    img = img.crop((0, 0, PAGE_W, final_height))

    img.save(output_path, "PNG", dpi=(150, 150))
    if title:
        print(f"  Created: {output_path}  ({title})")


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    output_dir = repo_root / "data" / "test_contracts"

    contracts = [
        (PAIR1_ORIGINAL,  output_dir / "pair1_original.png",  "Pair 1 — Service Agreement (original)"),
        (PAIR1_AMENDMENT, output_dir / "pair1_amendment.png", "Pair 1 — Service Agreement (amendment)"),
        (PAIR2_ORIGINAL,  output_dir / "pair2_original.png",  "Pair 2 — NDA (original)"),
        (PAIR2_AMENDMENT, output_dir / "pair2_amendment.png", "Pair 2 — NDA (amendment)"),
    ]

    print("Generating test contract images...")
    for text, path, title in contracts:
        render_contract_image(text, path, title)

    print("\nDone. 4 test images created in data/test_contracts/")
    print("\nUsage example:")
    print("  python src/main.py data/test_contracts/pair1_original.png "
          "data/test_contracts/pair1_amendment.png")


if __name__ == "__main__":
    main()
