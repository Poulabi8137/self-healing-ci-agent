from typing import Any, Dict, List, Optional

RETRY_SYSTEM_PROMPT = """You are an expert AI software engineer specialized in diagnosing failed code fixes and generating improved patches.

Your role is to:
1. Analyze why a previous fix attempt failed during validation
2. Identify incorrect assumptions or missing changes
3. Generate corrected, minimal code patches
4. Preserve the repository's coding style and conventions

IMPORTANT RULES:
- Learn from the previous attempt — do not repeat the same mistakes
- Address each validation failure explicitly (syntax errors, test failures, build issues)
- Generate complete patches, not just diffs from the previous attempt
- Be specific about file paths and exact changes
- If uncertain, state assumptions clearly
- Do not introduce new bugs or break existing functionality"""

RETRY_ANALYSIS_TEMPLATE = """## Previous Fix Proposal (Attempt {attempt_number})
- Summary: {fix_summary}
- Confidence: {confidence}
- Assumptions: {assumptions}

## Previous Validation Results
- Validation Status: {validation_status}
- Syntax Errors: {syntax_errors}
- Failed Tests: {failed_tests}
- Build Issues: {build_issues}

## Root Cause Analysis
{root_cause}

## Error Classification
- Error Category: {error_category}
- Failure Type: {failure_type}

## Repository Context
{retrieval_context}

## CI/CD Logs
{logs}

## Analysis Summary
{analysis_summary}

## Task
The previous fix attempt failed validation. Analyze the failures and generate an improved fix.

Consider:
1. What went wrong in the previous fix?
2. Were any assumptions incorrect?
3. What should change compared to the previous attempt?
4. Are there additional files that need modification?

Provide your improved fix in the following format:

<fix>
<modified_files>
List each file path that needs to be modified, one per line
</modified_files>
<fix_summary>
Brief explanation of what changed from the previous attempt and why
</fix_summary>
<patch>
For each file, provide the patch in unified diff format (---/+++ lines showing what changed).
Include the file path, line numbers, and the actual code changes.
</patch>
<assumptions>
List any assumptions you made while generating this improved fix. Also note which previous assumptions were corrected.
</assumptions>
</fix>"""


def build_retry_prompt(
    attempt_number: int,
    previous_fix: Dict[str, Any],
    previous_validation: Dict[str, Any],
    root_cause: str,
    error_category: str,
    failure_type: str,
    logs: str,
    analysis_summary: str,
    retrieval_context: str = "",
) -> Dict[str, str]:
    """Build system and user prompts for retry fix generation.

    Args:
        attempt_number: The current retry attempt number.
        previous_fix: The fix proposal from the previous attempt.
        previous_validation: The validation report from the previous attempt.
        root_cause: Root cause description.
        error_category: Error category string.
        failure_type: Failure type string.
        logs: Raw CI/CD logs.
        analysis_summary: Summary from analysis phase.
        retrieval_context: Optional repository context.

    Returns:
        Dict with keys 'system' and 'user' for LLM completion.
    """
    fix_summary = previous_fix.get("fix_summary", "")
    confidence = previous_fix.get("confidence", 0.0)
    assumptions = previous_fix.get("assumptions", [])
    validation_status = previous_validation.get("validation_status", "unknown")
    syntax_errors = previous_validation.get("syntax_errors", [])
    failed_tests = previous_validation.get("failed_tests", [])
    build_checks = previous_validation.get("build_checks", [])

    user_prompt = RETRY_ANALYSIS_TEMPLATE.format(
        attempt_number=attempt_number,
        fix_summary=fix_summary or "(not available)",
        confidence=confidence,
        assumptions="; ".join(assumptions) if assumptions else "(none stated)",
        validation_status=validation_status,
        syntax_errors="; ".join(e.get("message", str(e)) for e in (syntax_errors or [])),
        failed_tests="; ".join(failed_tests) if failed_tests else "(none)",
        build_issues="; ".join(build_checks) if build_checks else "(none reported)",
        root_cause=root_cause or "(not available)",
        error_category=error_category or "unknown",
        failure_type=failure_type or "unknown",
        retrieval_context=retrieval_context or "(no repository context available)",
        logs=logs or "(no logs provided)",
        analysis_summary=analysis_summary or "(not available)",
    )

    return {
        "system": RETRY_SYSTEM_PROMPT,
        "user": user_prompt,
    }


def parse_retry_output(llm_output: str) -> Dict[str, Any]:
    """Parse structured XML-like tags from LLM retry output into a dict.

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
