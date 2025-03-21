import os
import streamlit

from lib.amazon import page_1
from lib.amazon import page_2

def main():

    opt_1 = "Supervised Experiment"
    opt_2 = "Live Streaming Flows Features"

    with streamlit.sidebar:
        page = streamlit.radio("Select page to be displayed", 
                               options=[opt_1, opt_2])
        
    if page == opt_1:
        page_1.main()

    if page == opt_2:
        page_2.main()
main()


