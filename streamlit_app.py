import json
import requests
import streamlit as st


st.set_page_config(
    page_title="AI App Builder",
    page_icon="🤖",
    layout="wide",
)


st.title("🤖 AI App Builder")
st.caption("AI Plan → Approval → Apply → Validation")


# ---------------------------------------------------------
# Backend URL
# ---------------------------------------------------------
st.sidebar.header("⚙️ Backend")

backend_url = st.sidebar.text_input(
    "FastAPI Backend URL",
    value=st.session_state.get("backend_url", ""),
    placeholder="https://your-backend-url.com",
)

st.session_state["backend_url"] = backend_url

backend_url = backend_url.rstrip("/")


def api_request(method, endpoint, data=None):
    """Call the existing FastAPI backend."""
    if not backend_url:
        st.error("முதலில் Backend URL கொடுக்கவும்.")
        return None

    try:
        url = f"{backend_url}{endpoint}"

        if method == "GET":
            response = requests.get(url, timeout=60)
        else:
            response = requests.post(
                url,
                json=data,
                timeout=120,
            )

        try:
            result = response.json()
        except Exception:
            result = response.text

        if response.status_code >= 400:
            st.error(f"HTTP {response.status_code}")
            st.code(
                json.dumps(result, indent=2, ensure_ascii=False)
                if isinstance(result, dict)
                else str(result)
            )
            return None

        return result

    except requests.exceptions.Timeout:
        st.error("Backend response timeout.")
        return None

    except requests.exceptions.ConnectionError:
        st.error("Backend-ஐ connect செய்ய முடியவில்லை.")
        return None

    except Exception as e:
        st.error(f"Error: {e}")
        return None


# ---------------------------------------------------------
# Session state
# ---------------------------------------------------------
if "approval_id" not in st.session_state:
    st.session_state["approval_id"] = ""

if "last_plan" not in st.session_state:
    st.session_state["last_plan"] = None


# ---------------------------------------------------------
# Backend status
# ---------------------------------------------------------
st.header("1️⃣ Backend Status")

if st.button("🔍 Check Backend", use_container_width=True):
    result = api_request("GET", "/")

    if result:
        st.success("Backend Online")
        st.json(result)


# ---------------------------------------------------------
# Project
# ---------------------------------------------------------
st.header("2️⃣ Project")

project_path = st.text_input(
    "Project Path",
    value="./projects/default",
)

if st.button("📁 Create Project", use_container_width=True):

    result = api_request(
        "POST",
        "/api/project",
        {
            "project_path": project_path
        },
    )

    if result:
        st.success("Project created")
        st.json(result)


# ---------------------------------------------------------
# AI Command
# ---------------------------------------------------------
st.header("3️⃣ AI Command")

command = st.text_area(
    "What should AI build/change?",
    placeholder=(
        "Example:\n"
        "Create a simple expense management application "
        "with login, dashboard and expense tracking."
    ),
    height=140,
)


if st.button("🧠 Create AI Plan", use_container_width=True):

    if not command.strip():
        st.warning("AI command கொடுக்கவும்.")

    elif not project_path.strip():
        st.warning("Project path கொடுக்கவும்.")

    else:

        with st.spinner("AI plan உருவாக்கப்படுகிறது..."):

            result = api_request(
                "POST",
                "/api/command",
                {
                    "command": command,
                    "project_path": project_path,
                },
            )

        if result:

            st.session_state["last_plan"] = result

            approval_id = result.get("approval_id", "")

            if approval_id:
                st.session_state["approval_id"] = approval_id

            st.success("AI Plan உருவாக்கப்பட்டது.")

            if approval_id:
                st.info(f"Approval ID: {approval_id}")

            with st.expander("📋 AI Plan", expanded=True):
                st.json(result)


# ---------------------------------------------------------
# Approval
# ---------------------------------------------------------
st.header("4️⃣ Approval")

approval_id = st.text_input(
    "Approval ID",
    value=st.session_state["approval_id"],
)

st.session_state["approval_id"] = approval_id


col1, col2 = st.columns(2)


with col1:

    if st.button(
        "🔎 Check Approval",
        use_container_width=True,
    ):

        if not approval_id:
            st.warning("Approval ID இல்லை.")

        else:

            result = api_request(
                "GET",
                f"/api/approval/{approval_id}",
            )

            if result:
                st.json(result)


with col2:

    if st.button(
        "✅ Approve",
        use_container_width=True,
    ):

        if not approval_id:
            st.warning("Approval ID இல்லை.")

        else:

            result = api_request(
                "POST",
                "/api/approve",
                {
                    "approval_id": approval_id
                },
            )

            if result:
                st.success("Plan Approved")
                st.json(result)


# ---------------------------------------------------------
# Apply
# ---------------------------------------------------------
st.header("5️⃣ Apply Changes")

if st.button(
    "🚀 Apply Approved Plan",
    use_container_width=True,
):

    if not approval_id:
        st.warning("Approval ID இல்லை.")

    else:

        with st.spinner("Changes apply செய்யப்படுகிறது..."):

            result = api_request(
                "POST",
                "/api/apply",
                {
                    "approval_id": approval_id,
                    "project_path": project_path,
                },
            )

        if result:
            st.success("Changes applied successfully.")
            st.json(result)


# ---------------------------------------------------------
# Validation
# ---------------------------------------------------------
st.header("6️⃣ Validation")

if st.button(
    "🧪 Validate Project",
    use_container_width=True,
):

    with st.spinner("Validation running..."):

        result = api_request(
            "POST",
            "/api/validate",
            {
                "project_path": project_path
            },
        )

    if result:
        st.success("Validation completed.")
        st.json(result)


# ---------------------------------------------------------
# Result
# ---------------------------------------------------------
st.header("7️⃣ Last Result")

if st.session_state["last_plan"]:

    st.json(st.session_state["last_plan"])

else:

    st.info("இன்னும் AI Plan உருவாக்கப்படவில்லை.")
