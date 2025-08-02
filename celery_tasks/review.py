from celery import shared_task
from agents.review_agent import CodeReviewAgent
from core.config import OPENAI_API_KEY
from db.models import Review, FileIssue
from db.database import SessionLocal
import logging
from agents.utils import post_pr_comment

@shared_task(bind=True)
def run_pr_review(self, repo_url: str, pr_number: int, token: str = None, commit_sha: str = None):
    agent = CodeReviewAgent(OPENAI_API_KEY)
    result = agent.analyze(repo_url, pr_number, token)

    logging.info(f"Review result for {repo_url} PR #{pr_number}")

    db = SessionLocal()
    try:
        review = Review(
            task_id=result["task_id"],
            status=result["status"],
            summary=result["results"]["summary"],
        )

        db.add(review)

        db.commit()
        logging.info(f"Review saved to database for task {result['task_id']}")

        logging.info(f"Saving file issues for task {result['task_id']}")

        for file in result["results"]["files"]:
            file_issue = FileIssue(
                review_id=result["task_id"],
                file_name=file["name"],
                issues=file["issues"],
            )
            db.add(file_issue)

        db.commit()
        logging.info(f"Review saved to database for task {result['task_id']}")
        
        for file in result["results"]["files"]:
            for issue in file["issues"]:
                comment_body = f"**{issue['type'].capitalize()}** at line {issue['line']}: {issue['description']}\n\nSuggestion: {issue['suggestion']}"
                post_pr_comment(
                    repo_full_name=repo_url.replace("https://github.com/", ""),
                    pr_number=pr_number,
                    body=comment_body,
                    commit_id=commit_sha,
                    path=file["name"],
                    line=issue["line"],
                    github_token=token
                )

    except Exception as e:
        db.rollback()
        logging.error(f"Error saving review to database: {e}")
        raise self.retry(exc=e)
    finally:
        db.close()

    return {
        "task_id": result["task_id"],
        "status": result["status"],
        "summary": result["results"]["summary"]
    }
