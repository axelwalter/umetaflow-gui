import streamlit as st
from pathlib import Path
from src.common.common import page_setup
from src.UmetaFlowTOPPWorkflow import Workflow

# The rest of the page can, but does not have to be changed
params = page_setup()

flag_file = Path(st.session_state["workspace"], "umetaflow-expert-flag.txt")

def update_expert_mode():
    if st.session_state["umetaflow-expert-mode"]:
        flag_file.touch()
    else:
        flag_file.unlink(missing_ok=True)

st.toggle(
    "⚠️ **Expert Mode**",
    flag_file.exists(),
    key="umetaflow-expert-mode",
    on_change=update_expert_mode
)

wf = Workflow(st.session_state["workspace"])

wf.show_parameter_section()
