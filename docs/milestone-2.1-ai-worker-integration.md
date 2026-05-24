# Milestone 2.1 — Integración del pipeline AI en el Worker Python

**Proyecto:** LegalMove Pro  
**Estado:** Cerrado  
**Fecha:** Mayo 2026

---

## 1. Objetivo del milestone

Conectar el **pipeline de análisis de contratos con IA real** al worker Python existente, reemplazando el resultado mock del Milestone 1.

Al cerrar 2.1, el flujo end-to-end queda operativo en local:

1. Subir contrato original y enmienda vía API Go.
2. Crear un job de análisis en PostgreSQL (`QUEUED`).
3. El worker reclama el job, ejecuta OCR + agentes OpenAI y persiste un `FinalAnalysisReport` v1.
4. La API expone el resultado estructurado para revisión humana.

El objetivo de producto no cambia: **asistencia generada por IA para comparar un contrato original contra una enmienda**, con disclaimer explícito de que no constituye asesoría legal.

---

## 2. Arquitectura actualizada

```
┌─────────────┐     HTTP      ┌─────────────┐
│   Cliente   │ ────────────► │   Go API    │
│  (curl/CLI) │ ◄──────────── │  :8080      │
└─────────────┘               └──────┬──────┘
                                     │ read/write
                                     ▼
                              ┌─────────────┐
                              │ PostgreSQL  │
                              │  jobs, docs │
                              │  results    │
                              └──────┬──────┘
                                     │ poll + claim (SKIP LOCKED)
                                     ▼
                              ┌─────────────┐
                              │Python Worker│
                              │  (main.py)  │
                              └──────┬──────┘
                                     │
                                     ▼
                              ┌─────────────┐
                              │ AI Pipeline │
                              │ Vision +    │
                              │ 2 agentes   │
                              └──────┬──────┘
                                     │ FinalAnalysisReport v1
                                     ▼
                              ┌─────────────┐
                              │ PostgreSQL  │
                              │ analysis_   │
                              │ results +   │
                              │ detected_   │
                              │ changes     │
                              └─────────────┘

Almacenamiento local de imágenes: filesystem (`UPLOADS_DIR`)
Observabilidad opcional: Langfuse (traces por job)
```

**Cadena de datos:** Go API → PostgreSQL → Python Worker → AI Pipeline → PostgreSQL.

La API Go no invoca al worker directamente. La coordinación es **por base de datos**: jobs en cola, worker con polling periódico.

---

## 3. Qué cambió respecto al Milestone 1

| Aspecto | Milestone 1 | Milestone 2.1 |
|---------|-------------|---------------|
| Resultado del worker | JSON mock fijo (`WORKER_USE_MOCK_RESULT=true` o hardcoded) | Pipeline real con OpenAI (Vision + agentes) |
| Procesamiento de documentos | Metadatos en DB; sin lectura de contenido | OCR multimodal (GPT-4o Vision) sobre imágenes |
| Lógica de análisis | Placeholder estático | ContextualizationAgent + ExtractionAgent |
| Schema de salida | `FinalAnalysisReport` v1 definido | Mapeo desde `ContractChangeOutput` → report v1 |
| Errores | Genéricos | Dominio tipado (`PipelineError`, `DocumentLoadError`, etc.) |
| Observabilidad | Ninguna | Langfuse opcional por step del pipeline |
| CLI aislado | No existía | `python -m pipeline` sin DB ni worker |
| Tests | Básicos de worker/DB | + mapper, errores, CLI, paths, save con cambios |

Lo que **no cambió** en 2.1: esquema PostgreSQL, contratos HTTP de la API Go, almacenamiento en filesystem local, ausencia de frontend, S3 y SQS.

---

## 4. Nuevos módulos del worker

Estructura bajo `apps/worker-ai/src/`:

### `pipeline/` — Orquestación e integración

