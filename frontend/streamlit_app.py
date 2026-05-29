import streamlit as st

st.set_page_config(
    page_title="Self-Healing AI CI/CD Agent",
    page_icon="🤖",
    layout="wide",
)

st.title("Self-Healing AI CI/CD Failure Resolution System")
st.markdown("---")

with st.sidebar:
    st.header("Repository Indexing")
    repo_url = st.text_input(
        "Repository URL",
        placeholder="https://github.com/user/repo or local path",
    )
    branch = st.text_input("Branch (optional)", placeholder="main")
    if st.button("Index Repository"):
        if repo_url:
            st.session_state.repo_to_index = repo_url
            st.session_state.branch = branch or None
        else:
            st.warning("Enter a repository URL or path.")

    st.markdown("---")
    st.header("CI/CD Analysis & Fix")
    st.caption("Enter logs in the main panel.")

    st.markdown("---")
    st.caption("Self-Healing AI CI/CD Agent v0.1.0")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Repository Input")
    with st.container(border=True):
        if "repo_to_index" in st.session_state:
            st.info(f"Repository to index: `{st.session_state.repo_to_index}`")
        else:
            st.info("Enter a repo URL in the sidebar.")

    st.subheader("Indexing Status")
    with st.container(border=True):
        st.metric("Repositories Indexed", "—")
        st.metric("Files Processed", "—")
        st.metric("Chunks Created", "—")

    st.subheader("CI/CD Log Input")
    with st.container(border=True):
        analysis_repo = st.text_input("Repository name", placeholder="e.g., my-org-my-repo")
        analysis_logs = st.text_area("Paste CI/CD logs", height=150)
        if st.button("Analyze & Generate Fix") and analysis_repo and analysis_logs:
            st.session_state.analysis_repo = analysis_repo
            st.session_state.analysis_logs = analysis_logs

    st.subheader("Root Cause Analysis")
    with st.container(border=True):
        if "analysis_repo" in st.session_state:
            st.write(f"Repository: `{st.session_state.analysis_repo}`")
            st.caption("Analysis runs on the backend via `POST /analysis/debug`.")
        else:
            st.info("Enter logs and click **Analyze & Generate Fix**.")

with col2:
    st.subheader("Fix Summary")
    with st.container(border=True):
        if "analysis_repo" in st.session_state:
            st.caption("Fix generation runs on the backend via `POST /fix/generate`.")
        else:
            st.info("AI-generated fix summary will appear here.")

    st.subheader("Modified Files")
    with st.container(border=True):
        st.info("List of files to be modified will appear here.")

    st.subheader("Patch Preview")
    with st.container(border=True):
        st.info("Unified diff patch will appear here.")

    st.subheader("Assumptions")
    with st.container(border=True):
        st.info("Assumptions made during fix generation will appear here.")

st.markdown("---")
st.header("Validation")

val_col1, val_col2, val_col3 = st.columns(3)

with val_col1:
    st.subheader("Syntax Validation")
    with st.container(border=True):
        st.caption("Validates Python syntax with `ast.parse`.")
        st.metric("Syntax Errors", "—")

with val_col2:
    st.subheader("Build Validation")
    with st.container(border=True):
        st.caption("Checks project structure and config files.")
        st.metric("Build Checks", "—")

with val_col3:
    st.subheader("Test Execution")
    with st.container(border=True):
        st.caption("Runs pytest and captures failures.")
        st.metric("Tests Passed", "—")

st.subheader("Full Validation Pipeline")
with st.container(border=True):
    val_repo = st.text_input(
        "Repository name",
        key="val_repo",
        placeholder="e.g., my-org-my-repo",
    )
    val_logs = st.text_area("CI/CD logs", key="val_logs", height=120)
    val_cols = st.columns([1, 3])
    with val_cols[0]:
        run_val = st.button("Run Validation Pipeline")
    if run_val and val_repo and val_logs:
        st.session_state.val_repo = val_repo
        st.session_state.val_logs = val_logs

    if "val_repo" in st.session_state:
        st.success(f"Validation triggered for `{st.session_state.val_repo}` via `POST /validation/run`.")
        st.caption("Results appear below after backend processing.")

