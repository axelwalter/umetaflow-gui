import streamlit as st
from src.common.common import page_setup
from src.UmetaFlowTOPPWorkflow import Workflow

# The rest of the page can, but does not have to be changed
params = page_setup()

wf = Workflow()

wf.show_parameter_section()

