"""FastAPI application for Intelligent Feed system."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from app.models.response import InsightRequest, InsightResponse, HealthResponse, ErrorResponse
from app.services.orchestrator import IntelligentFeedOrchestrator
from app.utils.sample_business_view import SAMPLE_BUSINESS_VIEW
from app.core.config import settings
from app.core.logging import setup_logging, get_logger


# ==================== Feed Models ====================

class FeedCreate(BaseModel):
    name: str
    bv_name: str
    user_query: str
    schedule_type: str = "with_data_refresh"
    schedule_frequency: str = "daily"
    schedule_time: str = "09:00"
    schedule_from_date: Optional[str] = None  # For custom schedule date range
    schedule_to_date: Optional[str] = None    # For custom schedule date range
    is_active: bool = True


class FeedUpdate(BaseModel):
    name: Optional[str] = None
    bv_name: Optional[str] = None
    user_query: Optional[str] = None
    schedule_type: Optional[str] = None
    schedule_frequency: Optional[str] = None
    schedule_time: Optional[str] = None
    schedule_from_date: Optional[str] = None
    schedule_to_date: Optional[str] = None
    is_active: Optional[bool] = None


class Feed(BaseModel):
    id: str
    name: str
    bv_name: str
    user_query: str
    schedule_type: str
    schedule_frequency: str
    schedule_time: str
    schedule_from_date: Optional[str] = None
    schedule_to_date: Optional[str] = None
    is_active: bool
    last_run: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class QueryValidation(BaseModel):
    query: str
    bv_name: str


class QueryValidationResult(BaseModel):
    is_valid: bool
    can_proceed: bool
    feed_type: Optional[str] = None
    message: Optional[str] = None
    suggestions: List[str] = []


class TriggeredAlert(BaseModel):
    id: str
    feed_id: str
    feed_name: str
    user_query: str
    metric: str
    trigger_reason: str
    severity: str
    confidence: float
    triggered_at: datetime
    results: Dict[str, Any]


# In-memory storage (replace with database in production)
feeds_db: Dict[str, Feed] = {}
triggered_alerts_db: Dict[str, TriggeredAlert] = {}

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Global orchestrator instance
orchestrator: IntelligentFeedOrchestrator = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global orchestrator

    logger.info("application_starting", version=settings.VERSION)

    # Initialize orchestrator
    orchestrator = IntelligentFeedOrchestrator(
        business_view=SAMPLE_BUSINESS_VIEW,
        db_path="sqlite:///./tellius_feed.db",
    )

    logger.info("application_started")

    yield

    # Cleanup
    logger.info("application_shutting_down")
    if orchestrator:
        orchestrator.close()
    logger.info("application_stopped")


# Create FastAPI app
app = FastAPI(
    title="Tellius Intelligent Feed API",
    description="Next-generation question-driven insight engine with deep root-cause analysis",
    version=settings.VERSION,
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "service": "Tellius Intelligent Feed",
        "version": settings.VERSION,
        "status": "running",
        "docs": "/docs",
    }


@app.get("/api/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint.

    Returns system status and component health.
    """
    try:
        # Check database connection
        db_status = "connected"
        try:
            tables = orchestrator.tql_adapter.list_tables()
            if not tables:
                db_status = "empty"
        except:
            db_status = "disconnected"

        # Check LLM connection
        llm_status = "configured" if settings.ANTHROPIC_API_KEY else "not_configured"

        return HealthResponse(
            status="healthy",
            version=settings.VERSION,
            components={
                "database": db_status,
                "llm": llm_status,
                "python_sandbox": "ready",
            },
        )
    except Exception as e:
        logger.error("health_check_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/insight", response_model=InsightResponse, tags=["Insights"])
