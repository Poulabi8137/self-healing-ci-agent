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
st.caption("Built with FastAPI, LangChain, Streamlit & DeepSeek")
