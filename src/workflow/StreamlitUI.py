import streamlit as st
import pyopenms as poms
from pathlib import Path
import shutil
import subprocess
from typing import Any, Union, List, Literal
import json
import os
import sys
import importlib.util
import time
from io import BytesIO
import zipfile
from datetime import datetime
from streamlit_js_eval import streamlit_js_eval


from src.common.common import (
    OS_PLATFORM,
    TK_AVAILABLE,
    tk_directory_dialog,
    tk_file_dialog,
)


class StreamlitUI:
    """
    Provides an interface for Streamlit applications to handle file uploads,
    input selection, and parameter management for analysis workflows. It includes
    methods for uploading files, selecting input files from available ones, and
    generating various input widgets dynamically based on the specified parameters.
    """

    # Methods for Streamlit UI components
    def __init__(self, workflow_dir, logger, executor, parameter_manager):
        self.workflow_dir = workflow_dir
        self.logger = logger
        self.executor = executor
        self.parameter_manager = parameter_manager
        self.params = self.parameter_manager.get_parameters_from_json()

    @st.fragment
    def upload_widget(
        self,
        key: str,
        file_types: Union[str, List[str]],
        name: str = "",
        fallback: Union[List, str] = None,
    ) -> None:
        """
        Handles file uploads through the Streamlit interface, supporting both direct
        uploads and local directory copying for specified file types. It allows for
        specifying fallback files to ensure essential files are available.

        Args:
            key (str): A unique identifier for the upload component.
            file_types (Union[str, List[str]]): Expected file type(s) for the uploaded files.
            name (str, optional): Display name for the upload component. Defaults to the key if not provided.
            fallback (Union[List, str], optional): Default files to use if no files are uploaded.
        """
        files_dir = Path(self.workflow_dir, "input-files", key)

        # create the files dir
        files_dir.mkdir(exist_ok=True, parents=True)

        if fallback is not None:
            # check if only fallback files are in files_dir, if yes, reset the directory before adding new files
            if [Path(f).name for f in Path(files_dir).iterdir()] == [
                Path(f).name for f in fallback
            ]:
                shutil.rmtree(files_dir)
                files_dir.mkdir()

        if not name:
            name = key.replace("-", " ")

        c1, c2 = st.columns(2)
        c1.markdown("**Upload file(s)**")

        if st.session_state.location == "local":
            c2_text, c2_checkbox = c2.columns([1.5, 1], gap="large")
            c2_text.markdown("**OR add files from local folder**")
            use_copy = c2_checkbox.checkbox(
                "Make a copy of files",
                key=f"{key}-copy_files",
                value=True,
                help="Create a copy of files in workspace.",
            )
        else:
            use_copy = True

        # Convert file_types to a list if it's a string
        if isinstance(file_types, str):
            file_types = [file_types]

        if use_copy:
            with c1.form(f"{key}-upload", clear_on_submit=True):
                # Streamlit file uploader accepts file types as a list or None
                file_type_for_uploader = file_types if file_types else None

                files = st.file_uploader(
                    f"{name}",
                    accept_multiple_files=(st.session_state.location == "local"),
                    type=file_type_for_uploader,
                    label_visibility="collapsed",
                )
                if st.form_submit_button(
                    f"Add **{name}**", use_container_width=True, type="primary"
                ):
                    if files:
                        # in case of online mode a single file is returned -> put in list
                        if not isinstance(files, list):
                            files = [files]
                        for f in files:
                            # Check if file type is in the list of accepted file types
                            if f.name not in [
                                f.name for f in files_dir.iterdir()
                            ] and any(f.name.endswith(ft) for ft in file_types):
                                with open(Path(files_dir, f.name), "wb") as fh:
                                    fh.write(f.getbuffer())
                        st.success("Successfully added uploaded files!")
                    else:
                        st.error("Nothing to add, please upload file.")
        else:
            # Create a temporary file to store the path to the local directories
            external_files = Path(files_dir, "external_files.txt")
            # Check if the file exists, if not create it
            if not external_files.exists():
                external_files.touch()
            c1.write("\n")
            with c1.container(border=True):
                dialog_button = st.button(
                    rf"$\textsf{{\Large 📁 Add }} \textsf{{ \Large \textbf{{{name}}} }}$",
                    type="primary",
                    use_container_width=True,
                    key="local_browse_single",
                    help="Browse for your local MS data files.",
                    disabled=not TK_AVAILABLE,
                )

                # Tk file dialog requires file types to be a list of tuples
                if isinstance(file_types, str):
                    tk_file_types = [(f"{file_types}", f"*.{file_types}")]
                elif isinstance(file_types, list):
                    tk_file_types = [(f"{ft}", f"*.{ft}") for ft in file_types]
                else:
                    raise ValueError("'file_types' must be either of type str or list")

                if dialog_button:
                    local_files = tk_file_dialog(
                        "Select your local MS data files",
                        tk_file_types,
                        st.session_state["previous_dir"],
                    )
                    if local_files:
                        my_bar = st.progress(0)
                        for i, f in enumerate(local_files):
                            with open(external_files, "a") as f_handle:
                                f_handle.write(f"{f}\n")
                        my_bar.empty()
                        st.success("Successfully added files!")

                        st.session_state["previous_dir"] = Path(local_files[0]).parent

        # Local file upload option: via directory path
        if st.session_state.location == "local":
            # c2_text, c2_checkbox = c2.columns([1.5, 1], gap="large")
            # c2_text.markdown("**OR add files from local folder**")
            # use_copy = c2_checkbox.checkbox("Make a copy of files", key=f"{key}-copy_files", value=True, help="Create a copy of files in workspace.")
            with c2.container(border=True):
                st_cols = st.columns([0.05, 0.55], gap="small")
                with st_cols[0]:
                    st.write("\n")
                    st.write("\n")
                    dialog_button = st.button(
                        "📁",
                        key=f"local_browse_{key}",
                        help="Browse for your local directory with MS data.",
                        disabled=not TK_AVAILABLE,
                    )
                    if dialog_button:
                        st.session_state["local_dir"] = tk_directory_dialog(
                            "Select directory with your MS data",
                            st.session_state["previous_dir"],
                        )
                        st.session_state["previous_dir"] = st.session_state["local_dir"]

                with st_cols[1]:
                    local_dir = st.text_input(
                        f"path to folder with **{name}** files",
                        key=f"path_to_folder_{key}",
                        value=st.session_state["local_dir"],
                    )

                if c2.button(
                    f"Add **{name}** files from local folder",
                    use_container_width=True,
                    key=f"add_files_from_local_{key}",
                    help="Add files from local directory.",
                ):
                    files = []
                    local_dir = Path(
                        local_dir
                    ).expanduser()  # Expand ~ to full home directory path

                    for ft in file_types:
                        # Search for both files and directories with the specified extension
                        for path in local_dir.iterdir():
                            if path.is_file() and path.name.endswith(f".{ft}"):
                                files.append(path)
                            elif path.is_dir() and path.name.endswith(f".{ft}"):
                                files.append(path)

                    if not files:
                        st.warning(
                            f"No files with type **{', '.join(file_types)}** found in specified folder."
                        )
                    else:
                        my_bar = st.progress(0)
                        for i, f in enumerate(files):
                            my_bar.progress((i + 1) / len(files))
                            if use_copy:
                                if os.path.isfile(f):
                                    shutil.copy(f, Path(files_dir, f.name))
                                elif os.path.isdir(f):
                                    shutil.copytree(
                                        f, Path(files_dir, f.name), dirs_exist_ok=True
                                    )
                            else:
                                # Write the path to the local directories to the file
                                with open(external_files, "a") as f_handle:
                                    f_handle.write(f"{f}\n")
                        my_bar.empty()
                        st.success("Successfully copied files!")

            if not TK_AVAILABLE:
                c2.warning(
                    "**Warning**: Failed to import tkinter, either it is not installed, or this is being called from a cloud context. "
                    "This function is not available in a Streamlit Cloud context. "
                    "You will have to manually enter the path to the folder with the MS files."
                )

            if not use_copy:
                c2.warning(
                    "**Warning**: You have deselected the `Make a copy of files` option. "
                    "This **_assumes you know what you are doing_**. "
                    "This means that the original files will be used instead. "
                )

        if fallback and not any([f for f in Path(files_dir).iterdir() if f.name != "external_files.txt"]):
            if isinstance(fallback, str):
                fallback = [fallback]
            for f in fallback:
                c1, _ = st.columns(2)
                if not Path(files_dir, f).exists():
                    shutil.copy(f, Path(files_dir, Path(f).name))
            current_files = [f.name for f in files_dir.iterdir() if f.name != "external_files.txt"]
            c1.warning("**No data yet. Using example data file(s).**")
        else:
            if files_dir.exists():
                current_files = [
                    f.name
                    for f in files_dir.iterdir()
                    if "external_files.txt" not in f.name
                ]

                # Check if local files are available
                external_files = Path(
                    self.workflow_dir, "input-files", key, "external_files.txt"
                )

                if external_files.exists():
                    with open(external_files, "r") as f:
                        external_files_list = f.read().splitlines()
                    # Only make files available that still exist
                    current_files += [
                        f"(local) {Path(f).name}"
                        for f in external_files_list
                        if os.path.exists(f)
                    ]
            else:
                current_files = []

        if files_dir.exists() and not any(files_dir.iterdir()):
            shutil.rmtree(files_dir)

        c1, _ = st.columns(2)
        if current_files:
            c1.info(f"Current **{name}** files:\n\n" + "\n\n".join(current_files))
            if c1.button(
                f"🗑️ Clear **{name}** files.",
                use_container_width=True,
                key=f"remove-files-{key}",
            ):
                shutil.rmtree(files_dir)
                if key in self.params:
                    del self.params[key]
                with open(
                    self.parameter_manager.params_file, "w", encoding="utf-8"
                ) as f:
                    json.dump(self.params, f, indent=4)
                st.rerun()
        elif not fallback:
            st.warning(f"No **{name}** files!")

    @st.fragment
    def select_input_file(
        self,
        key: str,
        name: str = "",
        multiple: bool = False,
        display_file_path: bool = False,
    ) -> None:
        """
        Presents a widget for selecting input files from those that have been uploaded.
        Allows for single or multiple selections.

        Args:
            key (str): A unique identifier related to the specific input files.
            name (str, optional): The display name for the selection widget. Defaults to the key if not provided.
            multiple (bool, optional): If True, allows multiple files to be selected.
            display_file_path (bool, optional): If True, displays the full file path in the selection widget.
        """
        if not name:
            name = f"**{key}**"
        path = Path(self.workflow_dir, "input-files", key)
        if not path.exists():
            st.warning(f"No **{name}** files!")
            return
        options = [str(f) for f in path.iterdir() if "external_files.txt" not in str(f)]

        # Check if local files are available
        external_files = Path(
            self.workflow_dir, "input-files", key, "external_files.txt"
        )

        if external_files.exists():
            with open(external_files, "r") as f:
                external_files_list = f.read().splitlines()
            # Only make files available that still exist
            options += [f for f in external_files_list if os.path.exists(f)]
        if (key in self.params.keys()) and isinstance(self.params[key], list):
            self.params[key] = [f for f in self.params[key] if f in options]

        widget_type = "multiselect" if multiple else "selectbox"
        self.input_widget(
            key,
            name=name,
            widget_type=widget_type,
            options=options,
            display_file_path=display_file_path,
        )

    @st.fragment
    def input_widget(
        self,
        key: str,
        default: Any = None,
        name: str = "input widget",
        help: str = None,
        widget_type: str = "auto",  # text, textarea, number, selectbox, slider, checkbox, multiselect
        options: List[str] = None,
        min_value: Union[int, float] = None,
        max_value: Union[int, float] = None,
        step_size: Union[int, float] = 1,
        display_file_path: bool = False,
    ) -> None:
        """
        Creates and displays a Streamlit widget for user input based on specified
        parameters. Supports a variety of widget types including text input, number
        input, select boxes, and more. Default values will be read in from parameters
        if they exist. The key is modified to be recognized by the ParameterManager class
        as a custom parameter (distinct from TOPP tool parameters).

        Args:
            key (str): Unique identifier for the widget.
            default (Any, optional): Default value for the widget.
            name (str, optional): Display name of the widget.
            help (str, optional): Help text to display alongside the widget.
            widget_type (str, optional): Type of widget to create ('text', 'textarea',
                                         'number', 'selectbox', 'slider', 'checkbox',
                                         'multiselect', 'password', or 'auto').
            options (List[str], optional): Options for select/multiselect widgets.
            min_value (Union[int, float], optional): Minimum value for number/slider widgets.
            max_value (Union[int, float], optional): Maximum value for number/slider widgets.
            step_size (Union[int, float], optional): Step size for number/slider widgets.
            display_file_path (bool, optional): Whether to display the full file path for file options.
        """

        def format_files(input: Any) -> List[str]:
            if not display_file_path and Path(input).exists():
                return Path(input).name
            else:
                return input

        if key in self.params.keys():
            value = self.params[key]
        else:
            value = default
            # catch case where options are given but default is None
            if options is not None and value is None:
                if widget_type == "multiselect":
                    value = []
                elif widget_type == "selectbox":
                    value = options[0]

        key = f"{self.parameter_manager.param_prefix}{key}"

        if widget_type == "text":
            st.text_input(name, value=value, key=key, help=help)

        elif widget_type == "textarea":
            st.text_area(name, value=value, key=key, help=help)

        elif widget_type == "number":
            number_type = float if isinstance(value, float) else int
            step_size = number_type(step_size)
            if min_value is not None:
                min_value = number_type(min_value)
            if max_value is not None:
                max_value = number_type(max_value)
            help = str(help)
            st.number_input(
                name,
                min_value=min_value,
                max_value=max_value,
                value=value,
                step=step_size,
                format=None,
                key=key,
                help=help,
            )

        elif widget_type == "checkbox":
            st.checkbox(name, value=value, key=key, help=help)

        elif widget_type == "selectbox":
            if options is not None:
                st.selectbox(
                    name,
                    options=options,
                    index=options.index(value) if value in options else 0,
                    key=key,
                    format_func=format_files,
                    help=help,
                )
            else:
                st.warning(f"Select widget '{name}' requires options parameter")

        elif widget_type == "multiselect":
            if options is not None:
                st.multiselect(
                    name,
                    options=options,
                    default=value,
                    key=key,
                    format_func=format_files,
                    help=help,
                )
            else:
                st.warning(f"Select widget '{name}' requires options parameter")

        elif widget_type == "slider":
            if min_value is not None and max_value is not None:
                slider_type = float if isinstance(value, float) else int
                step_size = slider_type(step_size)
                if min_value is not None:
                    min_value = slider_type(min_value)
                if max_value is not None:
                    max_value = slider_type(max_value)
                st.slider(
                    name,
                    min_value=min_value,
                    max_value=max_value,
                    value=value,
                    step=step_size,
                    key=key,
                    format=None,
                    help=help,
                )
            else:
                st.warning(
                    f"Slider widget '{name}' requires min_value and max_value parameters"
                )

        elif widget_type == "password":
            st.text_input(name, value=value, type="password", key=key, help=help)

        elif widget_type == "auto":
            # Auto-determine widget type based on value
            if isinstance(value, bool):
                st.checkbox(name, value=value, key=key, help=help)
            elif isinstance(value, (int, float)):
                self.input_widget(
                    key,
                    value,
                    widget_type="number",
                    name=name,
                    min_value=min_value,
                    max_value=max_value,
                    step_size=step_size,
                    help=help,
                )
            elif (isinstance(value, str) or value == None) and options is not None:
                self.input_widget(
                    key,
                    value,
                    widget_type="selectbox",
                    name=name,
                    options=options,
                    help=help,
                )
            elif isinstance(value, list) and options is not None:
                self.input_widget(
                    key,
                    value,
                    widget_type="multiselect",
                    name=name,
                    options=options,
                    help=help,
                )
            elif isinstance(value, bool):
                self.input_widget(
                    key, value, widget_type="checkbox", name=name, help=help
                )
            else:
                self.input_widget(key, value, widget_type="text", name=name, help=help)

        else:
            st.error(f"Unsupported widget type '{widget_type}'")
        self.parameter_manager.save_parameters()

    @st.fragment
    def input_TOPP(
        self,
        topp_tool_name: str,
        num_cols: int = 4,
        exclude_parameters: List[str] = [],
        include_parameters: List[str] = [],
        display_tool_name: bool = True,
        display_subsections: bool = True,
        display_subsection_tabs: bool = False,
        custom_defaults: dict = {},
    ) -> None:
        """
        Generates input widgets for TOPP tool parameters dynamically based on the tool's
        .ini file. Supports excluding specific parameters and adjusting the layout.
        File input and output parameters are excluded.

        Args:
            topp_tool_name (str): The name of the TOPP tool for which to generate inputs.
            num_cols (int, optional): Number of columns to use for the layout. Defaults to 3.
            exclude_parameters (List[str], optional): List of parameter names to exclude from the widget. Defaults to an empty list.
            include_parameters (List[str], optional): List of parameter names to include in the widget. Defaults to an empty list.
            display_tool_name (bool, optional): Whether to display the TOPP tool name. Defaults to True.
            display_subsections (bool, optional): Whether to split parameters into subsections based on the prefix. Defaults to True.
            display_subsection_tabs (bool, optional): Whether to display main subsections in separate tabs (if more than one main section). Defaults to False.
            custom_defaults (dict, optional): Dictionary of custom defaults to use. Defaults to an empty dict.
        """

        if not display_subsections:
            display_subsection_tabs = False
        if display_subsection_tabs:
            display_subsections = True

        # write defaults ini files
        ini_file_path = Path(self.parameter_manager.ini_dir, f"{topp_tool_name}.ini")
        if not ini_file_path.exists():
            try:
                subprocess.call([topp_tool_name, "-write_ini", str(ini_file_path)])
            except FileNotFoundError:
                st.error(f"TOPP tool **'{topp_tool_name}'** not found.")
                return
            # update custom defaults if necessary
            if custom_defaults:
                param = poms.Param()
                poms.ParamXMLFile().load(str(ini_file_path), param)
                for key, value in custom_defaults.items():
                    encoded_key = f"{topp_tool_name}:1:{key}".encode()
                    if encoded_key in param.keys():
                        param.setValue(encoded_key, value)
                poms.ParamXMLFile().store(str(ini_file_path), param)

        # read into Param object
        param = poms.Param()
        poms.ParamXMLFile().load(str(ini_file_path), param)
        if include_parameters:
            valid_keys = [
                key
                for key in param.keys()
                if any([k.encode() in key for k in include_parameters])
            ]
        else:
            excluded_keys = [
                "log",
                "debug",
                "threads",
                "no_progress",
                "force",
                "version",
                "test",
            ] + exclude_parameters
            valid_keys = [
                key
                for key in param.keys()
                if not (
                    b"input file" in param.getTags(key)
                    or b"output file" in param.getTags(key)
                    or any([k.encode() in key for k in excluded_keys])
                )
            ]
        params = []
        for key in valid_keys:
            entry = param.getEntry(key)
            p = {
                "name": entry.name.decode(),
                "key": key,
                "value": entry.value,
                "valid_strings": [v.decode() for v in entry.valid_strings],
                "description": entry.description.decode(),
                "advanced": (b"advanced" in param.getTags(key)),
                "section_description": param.getSectionDescription(
                    ":".join(key.decode().split(":")[:-1])
                ),
            }
            # Parameter sections and subsections as string (e.g. "section:subsection")
            if display_subsections:
                p["sections"] = ":".join(
                    p["key"].decode().split(":1:")[1].split(":")[:-1]
                )
            params.append(p)

        # for each parameter in params_decoded
        # if a parameter with custom default value exists, use that value
        # else check if the parameter is already in self.params, if yes take the value from self.params
        for p in params:
            name = p["key"].decode().split(":1:")[1]
            if topp_tool_name in self.params:
                if name in self.params[topp_tool_name]:
                    p["value"] = self.params[topp_tool_name][name]
                elif name in custom_defaults:
                    p["value"] = custom_defaults[name]
            elif name in custom_defaults:
                p["value"] = custom_defaults[name]

        # Split into subsections if required
        param_sections = {}
        section_descriptions = {}
        if display_subsections:
            for p in params:
                # Skip adavnaced parameters if not selected
                if not st.session_state["advanced"] and p["advanced"]:
                    continue
                # Add section description to section_descriptions dictionary if it exists
                if p["section_description"]:
                    section_descriptions[p["sections"]] = p["section_description"]
                # Add parameter to appropriate section in param_sections dictionary
                if not p["sections"]:
                    p["sections"] = "General"
                if p["sections"] in param_sections:
                    param_sections[p["sections"]].append(p)
                else:
                    param_sections[p["sections"]] = [p]
        else:
            # Simply put all parameters in "all" section if no subsections required
            param_sections["all"] = params

        # Display tool name if required
        if display_tool_name:
            st.markdown(f"**{topp_tool_name}**")

        tab_names = [k for k in param_sections.keys() if ":" not in k]
        tabs = None
        if tab_names and display_subsection_tabs:
            tabs = st.tabs([k for k in param_sections.keys() if ":" not in k])

        # Show input widgets
        def show_subsection_header(section: str, display_subsections: bool):
            # Display section name and help text (section description) if required
            if section and display_subsections:
                parts = section.split(":")
                st.markdown(
                    ":".join(parts[:-1])
                    + (":" if len(parts) > 1 else "")
                    + f"**{parts[-1]}**",
                    help=(
                        section_descriptions[section]
                        if section in section_descriptions
                        else None
                    ),
                )

        def display_TOPP_params(params: dict, num_cols):
            """Displays individual TOPP parameters in given number of columns"""
            cols = st.columns(num_cols)
            i = 0
            for p in params:
                # get key and name
                key = f"{self.parameter_manager.topp_param_prefix}{p['key'].decode()}"
                name = p["name"]
                try:
                    # sometimes strings with newline, handle as list
                    if isinstance(p["value"], str) and "\n" in p["value"]:
                        p["value"] = p["value"].split("\n")
                    # bools
                    if isinstance(p["value"], bool):
                        cols[i].markdown("##")
                        cols[i].checkbox(
                            name,
                            value=(
                                (p["value"] == "true")
                                if type(p["value"]) == str
                                else p["value"]
                            ),
                            help=p["description"],
                            key=key,
                        )

                    # strings
                    elif isinstance(p["value"], str):
                        # string options
                        if p["valid_strings"]:
                            cols[i].selectbox(
                                name,
                                options=p["valid_strings"],
                                index=p["valid_strings"].index(p["value"]),
                                help=p["description"],
                                key=key,
                            )
                        else:
                            cols[i].text_input(
                                name, value=p["value"], help=p["description"], key=key
                            )

                    # ints
                    elif isinstance(p["value"], int):
                        cols[i].number_input(
                            name, value=int(p["value"]), help=p["description"], key=key
                        )

                    # floats
                    elif isinstance(p["value"], float):
                        cols[i].number_input(
                            name,
                            value=float(p["value"]),
                            step=1.0,
                            help=p["description"],
                            key=key,
                        )

                    # lists
                    elif isinstance(p["value"], list):
                        p["value"] = [
                            v.decode() if isinstance(v, bytes) else v
                            for v in p["value"]
                        ]
                        valid_entries_info = ''
                        if len(p['valid_strings']) > 0:
                            valid_entries_info = (
                                " Valid entries are: "
                                + ', '.join(sorted(p['valid_strings']))
                            )

                        cols[i].text_area(
                            name,
                            value="\n".join([str(val) for val in p["value"]]),
                            help=p["description"] + " Separate entries using the \"Enter\" key." + valid_entries_info,
                            key=key,
                        )

                    # increment number of columns, create new cols object if end of line is reached
                    i += 1
                    if i == num_cols:
                        i = 0
                        cols = st.columns(num_cols)
                except Exception as e:
                    cols[i].error(f"Error in parameter **{p['name']}**.")
                    print('Error parsing "' + p["name"] + '": ' + str(e))


        for section, params in param_sections.items():
            if tabs is None:
                show_subsection_header(section, display_subsections)
                display_TOPP_params(params, num_cols)
            else:
                tab_name = section.split(":")[0]
                with tabs[tab_names.index(tab_name)]:
                    show_subsection_header(section, display_subsections)
                    display_TOPP_params(params, num_cols)
        
        self.parameter_manager.save_parameters()
            

    @st.fragment
    def input_python(
        self,
        script_file: str,
        num_cols: int = 3,
    ) -> None:
        """
        Dynamically generates and displays input widgets based on the DEFAULTS
        dictionary defined in a specified Python script file.

        For each entry in the DEFAULTS dictionary, an input widget is displayed,
        allowing the user to specify values for the parameters defined in the
        script. The widgets are arranged in a grid with a specified number of
        columns. Parameters can be marked as hidden or advanced within the DEFAULTS
        dictionary; hidden parameters are not displayed, and advanced parameters
        are displayed only if the user has selected to view advanced options.

        Args:
        script_file (str): The file name or path to the Python script containing
                           the DEFAULTS dictionary. If the path is omitted, the method searches in
                           src/python-tools/'.
        num_cols (int, optional): The number of columns to use for displaying input widgets. Defaults to 3.
        """

        # Check if script file exists (can be specified without path and extension)
        # default location: src/python-tools/script_file
        if not script_file.endswith(".py"):
            script_file += ".py"
        path = Path(script_file)
        if not path.exists():
            path = Path("src", "python-tools", script_file)
            if not path.exists():
                st.error("Script file not found.")
        # load DEFAULTS from file
        if path.parent not in sys.path:
            sys.path.append(str(path.parent))
        spec = importlib.util.spec_from_file_location(path.stem, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        defaults = getattr(module, "DEFAULTS", None)
        if defaults is None:
            st.error("No DEFAULTS found in script file.")
            return
        elif isinstance(defaults, list):
            # display input widget for every entry in defaults
            # input widgets in n number of columns
            cols = st.columns(num_cols)
            i = 0
            for entry in defaults:
                key = f"{path.name}:{entry['key']}" if "key" in entry else None
                if key is None:
                    st.error("Key not specified for parameter.")
                    continue
                value = entry["value"] if "value" in entry else None
                if value is None:
                    st.error("Value not specified for parameter.")
                    continue
                hide = entry["hide"] if "hide" in entry else False
                # no need to display input and output files widget or hidden parameters
                if hide:
                    continue
                advanced = entry["advanced"] if "advanced" in entry else False
                # skip avdanced parameters if not selected
                if not st.session_state["advanced"] and advanced:
                    continue
                name = entry["name"] if "name" in entry else key
                help = entry["help"] if "help" in entry else ""
                min_value = entry["min"] if "min" in entry else None
                max_value = entry["max"] if "max" in entry else None
                step_size = entry["step_size"] if "step_size" in entry else 1
                widget_type = entry["widget_type"] if "widget_type" in entry else "auto"
                options = entry["options"] if "options" in entry else None

                with cols[i]:
                    self.input_widget(
                        key=key,
                        default=value,
                        name=name,
                        help=help,
                        widget_type=widget_type,
                        options=options,
                        min_value=min_value,
                        max_value=max_value,
                        step_size=step_size,
                    )
                # increment number of columns, create new cols object if end of line is reached
                i += 1
                if i == num_cols:
                    i = 0
                    cols = st.columns(num_cols)
        self.parameter_manager.save_parameters()

    def zip_and_download_files(self, directory: str):
        """
        Creates a zip archive of all files within a specified directory,
        including files in subdirectories, and offers it as a download
        button in a Streamlit application.

        Args:
            directory (str): The directory whose files are to be zipped.
        """
        # Ensure directory is a Path object and check if directory is empty
        directory = Path(directory)
        if not any(directory.iterdir()):
            st.error("No files to compress.")
            return

        bytes_io = BytesIO()
        files = list(directory.rglob("*"))  # Use list comprehension to find all files

        # Check if there are any files to zip
        if not files:
            st.error("Directory is empty or contains no files.")
            return

        n_files = len(files)

        c1, _ = st.columns(2)
        # Initialize Streamlit progress bar
        my_bar = c1.progress(0)

        with zipfile.ZipFile(bytes_io, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for i, file_path in enumerate(files):
                if (
                    file_path.is_file()
                ):  # Ensure we're only adding files, not directories
                    # Preserve directory structure relative to the original directory
                    zip_file.write(file_path, file_path.relative_to(directory.parent))
                    my_bar.progress((i + 1) / n_files)  # Update progress bar

        my_bar.empty()  # Clear progress bar after operation is complete
        bytes_io.seek(0)  # Reset buffer pointer to the beginning

        # Display a download button for the zip file in Streamlit
        c1.download_button(
            label="⬇️ Download Now",
            data=bytes_io,
            file_name="input-files.zip",
            mime="application/zip",
            use_container_width=True,
        )

    def file_upload_section(self, custom_upload_function) -> None:
        custom_upload_function()
        c1, _ = st.columns(2)
        if c1.button("⬇️ Download files", use_container_width=True):
            self.zip_and_download_files(Path(self.workflow_dir, "input-files"))

    def parameter_section(self, custom_parameter_function) -> None:
        st.toggle("Show advanced parameters", value=False, key="advanced")

        custom_parameter_function()

        # File Import / Export section       
        st.markdown("---")
        cols = st.columns(3)
        with cols[0]:
            if st.button(
                "⚠️ Load default parameters",
                help="Reset paramter section to default.",
                use_container_width=True,
            ):
                self.parameter_manager.reset_to_default_parameters()
                streamlit_js_eval(js_expressions="parent.window.location.reload()")
        with cols[1]:
            if self.parameter_manager.params_file.exists():
                with open(self.parameter_manager.params_file, "rb") as f:
                    st.download_button(
                        "⬇️ Export parameters",
                        data=f,
                        file_name="parameters.json",
                        mime="text/json",
                        help="Export parameter, can be used to import to this workflow.",
                        use_container_width=True,
                    )
            text = self.export_parameters_markdown()
            st.download_button(
                "📑 Method summary",
                data=text,
                file_name="method-summary.md",
                mime="text/md",
                help="Download method summary for publications.",
                use_container_width=True,
            )

        with cols[2]:
            up = st.file_uploader(
                "⬆️ Import parameters", help="Reset parameter section to default."
            )
            if up is not None:
                with open(self.parameter_manager.params_file, "w") as f:
                    f.write(up.read().decode("utf-8"))
                streamlit_js_eval(js_expressions="parent.window.location.reload()")

    def execution_section(self, start_workflow_function) -> None:
        with st.expander("**Summary**"):
            st.markdown(self.export_parameters_markdown())

        c1, c2 = st.columns(2)
        # Select log level, this can be changed at run time or later without re-running the workflow
        log_level = c1.selectbox(
            "log details", ["minimal", "commands and run times", "all"], key="log_level"
        )
        if self.executor.pid_dir.exists():
            if c1.button("Stop Workflow", type="primary", use_container_width=True):
                self.executor.stop()
                st.rerun()
        elif c1.button("Start Workflow", type="primary", use_container_width=True):
            start_workflow_function()
            st.rerun()
        log_path = Path(self.workflow_dir, "logs", log_level.replace(" ", "-") + ".log")
        if log_path.exists():
            if self.executor.pid_dir.exists():
                with st.spinner("**Workflow running...**"):
                    with open(log_path, "r", encoding="utf-8") as f:
                        st.code(
                            "".join(f.readlines()[-30:]),
                            language="neon",
                            line_numbers=False,
                        )
                    time.sleep(2)
                st.rerun()
            else:
                st.markdown(
                    f"**Workflow log file: {datetime.fromtimestamp(log_path.stat().st_ctime).strftime('%Y-%m-%d %H:%M')} CET**"
                )
                with open(log_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    # Check if workflow finished successfully
                    if not "WORKFLOW FINISHED" in content:
                        st.error("**Errors occurred, check log file.**")
                    st.code(content, language="neon", line_numbers=False)

    def results_section(self, custom_results_function) -> None:
        custom_results_function()

    def non_default_params_summary(self):
        # Display a summary of non-default TOPP parameters and all others (custom and python scripts)

        def remove_full_paths(d: dict) -> dict:
            # Create a copy to avoid modifying the original dictionary
            cleaned_dict = {}

            for key, value in d.items():
                if isinstance(value, dict):
                    # Recursively clean nested dictionaries
                    nested_cleaned = remove_full_paths(value)
                    if nested_cleaned:  # Only add non-empty dictionaries
                        cleaned_dict[key] = nested_cleaned
                elif isinstance(value, list):
                    # Filter out existing paths from the list
                    filtered_list = [
                        item if not Path(str(item)).exists() else Path(str(item)).name
                        for item in value
                    ]
                    if filtered_list:  # Only add non-empty lists
                        cleaned_dict[key] = ", ".join(filtered_list)
                elif not Path(str(value)).exists():
                    # Add entries that are not existing paths
                    cleaned_dict[key] = value

            return cleaned_dict

        # Don't want file paths to be shown in summary for export
        params = remove_full_paths(self.params)

        summary_text = ""
        python = {}
        topp = {}
        general = {}

        for k, v in params.items():
            # skip if v is a file path
            if isinstance(v, dict):
                topp[k] = v
            elif ".py" in k:
                script = k.split(".py")[0] + ".py"
                if script not in python:
                    python[script] = {}
                python[script][k.split(".py")[1][1:]] = v
            else:
                general[k] = v

        markdown = []

        def dict_to_markdown(d: dict):
            for key, value in d.items():
                if isinstance(value, dict):
                    # Add a header for nested dictionaries
                    markdown.append(f"> **{key}**\n")
                    dict_to_markdown(value)
                else:
                    # Add key-value pairs as list items
                    markdown.append(f">> {key}: **{value}**\n")

        if len(general) > 0:
            markdown.append("**General**")
            dict_to_markdown(general)
        if len(topp) > 0:
            markdown.append("**OpenMS TOPP Tools**\n")
            dict_to_markdown(topp)
        if len(python) > 0:
            markdown.append("**Python Scripts**")
            dict_to_markdown(python)
        return "\n".join(markdown)

    def export_parameters_markdown(self):
        markdown = []

        url = f"https://github.com/{st.session_state.settings['github-user']}/{st.session_state.settings['repository-name']}"
        tools = [p.stem for p in Path(self.parameter_manager.ini_dir).iterdir()]
        if len(tools) > 1:
            tools = ", ".join(tools[:-1]) + " and " + tools[-1]

        result = subprocess.run(
            "FileFilter --help", shell=True, text=True, capture_output=True
        )
        version = ""
        if result.returncode == 0:
            version = result.stderr.split("Version: ")[1].split("-")[0]

        markdown.append(
            f"""Data was processed using **{st.session_state.settings['app-name']}** ([{url}]({url})), a web application based on the OpenMS WebApps framework.
OpenMS ([https://www.openms.de](https://www.openms.de)) is a free and open-source software for LC-MS data analysis [1].
The workflow includes the **OpenMS {version}** TOPP tools {tools} as well as Python scripts. Non-default parameters are listed in the supplementary section below.

[1] Sachsenberg, Timo, et al. "OpenMS 3 expands the frontiers of open-source computational mass spectrometry." (2023).
"""
        )
        markdown.append(self.non_default_params_summary())
        return "\n".join(markdown)
    
    def simple_file_uploader(self, key: str, file_type: str, name: str = "") -> None:
        upload = st.file_uploader(
            name, file_type, False, help="Save parameters after uploading."
        )
        dir_path = Path(self.workflow_dir, "input-files", key)
        if upload:
            if dir_path.exists():
                shutil.rmtree(dir_path)
            dir_path.mkdir(parents=True, exist_ok=True)
            path = Path(dir_path, upload.name)
            with open(path, "wb") as f:
                f.write(upload.getbuffer())
        if dir_path.exists():
            st.info([p.name for p in dir_path.iterdir()][0])
        # else:
        #     st.warning(f"⚠️ **Missing:** {name}")
