# Milestone 2.2 — Output legal granular

**Proyecto:** LegalMove Pro  
**Estado:** Cerrado  
**Fecha:** Mayo 2026  
**Depende de:** [Milestone 2.1 — AI Worker Integration](./milestone-2.1-ai-worker-integration.md)

---

## 1. Objetivo del milestone

Rediseñar la salida del `ExtractionAgent` para emitir **cambios legales granulares, trazables y auditables** directamente desde el LLM (schema **v2.2**), en lugar del resumen por secciones del Milestone 2.1.

Al cerrar 2.2, cada cambio detectado incluye:

- Tipo de cambio y tema legal
- Texto antes/después anclado al documento
- Evidencia emparejada (citas literales, referencias de sección, páginas)
- Nivel de riesgo, confianza y señales de revisión humana
- Warnings explícitos cuando el OCR o la evidencia son insuficientes

El output granular se mapea a `FinalAnalysisReport` v1 para mantener compatibilidad con la API Go existente, enriqueciendo el JSONB con **extension fields** listos para una UI futura.

---

## 2. Qué problema resolvió respecto al Milestone 2.1

En 2.1, el `ExtractionAgent` producía un `ContractChangeOutput` orientado a **secciones y narrativa**:

| Limitación en 2.1 | Resolución en 2.2 |
|-------------------|-------------------|
| Lista de secciones modificadas sin cambios atómicos | Array `changes[]` con un ítem por cambio legal concreto |
| `before_text` / `after_text` siempre `null` en el mapper legacy | Citas literales del original y la enmienda, con validación semántica |
| `change_type` y `risk_level` fijos (`MODIFICATION`, `MEDIUM`) | Valores reales por cambio: `ADDITION`, `DELETION`, `HIGH`, `CRITICAL`, etc. |
| Sin evidencia trazable | Objeto `evidence` con quotes, referencias y páginas |
| Sin señales de confianza ni revisión humana | `confidence`, `requires_human_review`, coerción automática ante warnings |
| Validación limitada al mapper | Pydantic estricto + capa semántica (`granular_validation.py`) + mapper |
| Pipeline de 4 pasos agente + map | 6 pasos: + validación semántica y mapping explícito |
| `validation.status` casi siempre `VALID_WITH_WARNINGS` | Matriz `VALID` / `VALID_WITH_WARNINGS` / `INVALID` con job `FAILED` en casos inválidos |

El contrato HTTP de la API Go **no cambió**; la mejora es de calidad, trazabilidad y preparación para revisión humana asistida.

---

## 3. Arquitectura actualizada del pipeline

```
┌─────────────┐     HTTP      ┌─────────────┐
│   Cliente   │ ────────────► │   Go API    │
│  (curl/CLI) │ ◄──────────── │  :8080      │
└─────────────┘               └──────┬──────┘
                                     │
                                     ▼
                              ┌─────────────┐
                              │ PostgreSQL  │
                              │  jobs, docs │
                              └──────┬──────┘
                                     │ poll + claim
                                     ▼
                              ┌─────────────┐
                              │Python Worker│
                              └──────┬──────┘
                                     │
                                     ▼
                    ┌────────────────────────────────┐
                    │     Contract Analysis Pipeline │
                    └────────────────────────────────┘
                                     │
     ┌───────────────────────────────┼───────────────────────────────┐
     ▼                               ▼                               ▼
  OCR (original)              OCR (amendment)              ContextualizationAgent
  Vision / GPT-4o             Vision / GPT-4o              → StructuralContextMap
     │                               │                               │
     └───────────────────────────────┴───────────────────────────────┘
                                     │
                                     ▼
                          Granular ExtractionAgent
                          → GranularContractChangeOutput v2.2
                                     │
                                     ▼
                          Semantic validation
                          validate_granular_output()
                          normalize_granular_output()
                                     │
                                     ▼
                              Result mapper
                          map_extraction_to_final_report()
                          → FinalAnalysisReport v1
                                     │
                                     ▼
                              ┌─────────────┐
                              │ PostgreSQL  │
                              │ analysis_   │
                              │ results +   │
                              │ detected_   │
                              │ changes     │
                              └─────────────┘
```

**Orquestador:** `apps/worker-ai/src/pipeline/contract_analysis.py`