async def generate_insight(request: InsightRequest):
    """
    Generate deep insight from natural language question.

    This is the main endpoint for the Intelligent Feed system.

    **Flow:**
    1. Parse question into structured intent
    2. Generate and validate SQL/TQL plan
    3. Execute queries against data
    4. Run detection (Absolute or ARIMA)
    5. If triggered: perform deep RCA, generate charts, create narrative
    6. If not triggered: return explanation and suggestion

    **Examples:**
    - "Why did revenue in APAC drop in the last 8 weeks vs previous period?"
    - "Show me anomalies in user signups for Q4 2024"
    - "What caused the sales spike in Enterprise segment last month?"
    """
    try:
        logger.info("api_request_received", question=request.user_question)

        # Generate insight
        result = await orchestrator.generate_insight(request.user_question)

        logger.info(
            "api_request_completed",
            triggered=result.triggered if hasattr(result, 'triggered') else result.triggered,
        )

        return result

    except ValueError as e:
        # Validation errors (e.g., invalid question)
        logger.warning("validation_error", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        # Internal errors
        logger.error("insight_generation_error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate insight: {str(e)}",
        )


@app.get("/api/business-view", tags=["Metadata"])
async def get_business_view_info():
    """
    Get Business View metadata.

    Returns information about available measures, dimensions, and schema.
    """
    try:
        bv = SAMPLE_BUSINESS_VIEW
        return {
            "id": bv.id,
            "name": bv.name,
            "description": bv.description,
            "measures": [
                {
                    "name": m.name,
                    "expression": m.expression,
                    "format": m.format,
                    "description": m.description,
                }
                for m in bv.measures
            ],
            "dimensions": [
                {
                    "name": d.name,
                    "column": d.column,
                    "table": d.table,
                    "description": d.description,
                }
                for d in bv.dimensions
            ],
            "time_dimension": {
                "column": bv.time_dimension.column,
                "table": bv.time_dimension.table,
                "granularity": bv.time_dimension.granularity.value,
            },
        }
    except Exception as e:
        logger.error("business_view_info_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/example-questions", tags=["Examples"])
async def get_example_questions():
    """
    Get example questions for the Intelligent Feed.

    These examples demonstrate the types of questions the system can answer.
    """
    return {
        "examples": [
            {
                "question": "Why did revenue in APAC drop in the last 8 weeks vs previous period?",
                "type": "absolute",
                "description": "Analyzes revenue drop with regional filter and baseline comparison",
            },
            {
                "question": "Show me anomalies in revenue for Q4 2024",
                "type": "arima",
                "description": "Detects anomalies in revenue time-series using ARIMA",
            },
            {
                "question": "What caused the revenue spike in Enterprise segment last month?",
                "type": "absolute",
                "description": "Identifies drivers of revenue increase in specific segment",
            },
            {
                "question": "Why did profit decrease by more than 10% in November?",
                "type": "absolute",
                "description": "Analyzes profit decline with custom threshold",
            },
            {
                "question": "Find unusual patterns in Order_Count for the past 3 months",
                "type": "arima",
                "description": "Detects anomalies in order count using ARIMA",
            },
        ]
    }


# ==================== Feed Management Endpoints ====================

@app.get("/api/feeds", response_model=List[Feed], tags=["Feeds"])
async def list_feeds():
    """Get all feeds."""
    return list(feeds_db.values())


@app.post("/api/feeds", response_model=Feed, tags=["Feeds"])
async def create_feed(feed_data: FeedCreate):
    """Create a new feed."""
    feed_id = str(uuid.uuid4())
    now = datetime.now()
    
    feed = Feed(
        id=feed_id,
        name=feed_data.name,
        bv_name=feed_data.bv_name,
        user_query=feed_data.user_query,
        schedule_type=feed_data.schedule_type,
        schedule_frequency=feed_data.schedule_frequency,
        schedule_time=feed_data.schedule_time,
        schedule_from_date=feed_data.schedule_from_date,
        schedule_to_date=feed_data.schedule_to_date,
        is_active=feed_data.is_active,
        last_run=None,
        created_at=now,
        updated_at=now,
    )
    
    feeds_db[feed_id] = feed
    logger.info("feed_created", feed_id=feed_id, name=feed_data.name)
    return feed


@app.put("/api/feeds/{feed_id}", response_model=Feed, tags=["Feeds"])
async def update_feed(feed_id: str, feed_data: FeedUpdate):
    """Update an existing feed."""
    if feed_id not in feeds_db:
        raise HTTPException(status_code=404, detail="Feed not found")
    
    feed = feeds_db[feed_id]
    update_data = feed_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(feed, field, value)
    
    feed.updated_at = datetime.now()
    feeds_db[feed_id] = feed
    
    logger.info("feed_updated", feed_id=feed_id)
    return feed


@app.delete("/api/feeds/{feed_id}", tags=["Feeds"])
async def delete_feed(feed_id: str):
    """Delete a feed."""
    if feed_id not in feeds_db:
        raise HTTPException(status_code=404, detail="Feed not found")
    
    del feeds_db[feed_id]
    logger.info("feed_deleted", feed_id=feed_id)
    return {"message": "Feed deleted successfully"}


@app.post("/api/feeds/validate", response_model=QueryValidationResult, tags=["Feeds"])
async def validate_feed_query(validation: QueryValidation):
    """Validate a query using LLM to determine intent and suitability for ARIMA or Absolute detection."""
    from anthropic import Anthropic
    
    try:
        client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        
        validation_prompt = f"""Analyze this user query for an analytics feed system and determine:
1. Is it a valid analytics query that can be analyzed?
2. What type of detection should be used: "arima" (for anomaly/outlier detection) or "absolute" (for comparison/change analysis)?

User Query: "{validation.query}"

Guidelines for determining feed_type:
- Use "absolute" when the intent is to:
  * Compare values between two time periods (e.g., "Q4 vs Q3", "this month vs last year")
  * Explain why a change occurred (e.g., "Why did revenue drop?")
  * Quantify a specific change or difference
  
- Use "arima" when the intent is to:
  * Detect unusual patterns, anomalies, or outliers in a time series
  * Monitor for unexpected spikes, drops, or deviations from normal behavior
  * Find irregularities without a direct comparison period

Respond in JSON format:
{{
    "is_valid": true/false,
    "feed_type": "arima" or "absolute" or null,
    "confidence": 0-100,
    "message": "Brief explanation of the analysis",
    "suggestions": ["suggestion1", "suggestion2"] // Only if is_valid is false
}}"""

        response = client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=500,
            messages=[{"role": "user", "content": validation_prompt}]
        )
        
        response_text = response.content[0].text
        # Extract JSON from response
        import re
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            result = json.loads(json_match.group())
            
            return QueryValidationResult(
                is_valid=result.get("is_valid", True),
                can_proceed=True,
                feed_type=result.get("feed_type"),
                message=result.get("message", ""),
                suggestions=result.get("suggestions", [])
            )
        
        # Fallback if JSON parsing fails
        return QueryValidationResult(
            is_valid=True,
            can_proceed=True,
            feed_type="absolute",
            message="Query validated successfully.",
            suggestions=[]
        )
        
    except Exception as e:
        logger.error("query_validation_error", error=str(e))
        # Fallback to allow proceeding on error
        return QueryValidationResult(
            is_valid=True,
            can_proceed=True,
            feed_type=None,
            message="Validation service unavailable. Proceeding with default settings.",
            suggestions=[]
        )