st.markdown("---")
st.header("Self-Healing Retry Loop")

sh_col1, sh_col2 = st.columns(2)

with sh_col1:
    st.subheader("Run Self-Healing")
    with st.container(border=True):
        sh_repo = st.text_input(
            "Repository name",
            key="sh_repo",
            placeholder="e.g., my-org-my-repo",
        )
        sh_logs = st.text_area("CI/CD logs", key="sh_logs", height=120)
        if st.button("Run Self-Healing"):
            if sh_repo and sh_logs:
                st.session_state.sh_repo = sh_repo
                st.session_state.sh_logs = sh_logs
            else:
                st.warning("Enter a repository name and logs.")

        if "sh_repo" in st.session_state:
            st.success(f"Self-healing triggered for `{st.session_state.sh_repo}` via `POST /retry/run`.")

with sh_col2:
    st.subheader("Attempt History")
    with st.container(border=True):
        if "sh_repo" in st.session_state:
            st.caption("Retry timeline will appear here after backend processing.")
            st.metric("Attempts Used", "—")
            st.metric("Final Status", "—")
        else:
            st.info("Trigger a self-healing run to see attempt history.")

st.subheader("Retry Timeline")
with st.container(border=True):
    timeline_cols = st.columns(3)
    with timeline_cols[0]:
        st.caption("Attempt 1")
        st.metric("Status", "—")
    with timeline_cols[1]:
        st.caption("Attempt 2")
        st.metric("Status", "—")
    with timeline_cols[2]:
        st.caption("Attempt 3")
        st.metric("Status", "—")

st.markdown("---")
st.header("Multi-Agent Review")

rev_col1, rev_col2, rev_col3, rev_col4 = st.columns(4)

with rev_col1:
    st.subheader("Security")
    with st.container(border=True):
        st.caption("Secrets, injections, unsafe patterns")
        st.metric("Score", "—")

with rev_col2:
    st.subheader("Performance")
    with st.container(border=True):
        st.caption("Loops, memory, redundant ops")
        st.metric("Score", "—")

with rev_col3:
    st.subheader("Code Quality")
    with st.container(border=True):
        st.caption("Readability, naming, structure")
        st.metric("Score", "—")

with rev_col4:
    st.subheader("Test Coverage")
    with st.container(border=True):
        st.caption("Edge cases, assertions, gaps")
        st.metric("Score", "—")

st.subheader("Run Full Review Pipeline")
with st.container(border=True):
    rev_repo = st.text_input(
        "Repository name",
        key="rev_repo",
        placeholder="e.g., my-org-my-repo",
    )
    rev_logs = st.text_area("CI/CD logs", key="rev_logs", height=100)
    if st.button("Run Full Review") and rev_repo and rev_logs:
        st.session_state.rev_repo = rev_repo
        st.session_state.rev_logs = rev_logs

    if "rev_repo" in st.session_state:
        st.success(f"Review triggered for `{st.session_state.rev_repo}` via `POST /review/run`.")

st.subheader("Final Recommendation")
with st.container(border=True):
    if "rev_repo" in st.session_state:
        st.caption("Recommendation will appear here after backend processing.")
        st.metric("Overall Score", "—")
        st.metric("Recommendation", "—")
    else:
        st.info("Run the full review pipeline to see the final recommendation.")

st.markdown("---")
st.header("Pull Request Automation")

pr_col1, pr_col2 = st.columns([1, 1])

with pr_col1:
    st.subheader("Repository & Logs")
    with st.container(border=True):
        pr_repo = st.text_input(
            "Repository name",
            key="pr_repo",
            placeholder="e.g., owner/repo",
        )
        pr_logs = st.text_area("CI/CD logs", key="pr_logs", height=100)