| Paso | Componente | Salida |
|------|------------|--------|
| 1 | OCR Vision — contrato original | Texto plano del original |
| 2 | OCR Vision — enmienda | Texto plano de la enmienda |
| 3 | `ContextualizationAgent` | `StructuralContextMap` (alineación estructural) |
| 4 | `ExtractionAgent` (granular) | `GranularContractChangeOutput` v2.2 |
| 5 | Validación semántica | Output normalizado con warnings y coerciones |
| 6 | Result mapper | `FinalAnalysisReport` v1 (dict JSON) |

El worker persiste el reporte v1 y marca el job como `COMPLETED`, `VALID_WITH_WARNINGS` o `FAILED` según `validation.status`.

---

## 4. Nuevo schema granular

Definido en [`apps/worker-ai/src/core/extraction_models.py`](../apps/worker-ai/src/core/extraction_models.py). Versión: **`2.2`**.

### `LegalChangeEvidence`

Evidencia emparejada que ancla un cambio al texto fuente.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `original_quote` | `string \| null` | Cita literal del contrato original |
| `amendment_quote` | `string \| null` | Cita literal de la enmienda |
| `original_section_reference` | `string \| null` | Referencia de sección en el original |
| `amendment_section_reference` | `string \| null` | Referencia de sección en la enmienda |
| `original_page` | `int \| null` | Página en el original (≥ 1) |
| `amendment_page` | `int \| null` | Página en la enmienda (≥ 1) |

Helper: `has_textual_evidence()` — verdadero si al menos una cita no está vacía.

### `LegalChange`

Un cambio legal atómico dentro del contrato.

| Campo | Tipo | Valores / notas |
|-------|------|-----------------|
| `change_id` | `string` | Identificador estable (único en el reporte) |
| `change_type` | enum | Ver sección 5 |
| `legal_topic` | `string` | Tema legal o comercial |
| `section_reference` | `string` | Referencia de sección afectada |
| `before_text` | `string \| null` | Texto literal pre-cambio (solo del original) |
| `after_text` | `string \| null` | Texto literal post-cambio (solo de la enmienda) |
| `summary` | `string` | Resumen legible del cambio |
| `risk_level` | enum | `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`, `UNKNOWN` |
| `impact_explanation` | `string` | Efecto comercial u operativo |
| `evidence` | `LegalChangeEvidence` | Evidencia emparejada |
| `confidence` | enum | `LOW`, `MEDIUM`, `HIGH` |
| `requires_human_review` | `boolean` | Revisión humana recomendada u obligatoria |

Helpers: `has_textual_evidence()`, `is_high_risk()`, `needs_review()`.

### `GranularContractChangeOutput`

Contenedor raíz del schema v2.2.

| Campo | Tipo | Default |
|-------|------|---------|
| `schema_version` | `string` | `"2.2"` |
| `executive_summary` | `string` | — (requerido, no vacío) |
| `overall_risk_level` | enum | `UNKNOWN` (derivado de cambios si aplica) |
| `changes` | `LegalChange[]` | `[]` |
| `key_risks` | `string[]` | `[]` |
| `human_review_recommendations` | `string[]` | `[]` |
| `extraction_warnings` | `string[]` | `[]` |

Regla dura: `changes=[]` solo es válido si `extraction_warnings` explica por qué no hay cambios detectables.

---

## 5. Explicación de cada campo clave

### `change_type`

Clasifica la naturaleza del cambio detectado.

| Valor | Significado | Texto esperado |
|-------|-------------|----------------|
| `ADDITION` | Cláusula o texto nuevo en la enmienda | `after_text` o `amendment_quote`; sin `before_text` |
| `DELETION` | Eliminación de texto del original | `before_text` o `original_quote`; sin `after_text` |
| `MODIFICATION` | Cambio sustantivo de redacción u obligación | `before_text` y `after_text` |
| `REPLACEMENT` | Sustitución completa de una cláusula | `before_text` y `after_text` |
| `CLARIFICATION` | Aclaración sin cambio material de obligaciones | `impact_explanation` debe indicar que las obligaciones pueden no cambiar |
| `UNKNOWN` | Tipo indeterminado por ambigüedad o OCR incompleto | No puede tener `confidence=HIGH`; revisión humana obligatoria |

En el mapper v1, `CLARIFICATION` y `UNKNOWN` se normalizan a `MODIFICATION` por compatibilidad con el schema HTTP existente.

### `legal_topic`

Etiqueta del tema afectado (p. ej. *Payment Terms*, *Liability*, *Termination*). Agrupa cambios para la UI y filtros futuros. Debe ser descriptivo y no genérico.

