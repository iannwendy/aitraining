"""
FastAPI Backend — Mental Health AI Platform
Vietnamese Depression Detection via PhoBERT + BERTopic

Endpoints:
  GET  /api/health              — health check
  GET  /api/dashboard/stats     — dataset counts + best model metrics
  POST /api/predict             — single text prediction
  POST /api/predict/batch      — batch text prediction
  GET  /api/topics              — top BERTopic topics
  GET  /api/models/comparison  — all model metrics (incl. DAPT)
  GET  /api/statistics          — confusion matrix + class distribution
  GET  /api/history             — paginated prediction history
  POST /api/history             — save a prediction (auto on /predict)
  DELETE /api/history/{id}      — delete a history entry
  GET  /api/models/refresh/status — registry reload status
  POST /api/models/refresh       — trigger hot-reload of metrics + models
"""

from __future__ import annotations

import logging
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

# Fix import paths for Docker: /app/main.py needs /app in PYTHONPATH
_backend_dir = Path(__file__).resolve().parent  # /app/
sys.path.insert(0, str(_backend_dir))  # add /app so 'from inference...' works

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pydantic import Field

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ── App ────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Mental Health AI API",
    description="Vietnamese Depression Detection — PhoBERT + BERTopic",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Pydantic schemas ───────────────────────────────────────────────────────────

class PredictionRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)

class PredictionResponse(BaseModel):
    id: str
    text: str
    prediction: str  # "depression" | "normal"
    confidence: float
    topic: Optional[str] = None
    riskLevel: str  # "low" | "medium" | "high"
    highlightedKeywords: Optional[list[str]] = None
    explanation: Optional[str] = None
    modelName: str

class BatchPredictionRequest(BaseModel):
    comments: list[str] = Field(..., max_length=500)

class BatchPredictionResponse(BaseModel):
    results: list[PredictionResponse]
    total: int
    depression_count: int
    normal_count: int

class TopicResponse(BaseModel):
    id: int
    name: str
    keywords: list[str]
    count: int
    percentage: float
    examples: list[str]

class ModelMetricEntry(BaseModel):
    name: str
    accuracy: float
    macroF1: float
    weightedF1: float
    precision: Optional[float]
    recall: Optional[float]
    in_domain_f1: float
    cross_domain_f1: float
    std_in: Optional[float] = None
    std_cross: Optional[float] = None
    model_type: str  # "baseline" | "bilstm" | "phobert" | "bertopic" | "hybrid"
    note: Optional[str] = None

class DashboardStatsResponse(BaseModel):
    totalComments: int
    totalPredictions: int
    goldLabels: int
    currentModel: str
    bestCrossDomain: str
    trainingDate: str
    round: str
    metrics: dict

class StatisticsResponse(BaseModel):
    confusion_matrix: list[list[int]]
    class_distribution: dict  # {"depression": int, "normal": int}
    dataset_breakdown: dict  # {"gold": int, "pseudo": int}
    prediction_stats: dict  # from DB aggregates

class HistoryEntry(BaseModel):
    id: str
    text: str
    prediction: str
    confidence: float
    topic: Optional[str] = None
    risk_level: str
    model_name: Optional[str] = None
    created_at: str

class HistoryListResponse(BaseModel):
    items: list[HistoryEntry]
    total: int
    limit: int
    offset: int

class RefreshStatusResponse(BaseModel):
    status: str  # "idle" | "loading" | "error"
    last_refresh: Optional[str]
    round: Optional[str]

# ── Startup ───────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup_event():
    logger.info("=" * 60)
    logger.info("Starting Mental Health AI Backend v2.0.0")
    logger.info("=" * 60)

    # Init database
    try:
        import database
        database.init_db()
        logger.info("Database ready")
    except Exception as e:
        logger.warning("Database init failed: %s", e)

    # Init default registry (creates it if missing)
    try:
        from inference.registry import init_default_registry, ResultsRegistry
        init_default_registry()
        ResultsRegistry.get()
        logger.info("Results registry ready")
    except Exception as e:
        logger.warning("Registry init failed: %s", e)

    # Pre-warm the PhoBERT engine (load model on startup)
    try:
        from inference.phobert_engine import get_engine
        engine = get_engine()
        logger.info("PhoBERT engine warmed up on device: %s", engine.device)
    except Exception as e:
        logger.warning("PhoBERT engine warmup failed: %s", e)

    logger.info("Startup complete")


