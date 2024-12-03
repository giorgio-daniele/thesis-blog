import streamlit as st

# Set page configuration with dark theme
st.set_page_config(
    page_title="Welcome - QoE Research",
    layout="centered",
    initial_sidebar_state="expanded")

# Page title
page_title = "Design and Engineering of a System for Passive QoE Analysis from Tstat Traces"
st.title(page_title)

# Research description
research_description = """
This research focuses on the design and engineering of a system for passive analysis of Quality of Experience (QoE) 
using traces provided by Tstat. The main goal is to develop tools and methodologies to enhance understanding of 
user experience during multimedia content consumption.
"""
st.write(research_description)

# Software links section
software_section_title = "<h3>Software Used</h3>"
st.markdown(software_section_title, unsafe_allow_html=True)

# Links to the software
software_links = """
- [Streambot](https://github.com/giorgio-daniele/streambot): Software for automating experiments.
- [Tstat Scripting](https://github.com/giorgio-daniele/tstat-scripting): Software for processing data obtained from Tstat.
- [Tstat](http://tstat.polito.it/): The network analysis platform.
"""
st.write(software_links)

# Footer
footer_content = """
<footer style='text-align: center; color: #7f8c8d; font-family: Courier New, monospace;'>
    © 2024 QoE Research
</footer>
"""
st.markdown(footer_content, unsafe_allow_html=True)