### `before_text`

Fragmento literal del **contrato original** antes del cambio. Solo puede provenir del OCR del original. Si no es visible o legible, debe ser `null` — nunca una paráfrasis disfrazada de cita.

### `after_text`

Fragmento literal de la **enmienda** después del cambio. Mismas reglas que `before_text`, pero anclado al documento de enmienda.

### `evidence`

Objeto `LegalChangeEvidence` que respalda el cambio con citas literales y metadatos de ubicación. Es la base de trazabilidad: permite a un revisor humano verificar el output contra el documento fuente.

### `risk_level`

Evaluación del riesgo comercial/legal del cambio individual.

| Valor | Uso típico |
|-------|------------|
| `LOW` | Cambio menor, cosmético o de bajo impacto operativo |
| `MEDIUM` | Cambio relevante que merece revisión pero no es crítico |
| `HIGH` | Impacto significativo en obligaciones, plazos o responsabilidad |
| `CRITICAL` | Riesgo severo; requiere `impact_explanation` no vacío |
| `UNKNOWN` | No se puede evaluar con la evidencia disponible |

`HIGH`, `CRITICAL` y `UNKNOWN` activan `requires_human_review=true` automáticamente.

### `impact_explanation`

Descripción del efecto práctico del cambio (flujo de caja, responsabilidad, plazos, etc.). Obligatorio cuando `risk_level` es `HIGH` o `CRITICAL`. En `CLARIFICATION`, debe dejar claro si las obligaciones permanecen iguales.

### `confidence`

Confianza del modelo en la exactitud del cambio extraído.

| Valor | Cuándo aplica |
|-------|---------------|
| `HIGH` | Evidencia textual completa y coherente con el tipo de cambio |
| `MEDIUM` | Evidencia parcial pero razonable |
| `LOW` | OCR incompleto, evidencia faltante, warnings semánticos o tipo `UNKNOWN` |

La validación semántica **degrada automáticamente** a `LOW` ante cualquier warning estructural.

### `requires_human_review`

Bandera booleana que indica si un profesional debe verificar el cambio antes de confiar en el reporte. Se fuerza a `true` cuando:

- `confidence=LOW`
- `risk_level` es `HIGH`, `CRITICAL` o `UNKNOWN`
- Hay warnings semánticos en el cambio
- El agente lo marca explícitamente

---

## 6. Reglas anti-alucinación

Las reglas operan en **tres capas**: prompts del agente, validación Pydantic y validación semántica post-LLM.

### Reglas no negociables (prompt del ExtractionAgent)

Implementadas en [`apps/worker-ai/src/agents/extraction_agent.py`](../apps/worker-ai/src/agents/extraction_agent.py):

1. **No inventar texto** — usar únicamente el contenido provisto por OCR y context map; no inferir cláusulas, montos, fechas ni partes ausentes.
2. **Evidencia obligatoria cuando sea posible** — `before_text`/`after_text` y `evidence.*_quote` deben ser copias literales; `null` cuando no estén disponibles.
3. **`confidence=LOW` si falta evidencia** — OCR truncado, secciones no comparables o quotes ausentes degradan la confianza.
4. **Revisión humana obligatoria en riesgo alto o baja confianza** — `HIGH`/`CRITICAL`/`UNKNOWN` o `confidence=LOW` → `requires_human_review=true`.
5. **Un cambio atómico por ítem** — no agrupar múltiples modificaciones independientes en un solo `changes[]`.
6. **Conflictos mapa vs texto** — si el `StructuralContextMap` contradice el OCR visible, registrar el conflicto en `extraction_warnings` y reducir confianza.

### Validación semántica (runtime)

Implementada en [`apps/worker-ai/src/core/granular_validation.py`](../apps/worker-ai/src/core/granular_validation.py):

- Verifica coherencia entre `change_type` y presencia de `before_text`/`after_text`.
- Emite warning si `before_text`/`after_text` no están anclados en `evidence.original_quote`/`evidence.amendment_quote`.
- Cualquier warning → coerción a `confidence=LOW` + `requires_human_review=true`.
- Input inválido (campos requeridos vacíos, enums incorrectos, `changes=[]` sin explicación) → `ValidationError` → reporte `INVALID` → job `FAILED`.

**Limitación explícita:** no hay verificación runtime de substrings contra el texto OCR crudo; la grounding check opera entre campos del mismo output estructurado.

---

## 7. Cómo se mapea a FinalAnalysisReport v1

