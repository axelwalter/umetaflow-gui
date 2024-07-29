from streamlit.web import cli

if __name__=='__main__':
    cli._main_run_clExplicit('app.py', 'streamlit run', ['local', '--server.maxUploadSize', '2048'])

    # we will create this function inside our streamlit framework
