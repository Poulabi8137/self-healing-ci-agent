from typing import Any, Dict, List, Optional

PR_SYSTEM_PROMPT = """You are an expert software engineer generating pull request descriptions.

Your role is to:
1. Write clear, concise PR titles and descriptions
2. Explain what the fix does and why
3. Reference the root cause and validation results
4. Provide a summary of changes for reviewers

IMPORTANT RULES:
- Be specific and technical
- Include file paths and change types
- Reference validation results
- Mention review recommendations if available
- Keep the description focused on the changes"""

PR_TITLE_TEMPLATE = """## Fix Details
- Root Cause: {root_cause}
- Fix Summary: {fix_summary}
- Error Category: {error_category}

## Modified Files
{modified_files}

## Validation Results
{validation}

## Review Results
{review}

## Task
Generate a pull request title and description for the fix described above.

Provide your output in the following format:

<pr>
<title>Brief, descriptive PR title (max 72 chars)</title>
<description>
Detailed description of the changes, including:
1. What was fixed and why
2. How the fix was validated
3. Key files modified
4. Any assumptions or caveats
</description>
<change_summary>
Bullet-point summary of all changes made.
</change_summary>
</pr>"""


def build_pr_prompt(
    root_cause: str,
    fix_summary: str,
    error_category: str,
    modified_files: List[str],
    validation: str,
    review: str,
) -> Dict[str, str]:
    """Build system and user prompts for PR content generation.

    Args:
        root_cause: Root cause analysis text.
        fix_summary: Summary of the generated fix.
        error_category: Error category string.
        modified_files: List of modified file paths.
        validation: Validation report text.
        review: Review report text.

    Returns:
        Dict with keys 'system' and 'user' for LLM completion.
    """
    files_str = "\n".join(f"- {f}" for f in modified_files) if modified_files else "- (no files listed)"

    user_prompt = PR_TITLE_TEMPLATE.format(
        root_cause=root_cause or "(not available)",
        fix_summary=fix_summary or "(not available)",
        error_category=error_category or "unknown",
        modified_files=files_str,
        validation=validation or "(validation not available)",
        review=review or "(review not available)",
    )

    return {
        "system": PR_SYSTEM_PROMPT,
        "user": user_prompt,
    }


def parse_pr_output(llm_output: str) -> Dict[str, Any]:
    """Parse structured XML-like tags from LLM PR output into a dict.

    Args:
        llm_output: Raw text from the LLM containing <pr> tags.

    Returns:
        Dict with keys: title, description, change_summary.
    """
    import re

    result: Dict[str, Any] = {
        "title": "",
        "description": "",
        "change_summary": "",
    }

    title_match = re.search(r"<title>(.*?)</title>", llm_output, re.DOTALL)
    if title_match:
        result["title"] = title_match.group(1).strip()

    desc_match = re.search(r"<description>(.*?)</description>", llm_output, re.DOTALL)
    if desc_match:
        result["description"] = desc_match.group(1).strip()

    summary_match = re.search(r"<change_summary>(.*?)</change_summary>", llm_output, re.DOTALL)
    if summary_match:
        result["change_summary"] = summary_match.group(1).strip()

    return result
