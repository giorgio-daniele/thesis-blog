import os
import streamlit

from lib.dazn import page_1
from lib.dazn import page_2
from lib.dazn import page_3

SERVER = "dazn"

def main():

        
    FLOWS = "Active Experiments"
    PROFS = "DAZN Server Profiling"
    SAMPL = "DAZN Primary Flows Metrics"

    # config page
    streamlit.set_page_config(layout="wide")

    with streamlit.sidebar:
        page = streamlit.radio("Select page to be displayed", 
                               options=[FLOWS, PROFS, SAMPL])
        
    if page == FLOWS:
        page_1.main()
    if page == PROFS:
        page_2.main()
    if page == SAMPL:
        page_3.main()

main()