Implementado en [`apps/worker-ai/src/pipeline/result_mapper.py`](../apps/worker-ai/src/pipeline/result_mapper.py). Función de entrada: `map_extraction_to_final_report()`.

**Detección de path granular:** `schema_version` empieza con `"2."` o el payload contiene `changes[]` sin `sections_changed`.

| Campo granular | Destino en v1 |
|----------------|---------------|
| `executive_summary` | `analysis_summary.executive_summary` |
| `overall_risk_level` | `analysis_summary.overall_risk_level` (`CRITICAL→HIGH`, `UNKNOWN→MEDIUM`) |
| `changes[]` | `changes[]` (`CRITICAL→HIGH`; tipos no soportados en v1 → `MODIFICATION`) |
| `key_risks[]` | `risks[]` |
| `human_review_recommendations` | Merge con recomendaciones por defecto del sistema |
| `extraction_warnings` | `validation.warnings` |
| `impact_explanation` | Anexado a `summary` si no está incluido; también como extension field |
| `evidence`, `confidence` | Extension fields en cada ítem de `changes[]` |

### Extension fields (post-`model_dump()`)

Campos adicionales inyectados en el JSON persistido, no presentes en el schema Pydantic v1 de la API:

| Campo | Origen |
|-------|--------|
| `impact_explanation` | `LegalChange.impact_explanation` |
| `confidence` | `LegalChange.confidence` |
| `evidence` | `LegalChange.evidence` serializado |

La API Go ignora keys desconocidas en deserialización; una UI futura puede leerlos directamente del JSONB.

### Matriz `validation.status`

| Condición | `validation.status` | Job status |
|-----------|---------------------|------------|
| Input no reconocible o Pydantic inválido | `INVALID` | `FAILED` |
| `executive_summary` vacío (granular) | `INVALID` | `FAILED` |
| Warnings, evidencia parcial, IDs duplicados, path legacy | `VALID_WITH_WARNINGS` | `VALID_WITH_WARNINGS` |
| Granular limpio, sin warnings | `VALID` | `COMPLETED` |

El path legacy (`ContractChangeOutput` de 2.1) sigue soportado y siempre produce `VALID_WITH_WARNINGS`.

---

## 8. Cómo se persiste en `analysis_results` y `detected_changes`

### `analysis_results` — source of truth

Tabla creada en migración `000001`. El worker inserta el reporte v1 completo en `result_json` (JSONB), junto con `schema_version` y `validation_status`.

- Endpoint de lectura: `GET /analyses/{id}/result`
- Los extension fields (`impact_explanation`, `confidence`, `evidence`) viven en `result_json.changes[]`
- Es la fuente autoritativa para UI y auditoría

### `detected_changes` — denormalización relacional

Tabla base en `000001`; migración adicional en [`000002_detected_changes_granular.up.sql`](../apps/api-go/migrations/000002_detected_changes_granular.up.sql) añade:

```sql
ALTER TABLE detected_changes
    ADD COLUMN impact_explanation TEXT,
    ADD COLUMN confidence TEXT,
    ADD COLUMN evidence JSONB;
```

**Flujo de escritura** ([`apps/worker-ai/src/db.py`](../apps/worker-ai/src/db.py)):

1. `INSERT` en `analysis_results` con el JSON completo.
2. `DELETE` de filas previas del job en `detected_changes` (idempotencia).
3. `INSERT` de una fila por cada ítem en `changes[]`, mapeando columnas v1 + extension fields.
4. `UPDATE` de `analysis_jobs.status` → `COMPLETED` o `VALID_WITH_WARNINGS`.

Valores `NULL` en columnas de extensión para resultados mock, legacy o campos vacíos. La API Go **no expone** `detected_changes` en 2.2; la tabla prepara listados y filtros futuros.

---

## 9. Cómo ejecutar localmente

Prerrequisitos: Docker, Go 1.25+, Python 3.12+, `OPENAI_API_KEY`, imágenes de contrato (`.png`, `.jpg`, `.jpeg`, `.webp`, `.gif`).

### 9.1 PostgreSQL y migraciones

Desde la raíz del repositorio:

```bash
docker compose up -d

docker exec -i legalmove-postgres psql -U legalmove -d legalmove \
  < apps/api-go/migrations/000001_init.up.sql

docker exec -i legalmove-postgres psql -U legalmove -d legalmove \
  < apps/api-go/migrations/000002_detected_changes_granular.up.sql
```

