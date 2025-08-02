import gradio as gr
from main import get_review_result
import tempfile

def get_task_results(task_id: str):
    data = get_review_result(task_id)
    if "error" in data:
        return f"Error fetching results: {data['error']}", None
    
    output = f"### Code Review Results\n\n"
    output += f"**Task ID:** {task_id}\n"
    output += f"**Status:** {data['status']}\n\n"
    output += f"**Summary:**\n"
    output += f"- Total Files: {data['summary']['total_files']}\n"
    output += f"- Total Issues: {data['summary']['total_issues']}\n"
    output += f"- Critical Issues: {data['summary']['critical_issues']}\n\n"

    for file in data["files"]:
        output += f"---\n### File: `{file['file_name']}`\n"
        for issue in file["issues"]:
            output += f"- **Type:** {issue['type'].capitalize()}\n"
            output += f"  - Line: {issue['line']}\n"
            output += f"  - Description: {issue['description']}\n"
            output += f"  - Suggestion: {issue['suggestion']}\n\n"

    # Write to a temporary file
    report_path = tempfile.NamedTemporaryFile(delete=False, suffix=".txt").name
    with open(report_path, "w") as f:
        f.write(output)
    
    return output, report_path

    
with gr.Blocks() as demo:
    gr.Markdown("## Code Review Viewer")
    task_input = gr.Textbox(label="Enter Task ID")
    output = gr.Markdown()
    download_button = gr.File(label="Download Report")

    task_input.submit(fn=get_task_results, inputs=task_input, outputs=[output, download_button])

demo.launch(share=True, server_name="0.0.0.0")

