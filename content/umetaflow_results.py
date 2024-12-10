import streamlit as st
from src.common.common import page_setup
from src.UmetaFlowTOPPWorkflowExpert import Workflow

# The rest of the page can, but does not have to be changed
params = page_setup()

wf = Workflow()

wf.show_results_section()
