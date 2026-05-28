from typing import Any, Dict, List, Optional


SYSTEM_PROMPT = """You are an expert AI debugging engineer specialized in CI/CD pipeline failure analysis.

Your role is to:
1. Analyze CI/CD build/test logs and stack traces
2. Use the provided repository code context to understand the codebase
3. Identify the root cause of failures
4. Identify affected files and modules
5. Provide structured debugging recommendations

IMPORTANT RULES:
- Base your analysis on the actual logs and code context provided
- Do not guess or hallucinate file names or errors
- If the provided context is insufficient, state that clearly
- Be specific about line numbers and file paths when possible
- Separate symptoms from root causes
- Consider the order of operations in the CI/CD pipeline"""


ROOT_CAUSE_ANALYSIS_TEMPLATE = """## CI/CD Failure Logs

### Error Message
{error_message}

### Stack Trace
{stack_trace}

### Failure Type
{failure_type}

### Failing File
{failing_file}

## Repository Context
{retrieval_context}

## Task
Analyze the CI/CD failure above and provide a structured root cause analysis.

Focus on:
1. What is the root cause of this failure?
2. Which files/modules are affected?
3. What is the chain of events leading to the failure?
4. What specific debugging steps should be taken?

Provide your analysis in the following format:

<analysis>
<root_cause>Clearly describe the root cause</root_cause>
<affected_files>List affected file paths</affected_files>
<analysis_summary>Concise summary of the failure chain</analysis_summary>
<debugging_steps>Numbered list of debugging steps</debugging_steps>
</analysis>"""


def build_debug_prompt(
    error_message: str,
    stack_trace: str,
    failure_type: str,
    failing_file: str,
    retrieval_context: str,
    error_category: Optional[str] = None,
) -> Dict[str, str]:
    """Build the system and user prompts for root cause analysis.

    Args:
        error_message: Parsed error message from logs.
        stack_trace: Extracted stack trace.
        failure_type: CI/CD failure type.
        failing_file: File where the failure occurred (if known).
        retrieval_context: Formatted repository retrieval context.
        error_category: Optional classified error category.

    Returns:
        Dict with keys 'system' and 'user' for LLM completion.
    """
    context_parts = []
    if error_category:
        context_parts.append(f"### Classified Error Category\n{error_category}")

    user_prompt = ROOT_CAUSE_ANALYSIS_TEMPLATE.format(
        error_message=error_message or "(not detected)",
        stack_trace=stack_trace or "(not available)",
        failure_type=failure_type or "unknown",
        failing_file=failing_file or "(not identified)",
        retrieval_context=retrieval_context or "(no repository context available)",
    )

    return {
        "system": SYSTEM_PROMPT,
        "user": user_prompt,
    }


def parse_analysis_output(llm_output: str) -> Dict[str, Any]:
    """Parse structured XML-like tags from LLM output into a dict.

    Args:
        llm_output: Raw text from the LLM containing <analysis> tags.

    Returns:
        Dict with keys: root_cause, affected_files, analysis_summary, debugging_steps.
    """
    import re

    result: Dict[str, Any] = {
        "root_cause": "",
        "affected_files": [],
        "analysis_summary": "",
        "debugging_steps": [],
    }

    root_cause_match = re.search(r"<root_cause>(.*?)</root_cause>", llm_output, re.DOTALL)
    if root_cause_match:
        result["root_cause"] = root_cause_match.group(1).strip()

    files_match = re.search(r"<affected_files>(.*?)</affected_files>", llm_output, re.DOTALL)
    if files_match:
        raw = files_match.group(1).strip()
        result["affected_files"] = [f.strip() for f in raw.split("\n") if f.strip()]

    summary_match = re.search(r"<analysis_summary>(.*?)</analysis_summary>", llm_output, re.DOTALL)
    if summary_match:
        result["analysis_summary"] = summary_match.group(1).strip()

    steps_match = re.search(r"<debugging_steps>(.*?)</debugging_steps>", llm_output, re.DOTALL)
    if steps_match:
        raw = steps_match.group(1).strip()
        result["debugging_steps"] = [
s.strip() for s in re.split(r"\d+\.\s*", raw) if s.strip()
        ]

    return result
