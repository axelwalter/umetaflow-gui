import streamlit as st
from pathlib import Path
from src.common.common import page_setup

# The rest of the page can, but does not have to be changed
params = page_setup()

flag_file = Path(st.session_state["workspace"], "umetaflow-expert-flag")

def update_expert_mode(flag_file):
    if st.session_state["umetaflow-expert-mode"]:
        flag_file.touch()
    else:
        flag_file.unlink(missing_ok=True)

expert = st.toggle(
    "⚙️ **Expert Mode**",
    flag_file.exists(),
    key="umetaflow-expert-mode",
    on_change=update_expert_mode,
    args=(flag_file,)
)

if flag_file.exists():
    from src.UmetaFlowTOPPWorkflowExpert import Workflow
else:
    from src.UmetaFlowTOPPWorkflow import Workflow


wf = Workflow()

wf.show_parameter_section()
