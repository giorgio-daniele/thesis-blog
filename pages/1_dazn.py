import os
import streamlit

from lib.dazn import page_1
from lib.dazn import page_2
from lib.dazn import page_3

SERVER = "dazn"

def main():

        
    INTRO = "Introduction"
    FLOWS = "Supervised Experiments"
    PROFS = "Server Profiling"
    SAMPL = "HAS Flows Metrics"

    # config page
    streamlit.set_page_config(layout="wide")

    with streamlit.sidebar:
        page = streamlit.radio("Select page to be displayed", 
                               options=[INTRO, FLOWS, PROFS, SAMPL])
        
    if page == INTRO:
        pass
    if page == FLOWS:
        page_1.main()
    if page == PROFS:
        pass
    if page == SAMPL:
        page_3.main()

main()


