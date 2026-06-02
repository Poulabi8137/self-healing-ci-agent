from typing import Any, Dict, List

REVIEW_SYSTEM_PROMPT = """You are an expert code reviewer specialized in evaluating AI-generated code fixes.

Your role is to analyze the proposed fix, validation results, and repository context to provide structured scores and actionable recommendations.

IMPORTANT RULES:
- Be objective and evidence-based
- Score from 0.0 (worst) to 1.0 (best)
- List specific issues with clear descriptions
- Provide actionable recommendations
- Consider the fix in the context of the repository"""

SECURITY_REVIEW_TEMPLATE = """## Fix Proposal
{fix_summary}

## Patch
{patch}

## Modified Files
{modified_files}

## Validation Results
{validation}

## Task: Security Review
Review the proposed fix for security concerns:

Check for:
1. Hardcoded secrets, API keys, tokens, or passwords
2. Unsafe execution patterns (eval, exec, shell injection)
3. Dangerous imports or dependency risks
4. Insecure coding practices (SQL injection, command injection)
5. Permission or authentication issues
6. Exposure of sensitive data

For each issue found, describe:
- The specific concern
- The severity
- A recommendation to fix it

Provide your review in the following format:

<review>
<score>0.0 to 1.0</score>
<issues>
- Security issue 1
- Security issue 2
</issues>
<recommendations>
- Recommendation 1
- Recommendation 2
</recommendations>
</review>"""

PERFORMANCE_REVIEW_TEMPLATE = """## Fix Proposal
{fix_summary}

## Patch
{patch}

## Modified Files
{modified_files}

## Validation Results
{validation}

## Task: Performance Review
Review the proposed fix for performance concerns:

Check for:
1. Inefficient loops or nested iterations
2. Excessive computations or repeated calculations
3. Memory-heavy operations or leaks
4. Redundant processing or unnecessary operations
5. Poor data structure choices
6. Missing caching opportunities
7. Unoptimized database queries

For each issue found, describe:
- The specific concern
- The severity
- A recommendation to optimize

Provide your review in the following format:

<review>
<score>0.0 to 1.0</score>
<issues>
- Performance issue 1
- Performance issue 2
</issues>
<recommendations>
- Recommendation 1
- Recommendation 2
</recommendations>
</review>"""

QUALITY_REVIEW_TEMPLATE = """## Fix Proposal
{fix_summary}

## Patch
{patch}

## Modified Files
{modified_files}

## Validation Results
{validation}

## Task: Code Quality Review
Review the proposed fix for code quality concerns:

Check for:
1. Readability and clarity of the code
2. Maintainability and future-proofing
3. Modularity and separation of concerns
4. Naming conventions and consistency
5. Code organization and structure
6. Error handling completeness
7. Documentation and comments
8. Adherence to coding standards (PEP 8, etc.)

For each issue found, describe:
- The specific concern
- The severity
- A recommendation to improve quality

Provide your review in the following format:

<review>
<score>0.0 to 1.0</score>
<issues>
- Quality issue 1
- Quality issue 2
</issues>
<recommendations>
- Recommendation 1
- Recommendation 2
</recommendations>
</review>"""

COVERAGE_REVIEW_TEMPLATE = """## Fix Proposal
{fix_summary}

## Patch
{patch}

## Modified Files
{modified_files}

## Validation Results
{validation}

## Task: Test Coverage Review
Review the proposed fix for test coverage concerns:

Check for:
1. Missing test cases for new or modified code
2. Edge cases not covered (boundary conditions, error paths)
3. Weak or insufficient assertions
4. Missing integration or regression tests
5. Tests that don't validate the actual fix
6. Fragile test dependencies

For each issue found, describe:
- The specific coverage gap
- The severity
- A recommendation to improve coverage

Provide your review in the following format:

<review>
<score>0.0 to 1.0</score>
<issues>
- Coverage issue 1
- Coverage issue 2
</issues>
<recommendations>
- Recommendation 1
- Recommendation 2
</recommendations>
</review>"""


def build_review_prompt(
    review_type: str,
    fix_summary: str,
    patch: str,
    modified_files: List[str],
    validation: str,
) -> Dict[str, str]:
    """Build system and user prompts for a specific review type.

    Args:
        review_type: One of 'security', 'performance', 'quality', 'coverage'.
        fix_summary: Summary of the generated fix.
        patch: The code patch to review.
        modified_files: List of modified file paths.
        validation: Validation report text.

    Returns:
        Dict with keys 'system' and 'user' for LLM completion.
    """
    template_map = {
        "security": SECURITY_REVIEW_TEMPLATE,
        "performance": PERFORMANCE_REVIEW_TEMPLATE,
        "quality": QUALITY_REVIEW_TEMPLATE,
        "coverage": COVERAGE_REVIEW_TEMPLATE,
    }

    template = template_map.get(review_type, SECURITY_REVIEW_TEMPLATE)
    files_str = "\n".join(modified_files) if modified_files else "(no files listed)"

    user_prompt = template.format(
        fix_summary=fix_summary or "(not available)",
        patch=patch or "(no patch provided)",
        modified_files=files_str,
        validation=validation or "(validation not available)",
    )

    return {
        "system": REVIEW_SYSTEM_PROMPT,
        "user": user_prompt,
    }


def parse_review_output(llm_output: str) -> Dict[str, Any]:
    """Parse structured XML-like tags from LLM review output into a dict.

    Args:
        llm_output: Raw text from the LLM containing <review> tags.

    Returns:
        Dict with keys: score, issues, recommendations.
    """
    import re

    result: Dict[str, Any] = {
        "score": 0.0,
        "issues": [],
        "recommendations": [],
    }

    score_match = re.search(r"<score>\s*([\d.]+)\s*</score>", llm_output)
    if score_match:
        try:
            result["score"] = round(float(score_match.group(1)), 2)
        except ValueError:
            result["score"] = 0.0

    issues_match = re.search(r"<issues>(.*?)</issues>", llm_output, re.DOTALL)
    if issues_match:
        raw = issues_match.group(1).strip()
        result["issues"] = [i.strip().lstrip("- ").strip() for i in raw.split("\n") if i.strip()]

    recs_match = re.search(r"<recommendations>(.*?)</recommendations>", llm_output, re.DOTALL)
    if recs_match:
        raw = recs_match.group(1).strip()
        result["recommendations"] = [r.strip().lstrip("- ").strip() for r in raw.split("\n") if r.strip()]

    return result