| Módulo | Responsabilidad |
|--------|-----------------|
| `contract_analysis.py` | Orquestador principal: valida archivos, ejecuta OCR, agentes, mapping y trace Langfuse |
| `result_mapper.py` | Transforma `ContractChangeOutput` → `FinalAnalysisReport` v1 (función pura) |
| `cli.py` | CLI standalone para probar el pipeline sin PostgreSQL |
| `errors.py` | Excepciones de dominio y mensajes seguros para `analysis_jobs.error_message` |
| `observability.py` | Wrappers no bloqueantes para Langfuse (trace, generation, usage) |
| `path_resolver.py` | Resuelve `storage_path` de documentos contra `UPLOADS_DIR` |

### `agents/` — Agentes LLM

| Módulo | Responsabilidad |
|--------|-----------------|
| `contextualization_agent.py` | Agent 1: alinea estructura original vs enmienda → `StructuralContextMap` |
| `extraction_agent.py` | Agent 2: extrae cambios sustantivos → `ContractChangeOutput` |

### `core/` — Modelos y utilidades

| Módulo | Responsabilidad |
|--------|-----------------|
| `models.py` | Schemas intermedios del pipeline (`StructuralContextMap`, `ContractChangeOutput`) |
| `report_models.py` | Schema Pydantic de `FinalAnalysisReport` v1 |
| `image_parser.py` | Validación de imagen + OCR con GPT-4o Vision |
| `validation_utils.py` | Helpers de validación de structured outputs |

### `infra/` — Integraciones externas

| Módulo | Responsabilidad |
|--------|-----------------|
| `http_config.py` | Timeouts, retries y límites de imagen desde env |
| `openai_errors.py` | Normalización de errores OpenAI (rate limit, context length) |
| `langfuse_model.py` | Normalización de nombres de modelo para traces |

### Módulos existentes actualizados

- `worker.py` — Invoca `run_contract_analysis()` cuando `WORKER_USE_MOCK_RESULT=false`
- `db.py` — Persiste `result_json`, normaliza filas en `detected_changes`
- `config.py` — Variables OpenAI, Langfuse y flag mock

---

## 5. Flujo paso a paso

### Flujo end-to-end (API + worker)

1. **Upload original** — `POST /documents` con `document_role=ORIGINAL` e imagen del contrato.
2. **Upload enmienda** — `POST /documents` con `document_role=AMENDMENT`.
3. **Crear análisis** — `POST /analyses` con los UUIDs de ambos documentos. Job creado en `QUEUED`.
4. **Worker reclama job** — `UPDATE ... FOR UPDATE SKIP LOCKED` → status `PROCESSING`.
5. **Resolver paths** — Join en DB + `path_resolver.resolve_document_path()`.
6. **Pipeline AI** (4 pasos internos):
   - **1/4** OCR del contrato original (Vision)
   - **2/4** OCR de la enmienda (Vision)
   - **3/4** ContextualizationAgent → mapa estructural
   - **4/4** ExtractionAgent → lista de secciones/temas/resumen
7. **Mapping** — `map_contract_change_output_to_final_report()` → JSON v1.
8. **Validación** — Si `validation.status == INVALID` → job `FAILED`.
9. **Persistencia** — Insert en `analysis_results`, filas en `detected_changes`, job `COMPLETED` (o `VALID_WITH_WARNINGS` si aplica).
10. **Consulta** — Cliente hace polling con `GET /analyses/{id}` y obtiene payload con `GET /analyses/{id}/result`.

### Flujo de error

- `PipelineError` / documento no encontrado → `FAILED` + `error_message` legible.
- Error inesperado → mensaje genérico en DB; detalle en logs del worker.

---

## 6. Variables de entorno requeridas

Copiar `.env.example` a `.env` en la raíz del monorepo (API y worker leen `../../.env`).

