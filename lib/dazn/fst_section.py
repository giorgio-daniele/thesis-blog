import os
import pandas
import streamlit


from lib.generic import LOG_BOT_COMPLETE
from lib.generic import LOG_HAR_COMPLETE
from lib.generic import LOG_TCP_COMPLETE
from lib.generic import LOG_UDP_COMPLETE
from lib.generic import LOG_TCP_PERIODIC
from lib.generic import LOG_UDP_PERIODIC

from lib.generic import tcp_info
from lib.generic import udp_info
from lib.generic import http_info
from lib.generic import timeline
from lib.generic import periods

from lib.generic import LIMIT


SERVER = "dazn"

        
def get_number(name: str):
    return int(name.split("-")[1]) if "-" in name else 0


def tcp(dir: str):
    streamlit.markdown("### TCP")

    # Load data
    tcom = pandas.read_csv(os.path.join(dir, LOG_TCP_COMPLETE), sep=" ")
    tper = pandas.read_csv(os.path.join(dir, LOG_TCP_PERIODIC), sep=" ")
    evns = periods(os.path.join(dir, LOG_BOT_COMPLETE))

    # Define x and y values
    xs, xe = "xs", "xe"

    # Convert timestamps to datetime
    tcom[xs] = pandas.to_datetime(tcom["ts"], unit="ms", origin="unix")
    tcom[xe] = pandas.to_datetime(tcom["te"], unit="ms", origin="unix")
    tper[xs] = pandas.to_datetime(tper["ts"], unit="ms", origin="unix")
    tper[xe] = pandas.to_datetime(tper["te"], unit="ms", origin="unix")

    # Add info
    tcom["info"] = tcom.apply(tcp_info, axis=1)
    tper["info"] = tper.apply(tcp_info, axis=1)

    # Canonical Names selection
    cns = streamlit.multiselect("Select Canonical Names over TCP", sorted(set(tcom["cn"])))

    # Filter data based on selected Canonical Names
    com_cns = tcom[tcom["cn"].isin(cns)]
    per_cns = tper[tper["cn"].isin(cns)]

    # Display timelines if Canonical Names are selected
    if cns:
        for data, title in [(com_cns, "log TCP complete"), (per_cns, "log TCP periodic")]:
            timeline(data=data, 
                     evns=evns, xs=xs, xe=xe, y="id", color="cn", xtitle="time [mm:ss]", ytitle="id [#]",  ctitle=title)
    else:
        streamlit.warning("Nothing to see here")
    return

def udp(dir: str):
    streamlit.markdown("### UDP")

    # Load data
    ucom = pandas.read_csv(os.path.join(dir, LOG_UDP_COMPLETE), sep=" ")
    uper = pandas.read_csv(os.path.join(dir, LOG_UDP_PERIODIC), sep=" ")
    evns = periods(os.path.join(dir, LOG_BOT_COMPLETE))

    # Define x and y values
    xs, xe = "xs", "xe"
    id, cl = "id", "cn"

    # Convert timestamps to datetime
    ucom[xs] = pandas.to_datetime(ucom["ts"], unit="ms", origin="unix")
    ucom[xe] = pandas.to_datetime(ucom["te"], unit="ms", origin="unix")
    uper[xs] = pandas.to_datetime(uper["ts"], unit="ms", origin="unix")
    uper[xe] = pandas.to_datetime(uper["te"], unit="ms", origin="unix")

    # Add info
    ucom["info"] = ucom.apply(udp_info, axis=1)
    uper["info"] = uper.apply(udp_info, axis=1)

    # Canonical Names selection
    cns = streamlit.multiselect("Select Canonical Names over UDP", sorted(set(ucom["cn"])))

    # Filter data based on selected Canonical Names
    com_cns = ucom[ucom["cn"].isin(cns)]
    per_cns = uper[uper["cn"].isin(cns)]

    # Display timelines if Canonical Names are selected
    if cns:
        for data, title in [(com_cns, "log UDP complete"), (per_cns, "log UDP periodic")]:
            timeline(data=data, 
                     evns=evns, xs=xs, xe=xe, y=id, color=cl, xtitle="time [mm:ss]", ytitle="id [#]",  ctitle=title)
    else:
        streamlit.warning("Nothing to see here")
    return

def http(dir: str):
    streamlit.markdown("### HTTP")

    # Load data
    http = pandas.read_csv(os.path.join(dir, LOG_HAR_COMPLETE), sep=" ")
    evns = periods(os.path.join(dir, LOG_BOT_COMPLETE))

    # Define x and y values
    xs, xe = "xs", "xe"
    id, cl = "mime", "mime"

    # Convert timestamps to datetime
    http[xs] = pandas.to_datetime(http["ts"], unit="ms", origin="unix")
    http[xe] = pandas.to_datetime(http["te"], unit="ms", origin="unix")

    # Add info
    http["info"] = http.apply(http_info, axis=1)

    timeline(data=http, 
             evns=evns, xs=xs, xe=xe, y=id, color=cl, xtitle="time [mm:ss]", ytitle="mime [*]",  ctitle="log HAR complete")

#############################
#           MAIN            #
#############################

def main():
    streamlit.html(os.path.join("www", SERVER, "__fst_section", "0.html"))

    col1, col2 = streamlit.columns(2)

    with col1:
        qos = streamlit.selectbox("Choose testbed bandwidth", os.listdir(SERVER))

    with col2:
        path = os.path.join(SERVER, qos, "tests")
        opts = sorted([opt for opt in os.listdir(path)], key=get_number)
        test = streamlit.selectbox("Choose supervised experiment", options=opts[:LIMIT])

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