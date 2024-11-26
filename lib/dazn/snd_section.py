import os
import pandas
import streamlit
import plotly.express as px

from lib.generic import OPACITY

SERVER = "dazn"


def read_server_data(path: str):
    with open(path, 'r') as file:
        lines = file.readlines()
    
        # Filter out lines that start with '#' or are empty
        names = [line.strip() for line in lines if not line.startswith('#') and line.strip()]
        return names

def get_cdn_color(name: str):
    if name == "Akamai":
        return "rgba(173, 216, 230, 0.5)"  # lightblue with 50% opacity
    elif name == "Amazon Cloud Front":
        return "rgba(144, 238, 144, 0.5)"  # lightgreen with 50% opacity
    elif name == "Google Cloud":
        return "rgba(255, 255, 224, 0.5)"  # lightyellow with 50% opacity
    elif name == "Daznedge":
        return "rgba(240, 128, 128, 0.5)"  # lightcoral with 50% opacity
    elif name == "DAZN":
        return "rgba(255, 182, 193, 0.5)"  # lightpink with 50% opacity
    elif name == "DAZN CDN":
        return "rgba(211, 211, 211, 0.5)"  # lightgrey with 50% opacity
    else:
        return "rgba(255, 255, 255, 0.5)"  # white with 50% opacity
    
def get_cdn_name(name: str):
    if "akamaized.net" in name:
        return "Akamai"
    elif "cdn.indazn.com" in name:
        return "Amazon Cloud Front"
    elif "cdngc.dazn.com" in name:
        return "Google Cloud"
    elif "daznedge.net" in name:
        return "Daznedge"
    elif "dazn.com" in name:
        return "Fastly"
    else:
        return "Unknown"

def load_server_data(path: str) -> pandas.DataFrame:
    data = read_server_data(path=path)
    return pandas.DataFrame(data, columns=["cname"])

def add_cdn_info(frame: pandas.DataFrame) -> pandas.DataFrame:

    # Create 'CDN' column based on 'cname'
    frame["CDN"] = frame["cname"].apply(get_cdn_name)

    # Create 'color' column based on 'CDN'
    frame["color"] = frame["CDN"].apply(get_cdn_color)

    return frame

def highlight_rows(row: pandas.Series) -> list[str]:

    if "color" in row.index:
        color = row["color"]
    else:
        color = "rgba(255, 255, 255, 0.5)"

    return [f'background-color: {color};' for _ in row]

def display_styled_dataframe(frame: pandas.DataFrame) -> None:
    data = frame[["cname", "CDN"]].style.apply(highlight_rows, axis=1)
    streamlit.dataframe(data, use_container_width=True, hide_index=True)


##########################################################################
##########################################################################
#                                                                        #
#                               MAIN                                     #
#                                                                        #
##########################################################################
##########################################################################

def __main():

    streamlit.html(os.path.join("www", SERVER, "__snd_section", "0.html"))

    TCP_CNAMES = "meta/dazn/cnames_over_tcp"
    UDP_CNAMES = "meta/dazn/cnames_over_udp"
    NUM_EVENTS = "meta/dazn/num_events"

    MAIN_SERVERS   = "meta/dazn/servers/main.dat"
    LINEAR_SERVERS = "meta/dazn/servers/linear.dat"

    # Define two columns
    #  The left column is used to display CNAMEs over TCP
    #  while the right column is used to display CNAMEs
    #  over UDP

    tcp, udp = streamlit.columns(2)

    with open(NUM_EVENTS, "r") as file:
        num = int(next(file).strip())

    ############################################
    #              TCP section                 #
    ############################################

    tcp_frame = pandas.read_csv(TCP_CNAMES, sep="\s+")

    tcp_frame["rel"] = (tcp_frame["count"] / num) * 100

    ############################################
    #              UDP section                 #
    ############################################

    udp_frame = pandas.read_csv(UDP_CNAMES, sep="\s+")
    udp_frame["rel"] = (udp_frame["count"] / num) * 100

    with tcp:
        fig = px.bar(tcp_frame, x="cname", y="rel")
        fig.update_layout(xaxis_tickangle=-90, yaxis_title="frequency [%]")
        fig.update_xaxes(showgrid=True)
        fig.update_yaxes(showgrid=True)
        fig.update_layout(xaxis_tickangle=-90)
        fig.update_traces(opacity=OPACITY)
        streamlit.plotly_chart(fig, use_container_width=True)

    with udp:
        fig = px.bar(udp_frame, x="cname", y="rel")
        fig.update_layout(xaxis_tickangle=-90, yaxis_title="frequency [%]")
        fig.update_xaxes(showgrid=True)
        fig.update_yaxes(showgrid=True)
        fig.update_layout(xaxis_tickangle=-90)
        fig.update_traces(opacity=OPACITY)
        streamlit.plotly_chart(fig, use_container_width=True)

    streamlit.html(os.path.join("www", SERVER, "__snd_section", "1.html"))

    # Load and display Linear Servers
    linears = load_server_data(LINEAR_SERVERS)
    linears = add_cdn_info(linears)
    display_styled_dataframe(linears)

    streamlit.html(os.path.join("www", SERVER, "__snd_section", "2.html"))

    # Load and display Main Servers
    main = load_server_data(MAIN_SERVERS)
    streamlit.dataframe(main, use_container_width=True, hide_index=True)