# ── Health ───────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "name": "Mental Health AI API",
        "version": "2.0.0",
        "models": ["PhoBERT + BERTopic", "TF-IDF + LogReg", "BiLSTM"],
    }


@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
    }


# ── Dashboard Stats ────────────────────────────────────────────────────────────

@app.get("/api/dashboard/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats():
    from inference.metrics_loader import load_dashboard_stats
    try:
        stats = load_dashboard_stats()
        return DashboardStatsResponse(**stats)
    except Exception as e:
        logger.error("Dashboard stats failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ── Prediction ────────────────────────────────────────────────────────────────

@app.post("/api/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    try:
        from inference.phobert_engine import get_engine
        from inference.bertopic_engine import get_engine as get_topic_engine

        # Run PhoBERT inference
        phobert = get_engine()
        pred_result = phobert.predict_single(request.text)

        # Get BERTopic topic (lightweight)
        topic_info = None
        try:
            topic_engine = get_topic_engine()
            topic_info = topic_engine.predict_topic(request.text)
        except Exception:
            pass  # BERTopic is optional

        prediction = pred_result["prediction"]
        confidence = pred_result["confidence"]
        risk_level = pred_result["risk_level"]
        model_name = "PhoBERT (Round 5)"

        # Auto-save to history
        try:
            import database
            database.save_prediction(
                text=request.text,
                prediction=prediction,
                confidence=confidence,
                prob_normal=pred_result.get("prob_normal", 0),
                prob_depression=pred_result.get("prob_depression", confidence),
                topic_id=topic_info.get("topic_id") if topic_info else None,
                topic_name=topic_info.get("topic_name") if topic_info else None,
                risk_level=risk_level,
                model_name=model_name,
            )
        except Exception as e:
            logger.warning("Failed to save to history: %s", e)

        # Build explanation
        explanation = _build_explanation(prediction, confidence, topic_info)

        return PredictionResponse(
            id=str(uuid.uuid4()),
            text=request.text,
            prediction=prediction,
            confidence=confidence,
            topic=topic_info.get("topic_name") if topic_info else None,
            riskLevel=risk_level,
            explanation=explanation,
            modelName=model_name,
        )
    except Exception as e:
        logger.error("Prediction failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


def _build_explanation(prediction: str, confidence: float, topic_info: Optional[dict]) -> str:
    if prediction == "normal":
        return "Văn bản không chứa các chỉ báo rõ ràng về trầm cảm."

    topic_name = topic_info.get("topic_name") if topic_info else None
    if topic_name:
        return f"Mô hình nhận diện các cụm từ liên quan đến chủ đề '{topic_name}' với độ tin cậy {confidence:.0%}."
    return f"Mô hình nhận diện văn bản này có dấu hiệu trầm cảm (confidence: {confidence:.0%})."


# ── Batch Prediction ──────────────────────────────────────────────────────────

@app.post("/api/predict/batch", response_model=BatchPredictionResponse)
async def batch_predict(request: BatchPredictionRequest):
    if not request.comments:
        return BatchPredictionResponse(results=[], total=0, depression_count=0, normal_count=0)

    try:
        from inference.phobert_engine import get_engine
        from inference.bertopic_engine import get_engine as get_topic_engine

        phobert = get_engine()
        pred_results = phobert.predict_batch(request.comments)

        # Get topics in batch
        topic_engine = None
        try:
            topic_engine = get_topic_engine()
            topic_results = topic_engine.predict_topics(request.comments)
            topic_map = {i: topic_results[i] for i in range(len(topic_results))}
        except Exception:
            topic_map = {}

        results = []
        depression_count = 0
        normal_count = 0

        for i, (text, pred_result) in enumerate(zip(request.comments, pred_results)):
            pred = pred_result["prediction"]
            conf = pred_result["confidence"]
            risk = pred_result["risk_level"]
            topic_info = topic_map.get(i)

            if pred == "depression":
                depression_count += 1
            else:
                normal_count += 1

            results.append(PredictionResponse(
                id=str(uuid.uuid4()),
                text=text,
                prediction=pred,
                confidence=conf,
                topic=topic_info.get("topic_name") if topic_info else None,
                riskLevel=risk,
                modelName="PhoBERT (Round 5)",
            ))

        return BatchPredictionResponse(
            results=results,
            total=len(results),
            depression_count=depression_count,
            normal_count=normal_count,
        )
    except Exception as e:
        logger.error("Batch prediction failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ── Topics ────────────────────────────────────────────────────────────────────

@app.get("/api/topics", response_model=list[TopicResponse])
async def get_topics(limit: int = Query(default=20, ge=1, le=50)):
    try:
        from inference.bertopic_engine import get_engine
        engine = get_engine()
        topics = engine.get_top_topics(limit=limit)
        return [TopicResponse(
            id=t["id"],
            name=t["name"],
            keywords=t["keywords"],
            count=t["count"],
            percentage=t["percentage"],
            examples=t.get("examples", []),
        ) for t in topics]
    except Exception as e:
        logger.error("Topics endpoint failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ── Model Comparison ──────────────────────────────────────────────────────────

@app.get("/api/models/comparison")
async def get_model_comparison():
    try:
        from inference.metrics_loader import load_all_metrics

        metrics = load_all_metrics()

        # Normalize to API format
        models = []
        for m in metrics:
            models.append(ModelMetricEntry(
                name=m.get("name", ""),
                accuracy=m.get("accuracy", 0),
                macroF1=m.get("in_domain_f1", 0),
                weightedF1=m.get("in_domain_f1", 0),
                precision=m.get("precision"),
                recall=m.get("recall"),
                in_domain_f1=m.get("in_domain_f1", 0),
                cross_domain_f1=m.get("cross_domain_f1", 0),
                std_in=m.get("std_in"),
                std_cross=m.get("std_cross"),
                model_type=m.get("type", "unknown"),
                note=m.get("note"),
            ))

        # Sort: baseline → bilstm → phobert → hybrid → bertopic
        type_order = {"baseline": 0, "bilstm": 1, "phobert": 2, "hybrid": 3, "bertopic": 4}
        models.sort(key=lambda m: type_order.get(m.model_type, 9))

        return {"models": [m.model_dump() for m in models]}
    except Exception as e:
        logger.error("Model comparison failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ── Statistics ────────────────────────────────────────────────────────────────

@app.get("/api/statistics", response_model=StatisticsResponse)
async def get_statistics():
    try:
        import pandas as pd
        from pathlib import Path

        # Load confusion matrix from metrics
        confusion = [[0, 0], [0, 0]]
        try:
            from inference.metrics_loader import load_all_metrics
            metrics = load_all_metrics()
            for m in metrics:
                if m.get("name") == "PhoBERT + DAPT":
                    confusion = m.get("confusion_matrix", [[0, 0], [0, 0]])
                    break
            if not confusion or confusion == [[0, 0], [0, 0]]:
                for m in metrics:
                    cm = m.get("confusion_matrix")
                    if cm and cm != [[0, 0], [0, 0]]:
                        confusion = cm
                        break
        except Exception:
            pass

        # Class distribution from final_dataset
        class_dist = {"depression": 0, "normal": 0}
        dataset_breakdown = {"gold": 0, "pseudo": 0}
        try:
            data_dir = Path(__file__).resolve().parents[1].parent / "data"
            final_csv = data_dir / "final_dataset.csv"
            if final_csv.exists():
                df = pd.read_csv(final_csv, dtype=str).fillna("")
                df["label"] = pd.to_numeric(df["label"], errors="coerce").fillna(0).astype(int)
                class_dist["depression"] = int((df["label"] == 1).sum())
                class_dist["normal"] = int((df["label"] == 0).sum())

                if "source" in df.columns:
                    dataset_breakdown["gold"] = int((df["source"] == "human_gold").sum())
                    dataset_breakdown["pseudo"] = int((df["source"] != "human_gold").sum())
                else:
                    dataset_breakdown["gold"] = len(df)
                    dataset_breakdown["pseudo"] = 0
        except Exception:
            pass

        # Prediction stats from DB
        pred_stats = {"total": 0, "depression_count": 0, "normal_count": 0, "avg_confidence": 0, "unique_topics": 0}
        try:
            import database
            pred_stats = database.get_prediction_stats()
        except Exception:
            pass

        return StatisticsResponse(
            confusion_matrix=confusion,
            class_distribution=class_dist,
            dataset_breakdown=dataset_breakdown,
            prediction_stats=pred_stats,
        )
    except Exception as e:
        logger.error("Statistics endpoint failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ── History ────────────────────────────────────────────────────────────────────

@app.get("/api/history", response_model=HistoryListResponse)
async def get_history(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    try:
        import database
        items = database.get_history(limit=limit, offset=offset)
        total = database.get_history_count()
        return HistoryListResponse(
            items=[
                HistoryEntry(
                    id=item["id"],
                    text=item["text"],
                    prediction=item["prediction"],
                    confidence=item["confidence"],
                    topic=item.get("topic_name"),
                    risk_level=item["risk_level"],
                    model_name=item.get("model_name"),
                    created_at=item["created_at"],
                )
                for item in items
            ],
            total=total,
            limit=limit,
            offset=offset,
        )
    except Exception as e:
        logger.error("History endpoint failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/history")
async def save_history_entry(request: PredictionRequest):
    """Manually save a prediction to history (alternative to auto-save on /predict)."""
    try:
        import database
        from inference.phobert_engine import get_engine
        from inference.bertopic_engine import get_engine as get_topic_engine

        phobert = get_engine()
        result = phobert.predict_single(request.text)

        topic_info = None
        try:
            topic_engine = get_topic_engine()
            topic_info = topic_engine.predict_topic(request.text)
        except Exception:
            pass

        saved = database.save_prediction(
            text=request.text,
            prediction=result["prediction"],
            confidence=result["confidence"],
            prob_normal=result.get("prob_normal", 0),
            prob_depression=result.get("prob_depression", result["confidence"]),
            topic_id=topic_info.get("topic_id") if topic_info else None,
            topic_name=topic_info.get("topic_name") if topic_info else None,
            risk_level=result["risk_level"],
            model_name="PhoBERT (Round 5)",
        )
        return {"id": saved["id"], "status": "saved"}
    except Exception as e:
        logger.error("Save history failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/history/{id}")
async def delete_history_entry(id: str):
    try:
        import database
        deleted = database.delete_prediction(id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Prediction not found")
        return {"status": "deleted", "id": id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Delete history failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ── Model Refresh (Hot-reload) ────────────────────────────────────────────────

@app.get("/api/models/refresh/status", response_model=RefreshStatusResponse)
async def refresh_status():
    try:
        from inference.registry import ResultsRegistry
        status = ResultsRegistry.get().get_status()
        return RefreshStatusResponse(**status)
    except Exception as e:
        logger.error("Refresh status failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/models/refresh")
async def refresh_models():
    """Hot-reload the results registry and optionally PhoBERT model."""
    try:
        from inference.registry import ResultsRegistry
        from inference.phobert_engine import PhoBertEngine

        # Reload registry
        reg = ResultsRegistry.get()
        reg.load()

        # Reload PhoBERT if model path changed
        try:
            PhoBertEngine.get_instance().reload()
        except Exception as e:
            logger.warning("PhoBERT reload skipped: %s", e)

        return reg.refresh()
    except Exception as e:
        logger.error("Refresh failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ── Run ────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