### Worker y base de datos (obligatorias para el worker)

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `DATABASE_URL` | Conexión PostgreSQL | `postgres://legalmove:legalmove@localhost:5432/legalmove?sslmode=disable` |
| `UPLOADS_DIR` | Directorio compartido con la API Go | `./uploads` |
| `WORKER_POLL_INTERVAL_SECONDS` | Intervalo de polling | `5` |
| `WORKER_USE_MOCK_RESULT` | `true` = mock Milestone 1; `false` = pipeline real | `false` |

### API Go (obligatorias)

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `APP_ENV` | Entorno | `local` |
| `API_PORT` | Puerto HTTP | `8080` |
| `DATABASE_URL` | Misma instancia que el worker | (igual que arriba) |
| `UPLOADS_DIR` | **Debe coincidir** con el worker | `./uploads` |

### Pipeline AI (obligatorias cuando `WORKER_USE_MOCK_RESULT=false`)

| Variable | Descripción | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | Clave API OpenAI | — |
| `OPENAI_TIMEOUT` | Timeout HTTP (segundos) | `120` |
| `OPENAI_MAX_RETRIES` | Reintentos OpenAI | `2` |
| `OPENAI_VISION_MODEL` | Modelo OCR | `gpt-4o` |
| `OPENAI_TEXT_MODEL` | Modelo agentes | `gpt-4o` |
| `VISION_MAX_IMAGE_BYTES` | Tamaño máximo de imagen | `20971520` (20 MB) |
| `VISION_MAX_DIMENSION` | Dimensión máxima (px) | `8192` |

### Langfuse (opcionales)

| Variable | Descripción |
|----------|-------------|
| `LANGFUSE_PUBLIC_KEY` | Clave pública |
| `LANGFUSE_SECRET_KEY` | Clave secreta |
| `LANGFUSE_HOST` | Host (default: `https://cloud.langfuse.com`) |

Si las claves Langfuse están vacías, el pipeline corre sin traces.

---

## 7. Cómo ejecutar localmente

### Prerrequisitos

- Docker (PostgreSQL)
- Go 1.25+
- Python 3.12+
- `OPENAI_API_KEY` válida (para pipeline real)
- Imágenes de contrato/enmienda (`.png`, `.jpg`, `.jpeg`, `.webp`, `.gif`)

### 7.1 PostgreSQL

Desde la raíz del repositorio:

```bash
docker compose up -d
```

Aplicar migraciones (primera vez):

```bash
docker exec -i legalmove-postgres psql -U legalmove -d legalmove \
  < apps/api-go/migrations/000001_init.up.sql
```

Verificar:

```bash
docker exec legalmove-postgres pg_isready -U legalmove -d legalmove
```

### 7.2 API Go

```bash
cp .env.example .env
# Editar .env: DATABASE_URL, UPLOADS_DIR, API_PORT

cd apps/api-go
go run ./cmd/server
```

Health check:

```bash
curl -s http://localhost:8080/health | jq
```

### 7.3 Worker AI

```bash
cd apps/worker-ai
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Añadir OPENAI_API_KEY; WORKER_USE_MOCK_RESULT=false

# Desde apps/worker-ai, con UPLOADS_DIR apuntando al mismo dir que la API:
export UPLOADS_DIR=../api-go/uploads

PYTHONPATH=src python src/main.py
```

> **Importante:** API y worker deben compartir el mismo `UPLOADS_DIR` físico. Si la API corre desde `apps/api-go` con `UPLOADS_DIR=./uploads`, el worker debe usar `../api-go/uploads` (ruta absoluta recomendada en producción local).

### 7.4 Prueba con curl

Sustituir rutas por tus imágenes de prueba.

