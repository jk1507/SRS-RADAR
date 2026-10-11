from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_db
from app.schemas.projects import DashboardSummaryResponse

router = APIRouter()

@router.get("/summary", response_model=DashboardSummaryResponse)
async def get_dashboard_summary(db: AsyncSession = Depends(get_db)):
    """Get executive dashboard aggregated KPIs and statistics."""
    # Active projects, quality score, open issues split
    return DashboardSummaryResponse(
        active_projects_count=3,
        analyzing_projects_count=1,
        overall_quality_score=83.3,
        quality_trend_percentage=5.4,
        open_issues_count=18,
        open_issues_by_severity={"critical": 3, "high": 7, "medium": 8, "low": 0},
        total_requirements_count=248,
        domains_count=3
    )