> **Importante:** aplicar **ambas** migraciones. Sin `000002`, los INSERT con columnas de extensión en `detected_changes` fallarán en runtime.

### 9.2 API Go

```bash
cp .env.example .env
# DATABASE_URL, UPLOADS_DIR, API_PORT

cd apps/api-go
go run ./cmd/server
```

### 9.3 Worker AI (pipeline real)

```bash
cd apps/worker-ai
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# OPENAI_API_KEY obligatoria; WORKER_USE_MOCK_RESULT=false

export UPLOADS_DIR=../api-go/uploads
PYTHONPATH=src python src/main.py
```

API y worker deben compartir el mismo `UPLOADS_DIR` físico.

### 9.4 Prueba end-to-end con curl

```bash
ORIGINAL=$(curl -s -X POST http://localhost:8080/documents \
  -F "document_role=ORIGINAL" \
  -F "file=@/ruta/contrato-original.png" | jq -r '.id')

AMENDMENT=$(curl -s -X POST http://localhost:8080/documents \
  -F "document_role=AMENDMENT" \
  -F "file=@/ruta/enmienda.png" | jq -r '.id')

JOB=$(curl -s -X POST http://localhost:8080/analyses \
  -H "Content-Type: application/json" \
  -d "{\"original_document_id\":\"$ORIGINAL\",\"amendment_document_id\":\"$AMENDMENT\"}" \
  | jq -r '.id')

curl -s "http://localhost:8080/analyses/$JOB" | jq '.status, .error_message'
curl -s "http://localhost:8080/analyses/$JOB/result" | jq
```

Estados esperados: `QUEUED` → `PROCESSING` → `COMPLETED` o `VALID_WITH_WARNINGS` (o `FAILED` con `error_message`).

Variables de entorno completas: ver sección 6 de [Milestone 2.1](./milestone-2.1-ai-worker-integration.md).

---

## 10. Cómo probar el pipeline aislado

Sin PostgreSQL ni worker — útil para iterar prompts, OCR y validación.

Desde `apps/worker-ai` con venv activo y `OPENAI_API_KEY` en `.env`:

```bash
# Imprimir reporte v1 a stdout
PYTHONPATH=src python -m pipeline \
  --original-file-path /ruta/contrato.png \
  --amendment-file-path /ruta/enmienda.png \
  --analysis-job-id local-test-001

# Guardar en outputs/local-test-001.result.json
PYTHONPATH=src python -m pipeline \
  --original-file-path /ruta/contrato.png \
  --amendment-file-path /ruta/enmienda.png \
  --analysis-job-id local-test-001 \
  --save
```

Alternativa: `apps/worker-ai/scripts/run_pipeline_once.py`.

El CLI ejecuta los 6 pasos completos (OCR → agentes → validación semántica → mapper) y devuelve un `FinalAnalysisReport` v1 listo para inspección.

---

## 11. Cómo ejecutar tests

```bash
cd apps/worker-ai
.venv/bin/pytest
```

**98 tests** cubren:

| Área | Archivos principales |
|------|---------------------|
| Schema Pydantic v2.2 | `test_extraction_models.py` |
| Validación semántica | `test_granular_validation.py` |
| Mapper y extension fields | `test_result_mapper.py` |
| Prompts anti-alucinación | `test_extraction_agent_prompt.py` |
| Pipeline granular (mocked) | `test_contract_analysis_granular.py` |
| Integración mapper → DB | `test_extraction_mapper_integration.py` |
| Persistencia y rollback | `test_db_save_success.py` |
| INVALID → FAILED | `test_worker_failure.py` |

Ejecutar un subconjunto:

```bash
.venv/bin/pytest tests/test_granular_validation.py -v
.venv/bin/pytest tests/test_result_mapper.py -k "granular" -v
```

---

## 12. Limitaciones restantes

| Limitación | Impacto |
|------------|---------|
| **Sin UI** | El reporte solo es accesible vía API/curl; extension fields no tienen interfaz visual |
| **Sin S3/SQS** | Ingesta y cola siguen siendo filesystem + PostgreSQL polling |
| **Risk scoring heurístico / LLM-based** | No hay agente de riesgo dedicado ni modelo entrenado; niveles dependen del LLM |
| **Evidencia depende de OCR** | Calidad de quotes limitada por Vision; texto truncado o `[ILLEGIBLE]` degrada confianza |
| **Sin PDF nativo** | Solo imágenes; PDFs requieren conversión manual previa |
| **Sin revisión humana integrada** | `requires_human_review` es una señal en JSON; no hay workflow de aprobación |
| **Sin verificación OCR runtime** | Grounding check entre campos del output, no contra texto OCR crudo |
| **API no expone `detected_changes`** | Tabla denormalizada preparada pero sin endpoints de listado/filtro |

