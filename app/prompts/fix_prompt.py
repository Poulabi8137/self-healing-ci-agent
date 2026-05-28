from typing import Any, Dict, List, Optional

FIX_SYSTEM_PROMPT = """You are an expert AI software engineer specialized in generating code fixes for CI/CD pipeline failures.

Your role is to:
1. Analyze the root cause analysis and repository context provided
2. Generate minimal, correct code patches to fix the identified issues
3. Preserve the existing coding style and conventions of the repository
4. Provide clear explanations for each change

IMPORTANT RULES:
- Generate patches only — do not execute them
- Follow the existing code style from the repository context
- Make minimal changes — fix only what is broken
- Include necessary imports if adding new dependencies
- Be specific about file paths and line numbers
- If the fix is uncertain, state your assumptions clearly
- Do not introduce new bugs or break existing functionality
- Consider edge cases and error handling"""

FIX_GENERATION_TEMPLATE = """## Root Cause Analysis
{root_cause_analysis}

## Error Classification
- Category: {error_category}
- Confidence: {confidence}
- Failure Type: {failure_type}

## Repository Context
{retrieval_context}

## CI/CD Logs
{logs}

## Analysis Summary
{analysis_summary}

## Task
Generate a code fix for the CI/CD failure described above.

Provide your fix in the following format:

<fix>
<modified_files>
List each file path that needs to be modified, one per line
</modified_files>
<fix_summary>
Brief explanation of what the fix does and why
</fix_summary>
<patch>
For each file, provide the patch in unified diff format (---/+++ lines showing what changed).
Include the file path, line numbers, and the actual code changes.
</patch>
<assumptions>
List any assumptions you made while generating this fix
</assumptions>
</fix>"""


def build_fix_prompt(
    root_cause_analysis: str,
    retrieval_context: str,
    logs: str,
    error_category: str,
    failure_type: str,
    analysis_summary: str,
    affected_files: Optional[List[str]] = None,
    confidence: float = 0.0,
) -> Dict[str, str]:
    """Build system and user prompts for fix generation.

    Args:
        root_cause_analysis: Root cause description from analysis phase.
        retrieval_context: Formatted repository code context.
        logs: Raw CI/CD logs.
        error_category: Classified error category.
        failure_type: Failure type string.
        analysis_summary: Summary from the analysis phase.
        affected_files: Files identified during analysis.
        confidence: Confidence score from analysis.

    Returns:
        Dict with keys 'system' and 'user' for LLM completion.
    """
    context_parts = []
    if affected_files:
        context_parts.append("### Affected Files (from analysis)\n" + "\n".join(affected_files))

    user_prompt = FIX_GENERATION_TEMPLATE.format(
        root_cause_analysis=root_cause_analysis or "(not available)",
        error_category=error_category or "unknown",
        confidence=confidence,
        failure_type=failure_type or "unknown",
        retrieval_context=retrieval_context or "(no repository context available)",
        logs=logs or "(no logs provided)",
        analysis_summary=analysis_summary or "(not available)",
    )

    if context_parts:
        user_prompt = "\n\n".join(context_parts) + "\n\n" + user_prompt

    return {
        "system": FIX_SYSTEM_PROMPT,
        "user": user_prompt,
    }


def parse_fix_output(llm_output: str) -> Dict[str, Any]:
    """Parse structured XML-like tags from LLM fix output into a dict.

    Args:
        llm_output: Raw text from the LLM containing <fix> tags.

    Returns:
        Dict with keys: modified_files, fix_summary, patch, assumptions.
    """
    import re

    result: Dict[str, Any] = {
        "modified_files": [],
        "fix_summary": "",
        "patch": "",
        "assumptions": [],
    }

    files_match = re.search(r"<modified_files>(.*?)</modified_files>", llm_output, re.DOTALL)
    if files_match:
        raw = files_match.group(1).strip()
        result["modified_files"] = [f.strip() for f in raw.split("\n") if f.strip()]

    summary_match = re.search(r"<fix_summary>(.*?)</fix_summary>", llm_output, re.DOTALL)
    if summary_match:
        result["fix_summary"] = summary_match.group(1).strip()

    patch_match = re.search(r"<patch>(.*?)</patch>", llm_output, re.DOTALL)
    if patch_match:
        result["patch"] = patch_match.group(1).strip()

    assumptions_match = re.search(r"<assumptions>(.*?)</assumptions>", llm_output, re.DOTALL)
    if assumptions_match:
        raw = assumptions_match.group(1).strip()
        result["assumptions"] = [a.strip() for a in raw.split("\n") if a.strip()]

    return result