# ==================== Triggered Alerts Endpoints ====================

@app.get("/api/alerts/triggered", response_model=List[TriggeredAlert], tags=["Alerts"])
async def get_triggered_alerts():
    """Get all triggered alerts."""
    return list(triggered_alerts_db.values())


# ==================== Business View Endpoints ====================

@app.get("/api/business-views", tags=["Business Views"])
async def list_business_views():
    """Get all business views."""
    bv = SAMPLE_BUSINESS_VIEW
    
    # Count active feeds for this BV
    active_feeds = sum(1 for f in feeds_db.values() if f.bv_name == bv.name and f.is_active)
    
    return [{
        "name": bv.name,
        "display_name": bv.name.replace("_", " ").title(),
        "description": bv.description or "E-Commerce analytics business view",
        "table_count": len(bv.tables),
        "measure_count": len(bv.measures),
        "active_feeds": active_feeds,
        "last_refresh": None,
    }]


@app.post("/api/business-views/{bv_name}/refresh", tags=["Business Views"])
async def refresh_business_view(bv_name: str):
    """
    Refresh a business view by running all active feeds.
    Returns any triggered alerts.
    """
    logger.info("bv_refresh_started", bv_name=bv_name)
    
    # Get all active feeds for this BV
    active_feeds = [f for f in feeds_db.values() if f.bv_name == bv_name and f.is_active]
    
    triggered_count = 0
    new_alerts = []
    
    for feed in active_feeds:
        try:
            # Run the analysis
            result = await orchestrator.generate_insight(feed.user_query)
            
            # Update last_run
            feed.last_run = datetime.now()
            feeds_db[feed.id] = feed
            
            # Check if triggered
            if result.triggered:
                alert_id = str(uuid.uuid4())
                alert = TriggeredAlert(
                    id=alert_id,
                    feed_id=feed.id,
                    feed_name=feed.name,
                    user_query=feed.user_query,
                    metric=result.metric,
                    trigger_reason=result.trigger_reason,
                    severity=result.evidence.get("alert", {}).get("severity", "medium") if result.evidence else "medium",
                    confidence=result.confidence,
                    triggered_at=datetime.now(),
                    results=result.model_dump(),
                )
                triggered_alerts_db[alert_id] = alert
                new_alerts.append(alert)
                triggered_count += 1
                
        except Exception as e:
            logger.error("feed_analysis_error", feed_id=feed.id, error=str(e))
            continue
    
    logger.info("bv_refresh_completed", bv_name=bv_name, triggered_count=triggered_count)
    
    return {
        "message": f"Analyzed {len(active_feeds)} feeds",
        "triggered_count": triggered_count,
        "new_alerts": [a.model_dump() for a in new_alerts],
    }