Modo mock (`WORKER_USE_MOCK_RESULT=true`) sigue operativo para desarrollo sin OpenAI; no emite extension fields.

---

## 13. Próximo milestone recomendado

### Opción A — Milestone 3: Frontend MVP

**Elegir si el objetivo inmediato es:**

- Demostrar valor de producto a usuarios o inversores
- Validar UX de revisión de cambios granulares (`before`/`after`, evidencia, riesgo)
- Aprovechar extension fields ya persistidos en `result_json`
- Cerrar el loop humano: subir documentos → ver reporte → marcar revisión

**Entregables típicos:** SPA con upload, polling de job, vista de cambios con diff visual, badges de riesgo/confianza, disclaimer legal visible.

### Opción B — Milestone 2.3: Document ingestion PDF/S3/SQS

**Elegir si el objetivo inmediato es:**

- Preparar infraestructura de producción antes de la UI
- Soportar PDF nativo y almacenamiento escalable
- Desacoplar worker con cola SQS y uploads S3
- Reducir fricción operativa (sin conversión manual de PDF a imagen)

**Entregables típicos:** pipeline de conversión PDF→imágenes, bucket S3, cola SQS, worker autoscaling-ready.

### Criterio de decisión

| Prioridad | Milestone recomendado |
|-----------|----------------------|
| Validación de producto, demo, portafolio con UX | **Milestone 3 — Frontend MVP** |
| Despliegue cloud, volumen de documentos, PDFs reales | **Milestone 2.3 — Ingestion PDF/S3/SQS** |

Recomendación para el estado actual del repo: **Milestone 3**, porque el backend ya entrega output granular rico en JSONB y la mayor brecha visible para usuarios es la ausencia de interfaz de revisión.

---

## 14. Checklist de aceptación

- [x] `ExtractionAgent` emite `GranularContractChangeOutput` schema v2.2 con structured output
- [x] Modelos `LegalChangeEvidence`, `LegalChange`, `GranularContractChangeOutput` definidos y validados con Pydantic
- [x] Campos granulares: `change_type`, `legal_topic`, `before_text`, `after_text`, `evidence`, `risk_level`, `impact_explanation`, `confidence`, `requires_human_review`
- [x] Prompts con reglas anti-alucinación (no inventar, evidencia literal, degradación de confianza)
- [x] Capa de validación semántica (`granular_validation.py`) con coerciones automáticas
- [x] Pipeline de 6 pasos: OCR × 2 → Contextualization → Extraction → semantic validation → mapper
- [x] Mapper dual: path granular v2.2 + compatibilidad legacy `ContractChangeOutput`
- [x] Extension fields (`impact_explanation`, `confidence`, `evidence`) en `result_json.changes[]`
- [x] Migración `000002` con columnas de extensión en `detected_changes`
- [x] Worker persiste en `analysis_results` + `detected_changes` con rollback transaccional
- [x] Matriz `validation.status` → job status (`VALID`/`VALID_WITH_WARNINGS`/`INVALID`→`FAILED`)
- [x] CLI standalone (`python -m pipeline`) ejecuta pipeline completo sin DB
- [x] 98 tests automatizados pasando
- [x] Contrato HTTP de API Go sin cambios breaking
- [x] Documentación de milestone y disclaimer legal

---

## 15. Disclaimer legal

LegalMove Pro proporciona **asistencia generada por IA para la revisión de contratos y enmiendas**. El output granular — incluyendo citas, niveles de riesgo, confianza y recomendaciones de revisión — es **informativo y de apoyo**, no constituye asesoría legal, opinión jurídica vinculante ni sustituto del criterio de un abogado u otro profesional legal calificado.

El usuario es responsable de verificar todo cambio detectado contra los documentos originales antes de tomar decisiones comerciales, contractuales o legales. Los campos `requires_human_review`, `confidence=LOW` y `extraction_warnings` existen precisamente para señalar cuándo la evidencia es insuficiente o el OCR puede haber omitido contenido relevante.

LegalMove Pro no garantiza exhaustividad, exactitud ni ausencia de errores en la extracción automatizada.