```bash
# 1. Subir contrato original
ORIGINAL=$(curl -s -X POST http://localhost:8080/documents \
  -F "document_role=ORIGINAL" \
  -F "file=@/ruta/al/contrato-original.png" | jq -r '.id')

# 2. Subir enmienda
AMENDMENT=$(curl -s -X POST http://localhost:8080/documents \
  -F "document_role=AMENDMENT" \
  -F "file=@/ruta/a/enmienda.png" | jq -r '.id')

# 3. Crear job de análisis
JOB=$(curl -s -X POST http://localhost:8080/analyses \
  -H "Content-Type: application/json" \
  -d "{\"original_document_id\":\"$ORIGINAL\",\"amendment_document_id\":\"$AMENDMENT\"}" \
  | jq -r '.id')

echo "Job ID: $JOB"

# 4. Polling de estado (el worker tarda según tamaño de imagen y OpenAI)
curl -s "http://localhost:8080/analyses/$JOB" | jq '.status, .error_message'

# 5. Obtener resultado cuando status sea COMPLETED
curl -s "http://localhost:8080/analyses/$JOB/result" | jq
```

Estados esperados del job: `QUEUED` → `PROCESSING` → `COMPLETED` (o `FAILED` con `error_message`).

---

## 8. Cómo probar el pipeline de forma aislada

Sin PostgreSQL ni worker — útil para iterar prompts, OCR y mapping.

Desde `apps/worker-ai` con venv activo y `OPENAI_API_KEY` en `.env`:

```bash
# Imprimir JSON a stdout
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

Alternativa equivalente (añade `src` al path automáticamente):

```bash
python scripts/run_pipeline_once.py \
  --original-file-path /ruta/contrato.png \
  --amendment-file-path /ruta/enmienda.png \
  --save