@app.get("/api/business-views/{bv_name}/data", tags=["Business Views"])
async def get_business_view_data(bv_name: str, limit: int = 100):
    """
    Get sample data from a business view's tables.
    Returns data in tabular format for display.
    """
    import sqlite3
    import pandas as pd
    import numpy as np
    
    def convert_to_native(obj):
        """Convert numpy types to native Python types for JSON serialization."""
        if isinstance(obj, dict):
            return {k: convert_to_native(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_to_native(item) for item in obj]
        elif isinstance(obj, (np.integer,)):
            return int(obj)
        elif isinstance(obj, (np.floating,)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif pd.isna(obj):
            return None
        return obj
    
    try:
        bv = SAMPLE_BUSINESS_VIEW
        if bv.name != bv_name:
            raise HTTPException(status_code=404, detail="Business view not found")
        
        db_path = "./tellius_feed.db"
        conn = sqlite3.connect(db_path)
        
        # Get data from each table in the BV
        tables_data = {}
        
        for table in bv.tables:
            try:
                # Get sample data from each table
                query = f"SELECT * FROM {table.name} LIMIT {limit}"
                df = pd.read_sql_query(query, conn)
                
                # Convert DataFrame to records and handle numpy types
                records = df.to_dict(orient="records")
                records = [convert_to_native(row) for row in records]
                
                total_rows_df = pd.read_sql_query(f"SELECT COUNT(*) as cnt FROM {table.name}", conn)
                total_rows = int(total_rows_df.iloc[0]["cnt"])
                
                tables_data[table.name] = {
                    "columns": list(df.columns),
                    "data": records,
                    "row_count": len(df),
                    "total_rows": total_rows
                }
            except Exception as e:
                logger.warning(f"Error reading table {table.name}: {e}")
                tables_data[table.name] = {"error": str(e)}
        
        conn.close()
        
        return {
            "bv_name": bv.name,
            "tables": tables_data,
            "measures": [
                {"name": m.name, "expression": m.expression, "format": m.format}
                for m in bv.measures
            ],
            "dimensions": [
                {"name": d.name, "column": d.column, "table": d.table}
                for d in bv.dimensions
            ],
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("bv_data_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
