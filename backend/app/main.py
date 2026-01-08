"""FastAPI application for Intelligent Feed system."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.models.response import InsightRequest, InsightResponse, HealthResponse, ErrorResponse
from app.services.orchestrator import IntelligentFeedOrchestrator
from app.utils.sample_business_view import SAMPLE_BUSINESS_VIEW
from app.core.config import settings
from app.core.logging import setup_logging, get_logger

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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
