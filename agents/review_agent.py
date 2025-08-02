import logging
import requests
from crewai import Crew, Agent, Task
from openai import OpenAI
import uuid
from pydantic import BaseModel
from typing import List, Dict
import json


class Issue(BaseModel):
    type: str
    line: int
    description: str
    suggestion: str

class ReviewOutput(BaseModel):
    name: str
    issues: List[Issue]


class CodeReviewAgent:
    def __init__(self, openai_api_key: str):
        self.openai_api_key = openai_api_key
        self.client = OpenAI(api_key=openai_api_key)
        self.review_agent = Agent(
            role="Code Review Expert",
            goal="Identify all issues in code diffs including style, bugs, and critical concerns",
            backstory="You are a senior software engineer who reviews pull requests for code quality, safety, and style.",
            verbose=True,
            allow_delegation=False,
            llm="gpt-4.1-mini",
        )

    def _fetch_diff_by_file(self, repo_url: str, pr_number: int, token: str):
        """
        Fetches the diff of a pull request split by file.
        """
        owner_repo = repo_url.replace("https://github.com/", "").strip("/")
        api_url = f"https://api.github.com/repos/{owner_repo}/pulls/{pr_number}/files"

        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3.diff+json",
        }

        response = requests.get(api_url, headers=headers)
        if response.status_code != 200:
            raise Exception(
                f"Failed to fetch PR diff: {response.status_code} {response.text}"
            )

        file_diffs = {}
        for file in response.json():
            filename = file.get("filename")
            patch = file.get("patch", "")
            file_diffs[filename] = patch

        return file_diffs

    def _build_prompt(self, file_name: str, diff: str):
        return f"""
            You are a senior software engineer performing a code review.

            File: {file_name}

            Diff:
            {diff}

            Respond ONLY with a valid JSON object in this format:

            {{
            "name": "{file_name}",
            "issues": [
                {{
                "type": "bug" | "style" | "performance" | "best_practice",
                "line": <line_number>,
                "description": "clear explanation of the issue",
                "suggestion": "suggested fix or improvement"
                }}
            ]
            }}

            Guidelines:
            - Do NOT return markdown.
            - Do NOT explain your answer.
            - Do NOT include triple backticks.
            - Ensure valid JSON only.
            - If no issues found, return: {{
                "name": "{file_name}",
                "issues": []
            }}
            """


    def analyze(self, repo_url: str, pr_number: int, token: str = None):
        file_diffs = self._fetch_diff_by_file(repo_url, pr_number, token)
        task_id = str(uuid.uuid4())

        reviewed_files = []
        total_issues = 0
        critical_issues = 0

        for file_name, diff in file_diffs.items():
            prompt = self._build_prompt(file_name, diff)

            review_task = Task(
                description=prompt,
                agent=self.review_agent,
                expected_output="Return only the JSON with the issues found for this file as instructed.",
                output_json=ReviewOutput
            )

            crew = Crew(
                agents=[self.review_agent],
                tasks=[review_task],
                verbose=True,
            )

            result = crew.kickoff()
            
            logging.info(f"Review result for {file_name}: {result}")
            
            result = json.loads(result) if isinstance(result, str) else result
            
            logging.info(f"Parsed result for {file_name}: {result} {type(result)}")
            
            try:
                file_result = eval(result) if isinstance(result, str) else result
                reviewed_files.append(file_result)

                total_issues += len(file_result["issues"])
                critical_issues += sum(
                    1 for issue in file_result["issues"] if issue["type"] == "bug"
                )
            except Exception as e:
                logging.warning(f"Error parsing result for {file_name}: {e}")
                continue

        summary = {
            "total_files": len(reviewed_files),
            "total_issues": total_issues,
            "critical_issues": critical_issues,
        }
        

        return {
            "task_id": task_id,
            "status": "completed",
            "results": {
                "files": reviewed_files,
                "summary": summary,
            },
        }
