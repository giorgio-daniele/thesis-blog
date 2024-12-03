import os
import pandas    as pd
import streamlit as st


from lib.generic import LOG_BOT_COMPLETE
from lib.generic import LOG_HAR_COMPLETE
from lib.generic import LOG_TCP_COMPLETE
from lib.generic import LOG_UDP_COMPLETE
from lib.generic import LOG_TCP_PERIODIC
from lib.generic import LOG_UDP_PERIODIC

from lib.generic import tcp_info
from lib.generic import udp_info
from lib.generic import http_info
from lib.generic import plot_timeline
from lib.generic import periods
from lib.generic import LIMIT


SERVER = "dazn"

        
def get_number(name: str):
    return int(name.split("-")[1]) if "-" in name else 0

def tcp(dir: str):
    st.markdown("### TCP")

    # Load data
    tcom = pd.read_csv(os.path.join(dir, LOG_TCP_COMPLETE), sep=" ")
    tper = pd.read_csv(os.path.join(dir, LOG_TCP_PERIODIC), sep=" ")
    evns = periods(os.path.join(dir, LOG_BOT_COMPLETE))

    # Define x and y values
    xs, xe = "xs", "xe"

    # Convert timestamps to datetime
    tcom[xs] = pd.to_datetime(tcom["ts"], unit="ms", origin="unix")
    tcom[xe] = pd.to_datetime(tcom["te"], unit="ms", origin="unix")
    tper[xs] = pd.to_datetime(tper["ts"], unit="ms", origin="unix")
    tper[xe] = pd.to_datetime(tper["te"], unit="ms", origin="unix")

    # Add info
    tcom["info"] = tcom.apply(tcp_info, axis=1)
    tper["info"] = tper.apply(tcp_info, axis=1)

    # Canonical Names selection
    cnames = st.multiselect("Select Canonical Names over TCP", sorted(set(tcom["cn"])))

    # Filter data based on selected Canonical Names
    com_cns = tcom[tcom["cn"].isin(cnames)]
    per_cns = tper[tper["cn"].isin(cnames)]

    if cnames:
        for data, title in [(com_cns, "log_tcp_complete"), (per_cns, "log_tcp_periodic")]:
            plot_timeline(data=data, 
                     evns=evns, xs=xs, xe=xe, y="id", color="cn", xaxis_title="time [mm:ss]", yaxis_title="id [#]",  chart_title=title)
    else:
        st.warning("Nothing to see here")
    return

def udp(dir: str):
    st.markdown("### UDP")

    # Load data
    ucom = pd.read_csv(os.path.join(dir, LOG_UDP_COMPLETE), sep=" ")
    uper = pd.read_csv(os.path.join(dir, LOG_UDP_PERIODIC), sep=" ")
    evns = periods(os.path.join(dir, LOG_BOT_COMPLETE))

    # Define x and y values
    xs, xe = "xs", "xe"
    id, cl = "id", "cn"

    # Convert timestamps to datetime
    ucom[xs] = pd.to_datetime(ucom["ts"], unit="ms", origin="unix")
    ucom[xe] = pd.to_datetime(ucom["te"], unit="ms", origin="unix")
    uper[xs] = pd.to_datetime(uper["ts"], unit="ms", origin="unix")
    uper[xe] = pd.to_datetime(uper["te"], unit="ms", origin="unix")

    # Add info
    ucom["info"] = ucom.apply(udp_info, axis=1)
    uper["info"] = uper.apply(udp_info, axis=1)

    # Canonical Names selection
    cnames = st.multiselect("Select Canonical Names over UDP", sorted(set(ucom["cn"])))

    # Filter data based on selected Canonical Names
    com_cns = ucom[ucom["cn"].isin(cnames)]
    per_cns = uper[uper["cn"].isin(cnames)]

    # Display timelines if Canonical Names are selected
    if cnames:
        for data, title in [(com_cns, "log_udp_complete"), (per_cns, "log_udp_periodic")]:
            plot_timeline(data=data, 
                          evns=evns, xs=xs, xe=xe, y=id, color=cl, 
                          xaxis_title="time [mm:ss]", 
                          yaxis_title="id [#]",  
                          chart_title=title)
    else:
        st.warning("Nothing to see here")
    return

def http(dir: str):
    st.markdown("### HTTP")

    # Load data
    http = pd.read_csv(os.path.join(dir, LOG_HAR_COMPLETE), sep=" ")
    evns = periods(os.path.join(dir, LOG_BOT_COMPLETE))

    # Define x and y values
    xs, xe = "xs",   "xe"
    id, cl = "mime", "mime"

    # Convert timestamps to datetime
    http[xs] = pd.to_datetime(http["ts"], unit="ms", origin="unix")
    http[xe] = pd.to_datetime(http["te"], unit="ms", origin="unix")

    # Add info
    http["info"] = http.apply(http_info, axis=1)

    plot_timeline(data=http, 
                  evns=evns, xs=xs, xe=xe, y=id, color=cl, 
                  xaxis_title="time [mm:ss]",
                  yaxis_title="mime [*]",  
                  chart_title="log_har_complete")

def main():
    
    st.title("Supervised Experiments")
    
    col1, col2 = st.columns(2)

    with col1:
        qos = st.selectbox("Choose testbed bandwidth", os.listdir(SERVER))

    with col2:
        path = os.path.join(SERVER, qos, "tests")
        opts = sorted([opt for opt in os.listdir(path)], key=get_number)
        test = st.selectbox("Choose supervised experiment", options=opts[:LIMIT])

    """
    =============================
    =    Processing TCP Layer   =
    =============================
    """

    tcp(dir=os.path.join(SERVER, qos, "tests", test))


    """
    =============================
    =    Processing TCP Layer   =
    =============================
    """

    udp(dir=os.path.join(SERVER, qos, "tests", test))


    """
    =============================
    =   Processing HTTP Layer   =
    =============================
    """

    http(dir=os.path.join(SERVER, qos, "tests", test))