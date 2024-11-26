import os
import streamlit

from lib.dazn import fst_section
from lib.dazn import snd_section
from lib.dazn import trd_section

SERVER = "dazn"

def main():

        
    INTRO = "Introduction"
    FLOWS = "Recostructed Flows"
    PROFS = "DAZN Servers Profiling"
    SAMPL = "Measurements"

    # config page
    streamlit.set_page_config(layout="wide")

    with streamlit.sidebar:
        page = streamlit.radio("Select page to be displayed", 
                               options=[INTRO, FLOWS, PROFS, SAMPL])
        
    if page == INTRO:
        pass
    if page == FLOWS:
        fst_section.main()
    if page == PROFS:
        pass
    if page == SAMPL:
        trd_section.main()

main()