```

Tests unitarios del worker (sin llamadas OpenAI reales en la mayoría):

```bash
cd apps/worker-ai
pytest
```

---

## 9. Shape del `FinalAnalysisReport` v1

Schema definido en `core/report_models.py`. Ejemplo representativo:

```json
{
  "schema_version": "1.0",
  "disclaimer": "AI-generated review support. Not legal advice.",
  "analysis_summary": {
    "executive_summary": "Narrativa ejecutiva de los cambios detectados.",
    "overall_risk_level": "LOW | MEDIUM | HIGH",
    "total_changes": 2,
    "high_risk_changes": 0,
    "requires_human_review": true
  },
  "changes": [
    {
      "change_id": "chg_001",
      "change_type": "MODIFICATION | ADDITION | DELETION | REPLACEMENT",
      "legal_topic": "Payment Terms",
      "section_reference": "§3 — Payment Terms",
      "before_text": null,
      "after_text": null,
      "summary": "Descripción del cambio en la sección.",
      "risk_level": "LOW | MEDIUM | HIGH",
      "requires_human_review": true
    }
  ],
  "risks": [],
  "human_review_recommendations": [
    "Review all detected changes manually before relying on this report.",
    "This AI-generated output is not legal advice."
  ],
  "validation": {
    "status": "VALID | INVALID | VALID_WITH_WARNINGS",
    "warnings": [
      "The original extraction output does not include textual before/after evidence."
    ]
  }
}
```

**Persistencia:**

- JSON completo → `analysis_results.result_json`
- Cada ítem de `changes[]` → fila en `detected_changes`
- `validation.status` → `analysis_results.validation_status` y status del job

---

## 10. Limitaciones actuales

| Limitación | Detalle |
|------------|---------|
| **Mapping simple** | `result_mapper.py` genera un cambio por sección en `sections_changed`; `change_type` siempre `MODIFICATION`; riesgo fijo `MEDIUM` |
| **Sin risk agent real** | `risks[]` queda vacío; no hay agente dedicado a evaluación de riesgo legal |
| **`before_text` / `after_text` null** | El extractor no devuelve evidencia textual pareada; el mapper las deja en `null` |
| **Evidencia textual limitada** | El resumen narrativo existe, pero no hay citas literales before/after por cambio |
| **Sin S3 / SQS** | Archivos en filesystem local; worker hace polling SQL, no cola de mensajes |
| **Sin frontend** | Solo API REST + worker; no hay UI Next.js integrada en este milestone |
| **Entrada multimodal** | Pipeline espera imágenes escaneadas; no PDF nativo ni DOCX |
| **Langfuse opcional** | Sin claves, no hay trazabilidad centralizada |
| **Mock mode disponible** | `WORKER_USE_MOCK_RESULT=true` permite probar integración DB sin costo OpenAI |

---

## 11. Próximo paso: Milestone 2.2 — Output legal granular

**Completado.** Ver documentación detallada en [milestone-2.2-granular-legal-output.md](./milestone-2.2-granular-legal-output.md).

Resumen de lo implementado:

- Nuevo schema granular (`GranularContractChangeOutput`) con cambios atómicos trazables
- `ExtractionAgent` actualizado para emitir `changes[]` directamente desde el LLM
- Mapper dual: path granular + compatibilidad legacy con `ContractChangeOutput`
- `VALID_WITH_WARNINGS` activo cuando falta evidencia o hay `confidence=LOW`
- Persistencia en `detected_changes` con `change_type`, before/after y `risk_level` reales

---

## 12. Checklist de aceptación

### Integración worker ↔ pipeline

- [x] Worker reclama jobs `QUEUED` con `SKIP LOCKED`
- [x] Worker invoca `run_contract_analysis()` cuando mock está desactivado
- [x] Resultado mock sigue disponible con `WORKER_USE_MOCK_RESULT=true`
- [x] Jobs con `validation.status=INVALID` terminan en `FAILED`
- [x] Jobs exitosos persisten en `analysis_results` y `detected_changes`
- [x] Errores de pipeline se guardan en `analysis_jobs.error_message`

### Pipeline AI

- [x] OCR Vision para original y enmienda
- [x] ContextualizationAgent produce `StructuralContextMap` validado
- [x] ExtractionAgent produce `ContractChangeOutput` validado
- [x] Mapping a `FinalAnalysisReport` v1 con `schema_version=1.0`
- [x] Errores de dominio (`DocumentLoadError`, `AgentExecutionError`, etc.) con mensajes acotados

### Operabilidad

- [x] CLI standalone (`PYTHONPATH=src python -m pipeline`) sin DB
- [x] Variables de entorno documentadas en `.env.example`
- [x] Langfuse integrado de forma no bloqueante (opcional)
- [x] Resolución de paths de documentos vía `UPLOADS_DIR`

### Tests automatizados

- [x] Mapper: secciones → cambios, warnings, schema v1
- [x] Worker: éxito pipeline, fallo pipeline, modo mock, validación INVALID
- [x] DB: save success, detected_changes, paths
- [x] CLI: stdout JSON, `--save`, manejo de errores
- [x] Errores: clasificación OpenAI, documentos, structured output

### API (sin cambios de contrato en 2.1)

- [x] `POST /documents`, `POST /analyses`, `GET /analyses/{id}`, `GET /analyses/{id}/result` operativos
- [x] Flujo curl end-to-end verificable en local con PostgreSQL + API + worker

---

## Referencias en el repositorio

| Recurso | Ruta |
|---------|------|
| Orquestador del pipeline | `apps/worker-ai/src/pipeline/contract_analysis.py` |
| Mapper v1 | `apps/worker-ai/src/pipeline/result_mapper.py` |
| Schema del reporte | `apps/worker-ai/src/core/report_models.py` |
| Worker loop | `apps/worker-ai/src/worker.py`, `apps/worker-ai/src/main.py` |
| Migraciones DB | `apps/api-go/migrations/000001_init.up.sql` |
| MVP overview | `docs/mvp-v0.1.md` |

---

## Disclaimer legal

LegalMove Pro proporciona **soporte de revisión generado por IA**. No sustituye el criterio de un profesional legal calificado. Todo output debe ser revisado por una persona antes de tomar decisiones.