with pr_col2:
    st.subheader("Options")
    with st.container(border=True):
        pr_dry_run = st.checkbox("Dry Run (safe mode)", value=True, key="pr_dry_run")
        pr_approved = st.checkbox("Approved (allow real PR)", value=False, key="pr_approved")
        if pr_approved and not pr_dry_run:
            st.warning("REAL MODE — PR will be created on GitHub")
        elif not pr_dry_run:
            st.info("Uncheck Dry Run and check Approved to create a real PR.")

st.subheader("Generate & Create PR")
with st.container(border=True):
    pr_cols = st.columns([1, 3])
    with pr_cols[0]:
        if st.button("Create Pull Request") and pr_repo and pr_logs:
            st.session_state.pr_repo = pr_repo
            st.session_state.pr_logs = pr_logs
            st.session_state.pr_dry_run = pr_dry_run
            st.session_state.pr_approved = pr_approved

    if "pr_repo" in st.session_state:
        mode = "Dry Run" if st.session_state.pr_dry_run else "Real"
        st.success(f"PR creation triggered for `{st.session_state.pr_repo}` ({mode}) via `POST /pr/create`.")

st.subheader("PR Details")
prd_col1, prd_col2 = st.columns(2)

with prd_col1:
    with st.container(border=True):
        st.caption("Branch")
        st.metric("Name", "—")
        st.caption("Commit Message")
        st.text("—", disabled=True)

with prd_col2:
    with st.container(border=True):
        st.caption("PR Status")
        st.metric("Status", "—")
        st.caption("PR URL")
        st.text("—", disabled=True)

st.subheader("Generated PR Content")
with st.container(border=True):
    st.text_input("PR Title", value="—", disabled=True, key="pr_title_display")
    st.text_area("PR Description", value="—", height=120, disabled=True, key="pr_desc_display")

st.markdown("---")
st.header("Benchmark Dashboard")

dash_tab1, dash_tab2, dash_tab3, dash_tab4, dash_tab5, dash_tab6 = st.tabs(
    ["System Overview", "Repository Analytics", "Retry Analytics", "Validation Analytics", "Review Analytics", "PR Analytics"]
)

with dash_tab1:
    st.subheader("System Overview")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Runs", "—")
    with c2:
        st.metric("Success Rate", "—")
    with c3:
        st.metric("Avg Retries", "—")
    with c4:
        st.metric("Avg Confidence", "—")
    st.caption("Data available from `GET /dashboard/summary`.")

with dash_tab2:
    st.subheader("Repository Analytics")
    st.caption("Per-repository metrics available from `GET /dashboard/repositories`.")
    st.info("Repository-level statistics will appear here after workflow runs.")

with dash_tab3:
    st.subheader("Retry Analytics")
    rc1, rc2, rc3 = st.columns(3)
    with rc1:
        st.metric("Total Retries", "—")
    with rc2:
        st.metric("Avg Retries/Run", "—")
    with rc3:
        st.metric("Retry Distribution", "—")
    st.caption("Retry data available from `GET /dashboard/metrics`.")

with dash_tab4:
    st.subheader("Validation Analytics")
    vc1, vc2 = st.columns(2)
    with vc1:
        st.metric("Validation Pass Rate", "—")
    with vc2:
        st.metric("Total Attempts", "—")
    st.caption("Validation data available from `GET /dashboard/charts/validation-results`.")

with dash_tab5:
    st.subheader("Review Analytics")
    rvc1, rvc2, rvc3, rvc4, rvc5 = st.columns(5)
    with rvc1:
        st.metric("Security", "—")
    with rvc2:
        st.metric("Performance", "—")
    with rvc3:
        st.metric("Quality", "—")
    with rvc4:
        st.metric("Coverage", "—")
    with rvc5:
        st.metric("Overall", "—")
    st.caption("Review data available from `GET /dashboard/charts/review-scores`.")

with dash_tab6:
    st.subheader("PR Analytics")
    pc1, pc2 = st.columns(2)
    with pc1:
        st.metric("Total PRs", "—")
    with pc2:
        st.metric("Real PRs", "—")
    st.caption("PR statistics available from `GET /dashboard/charts/pr-statistics`.")

st.markdown("---")
st.caption("Built with FastAPI, LangChain, Streamlit & DeepSeek")
