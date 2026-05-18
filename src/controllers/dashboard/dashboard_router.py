"""Dashboard router: HTML view, JSON API, and unauthenticated health probe."""
import math

from fastapi import APIRouter, Depends, Query, Request

from domain.models.dashboard_stats import DashboardStats
from infrastructure.web.auth import html_require_session, require_session


router = APIRouter()

_PAGE_SIZE = 5


@router.get("/")
async def dashboard_html(
    request: Request,
    page: int = Query(1, ge=1),
    _user: str = Depends(html_require_session),
):
    use_case = request.app.state.use_case
    stats: DashboardStats = use_case.execute()
    transcodings, total_transcodings = use_case.execute_latest_transcodings(page, _PAGE_SIZE)
    total_pages = max(1, math.ceil(total_transcodings / _PAGE_SIZE))
    page = min(page, total_pages)

    max_codec_count = max((c.count for c in stats.codec_distribution), default=1) or 1
    max_resolution_count = (
        max((r.count for r in stats.resolution_distribution), default=1) or 1
    )

    templates = request.app.state.templates
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "stats": stats,
            "max_codec_count": max_codec_count,
            "max_resolution_count": max_resolution_count,
            "transcodings": transcodings,
            "page": page,
            "total_pages": total_pages,
            "total_transcodings": total_transcodings,
        },
    )


@router.get("/api/stats", response_model=DashboardStats)
async def dashboard_stats_json(
    request: Request,
    _user: str = Depends(require_session),
) -> DashboardStats:
    return request.app.state.use_case.execute()


@router.get("/api/transcodings")
async def transcodings_json(
    request: Request,
    page: int = Query(1, ge=1),
    _user: str = Depends(require_session),
):
    use_case = request.app.state.use_case
    transcodings, total = use_case.execute_latest_transcodings(page, _PAGE_SIZE)
    total_pages = max(1, math.ceil(total / _PAGE_SIZE))
    page = min(page, total_pages)
    return {
        "transcodings": [t.model_dump() for t in transcodings],
        "page": page,
        "total_pages": total_pages,
        "total": total,
    }


@router.get("/healthz")
async def healthz():
    return {"status": "ok"}
