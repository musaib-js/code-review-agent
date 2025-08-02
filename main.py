from fastapi import FastAPI
from pydantic import BaseModel
from celery_tasks.review import run_pr_review
from db.database import init_db, SessionLocal
from contextlib import asynccontextmanager
import logging
from celery.result import AsyncResult
from typing import Optional, List, Dict
from fastapi import HTTPException
from db.models import Review, FileIssue
from pydantic import BaseModel
from core.caching import cache_result, get_cached_result

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("Connecting to database...")
    init_db()
    yield
    logging.info("Shutting down application...")


app = FastAPI(lifespan=lifespan)


class PRRequest(BaseModel):
    repo_url: str
    pr_number: int
    github_token: Optional[str] = None


@app.post("/review")
def review_pr(data: PRRequest):
    review_task = run_pr_review.delay(data.repo_url, data.pr_number, data.github_token)
    return {"message": "Review started in background", "task_id": review_task.id}


@app.post("/get-task-status")
def get_task_status(task_id: str):
    result = AsyncResult(task_id)
    if result.state == "PENDING":
        return {"status": "Pending"}
    elif result.state == "SUCCESS":
        return {"status": "Success", "result": result.result}
    elif result.state == "FAILURE":
        return {"status": "Failure", "error": str(result.info)}
    else:
        return {"status": result.state}


class FileIssueSchema(BaseModel):
    file_name: str
    issues: List[dict]


class ReviewResultSchema(BaseModel):
    task_id: str
    status: str
    summary: Optional[Dict[str, int]] = None
    files: List[FileIssueSchema]


@app.get("/results/{task_id}", response_model=ReviewResultSchema)
def get_review_result(task_id: str):

    cached_result = get_cached_result(task_id)
    if cached_result:
        return cached_result

    else:

        db = SessionLocal()
        review = db.query(Review).filter(Review.task_id == task_id).first()
        if not review:
            raise HTTPException(status_code=404, detail="Review not found")

        file_issues = db.query(FileIssue).filter(FileIssue.review_id == task_id).all()

        cache_result(
            task_id,
            {
                "task_id": review.task_id,
                "status": review.status,
                "summary": review.summary,
                "files": [
                    {"file_name": fi.file_name, "issues": fi.issues}
                    for fi in file_issues
                ],
            },
        )

        return {
            "task_id": review.task_id,
            "status": review.status,
            "summary": review.summary,
            "files": [
                {"file_name": fi.file_name, "issues": fi.issues} for fi in file_issues
            ],
        }
