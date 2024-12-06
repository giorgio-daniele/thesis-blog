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
from lib.generic import plot_timeline
from lib.generic import periods
from lib.generic import LIMIT


import plotly.express as px

        
def get_number(name: str):
    return int(name.split("-")[1]) if "-" in name else 0

def time_axis(min_value, max_value):
    values = pandas.date_range(start=min_value, end=max_value, freq="10s")
    labels = [v.strftime("%M:%S") for v in values]
    return values, labels

def plot_timeline(flows: pandas.DataFrame, intervals: pandas.DataFrame, x_start: str, x_end: str, y: str, color: str, 
                  xaxis_title: str, 
                  yaxis_title: str, 
                  chart_title: str):
    
    # Calculate the number of categories and define chart height
    num_categories      = flows[y].nunique()
    height_per_category = 40
    chart_height        = max(220, num_categories * height_per_category)
    
    # Define color for a streaming period
    yellow = "rgba(255,255,0,0.2)"
    
    # Generate a new figure
    figure = px.timeline(flows, x_start=x_start, x_end=x_end, y=y, color=color, custom_data="info")
    
    # Add hovertemplate
    figure.update_traces(hovertemplate="%{customdata[0]}<extra></extra>")
    
    # Define the x-axis boundaries
    min_x_axis_value = pandas.Timestamp('1970-01-01 00:00:00')
    max_x_axis_value = max(intervals, key=lambda x: x[1])[1]
    
    # Define the xaxis values and labels
    xaxis_values, xaxis_labels = time_axis(min_value=min_x_axis_value, 
                                           max_value=pandas.to_datetime(max_x_axis_value, unit="ms", origin="unix"))
    
    for interval in intervals:
        ts = pandas.to_datetime(interval[0], unit="ms", origin="unix")
        te = pandas.to_datetime(interval[1], unit="ms", origin="unix")
        figure.add_vrect(x0=ts, x1=te, fillcolor=yellow, line_width=0)
        
    # Update x-axis
    figure.update_layout(xaxis=dict(tickvals=xaxis_values, 
                                    ticktext=xaxis_labels,  tickformat="%M:%S", 
                                    tickfont=dict(size=12), title=xaxis_title, showgrid=True))
    # Update y-axis
    figure.update_layout(yaxis=dict(tickfont=dict(size=12), title=yaxis_title, showgrid=True, categoryorder="array"))
    
    # Update the title
    figure.update_layout(title=dict(text=chart_title, font=dict(size=13)), showlegend=True, height=chart_height)
    
    # Render the image
    streamlit.plotly_chart(figure_or_data=figure)

def tcp(dir: str):
    
    # Define the title of the section
    streamlit.markdown("## TCP")
    
    # Explain what TCP is, and how Tstat reconstruct flows
    streamlit.markdown(
        """
        <style>
        .justified-text {
            text-align: justify;
        }
        </style>
        <div class="justified-text">
            Transmission Control Protocol (TCP) is a fundamental protocol within the Internet protocol suite, 
            ensuring reliable, ordered, and error-checked delivery of data across networks. Tstat, a network 
            analysis tool, reconstructs a TCP flow by identifying the initial synchronization (SYN) packet 
            and marking its termination with either a FIN or RST packet. Once the flow boundaries are defined, 
            Tstat computes an extensive set of statistics, which are broadly classified into two main categories: 
            volumetric metrics and temporal metrics. Volumetric metrics are concerned with the amount of data 
            (bytes and packets) exchanged during the flow, whereas temporal metrics focus on the flow's duration, 
            average round-trip time (RTT), and other statistical measures that provide insights into the flow's behavior.
            <br/>
            <br/>
            When Tstat generates the <code>log_tcp_complete</code>, metrics are reported as cumulative sums over the entire 
            lifespan of the flow for volumetric metrics. Temporal metrics, in contrast, are calculated using statistical 
            indicators (such as the mean, the standard deviation) aggregated over the flow's complete duration. Conversely, 
            when Tstat generates the <code>log_tcp_periodic</code>, metrics are computed over short time intervals, referred 
            to as <b>bins</b>. Each bin represents a maximum duration of one second and captures data exchange during a brief 
            period while either the client or server is active. The <code>log_tcp_periodic</code> output provides a detailed 
            temporal perspective, offering insights into the nature of the data exchange, such as whether it involves prolonged 
            silences, impulsive bursts, or continuous transmission patterns.
            <br/>
            <br/>
        </div>
        """, unsafe_allow_html=True)

    # Load data
    complete  = pandas.read_csv(os.path.join(dir, LOG_TCP_COMPLETE), sep=" ")
    periodic  = pandas.read_csv(os.path.join(dir, LOG_TCP_PERIODIC), sep=" ")
    intervals = periods(os.path.join(dir, LOG_BOT_COMPLETE))

    # Define x and y values
    xs, xe = "xs", "xe"

    # Convert timestamps to datetime in complete document
    complete[xs] = pandas.to_datetime(complete["ts"], unit="ms", origin="unix")
    complete[xe] = pandas.to_datetime(complete["te"], unit="ms", origin="unix")
    
    # Convert timstamps to datetime in periodic documents
    periodic[xs] = pandas.to_datetime(periodic["ts"], unit="ms", origin="unix")
    periodic[xe] = pandas.to_datetime(periodic["te"], unit="ms", origin="unix")

    # Add info
    complete["info"] = complete.apply(tcp_info, axis=1)
    periodic["info"] = periodic.apply(tcp_info, axis=1)

    # CNAME selection
    cnames = streamlit.multiselect("Select CNAMEs from in TCP flows", sorted(set(complete["cn"])))

    # Filter data based on selected Canonical Names
    selected_complete = complete[complete["cn"].isin(cnames)]
    selected_periodic = periodic[periodic["cn"].isin(cnames)]
    
    # If the CNAMEs are not selected, return
    if cnames:
        xaxis_title = "time [mm:ss]"
        yaxis_title = "id [#]"
        chart_title = "TCP flows reconstructed by Tstat in log_tcp_complete"
        plot_timeline(flows=selected_complete, intervals=intervals, x_start=xs, x_end=xe, y="id", color="cn",
                    xaxis_title=xaxis_title,
                    yaxis_title=yaxis_title,
                    chart_title=chart_title)
        
        xaxis_title = "time [mm:ss]"
        yaxis_title = "id [#]"
        chart_title = "TCP flows reconstructed by Tstat in log_tcp_periodic"
        plot_timeline(flows=selected_periodic, intervals=intervals, x_start=xs, x_end=xe, y="id", color="cn",
                    xaxis_title=xaxis_title,
                    yaxis_title=yaxis_title,
                    chart_title=chart_title)
    else:
        streamlit.warning("Nothing to see here, you do not have selected any CNAME")
        return

def udp(dir: str):
    
    # Define the title of the section
    streamlit.markdown("## UDP")
    
    # Explain what UDP is, and how Tstat reconstruct flows
    streamlit.markdown(
        """
        <style>
        .justified-text {
            text-align: justify;
        }
        </style>
        <div class="justified-text">
            User Datagram Protocol (UDP) is a core protocol within the Internet protocol suite, designed for lightweight, 
            connectionless communication across networks. Unlike TCP, UDP does not provide guarantees for reliable, ordered, 
            or error-checked delivery of data, making it suitable for time-sensitive applications such as video streaming, 
            online gaming, and VoIP. Due to the absence of a connection-oriented design, Tstat cannot reconstruct flows using 
            specific packets like the SYN or FIN markers used in TCP. Instead, Tstat processes the client-to-server and 
            server-to-client data streams as separate unidirectional flows. In the analysis that follows, only the 
            server-to-client flow is considered. Therefore both <code>log_udp_complete</code> and <code>log_udp_periodic</code>,
            what Tstat observed traversing the network from server to client, considering the lifespan of all UDP
            data exchange equal to the lifspan of the UDP flow from server to client.
            <br/>
            <br/>
        </div>
        """, unsafe_allow_html=True)

    # Load data
    complete  = pandas.read_csv(os.path.join(dir, LOG_UDP_COMPLETE), sep=" ")
    periodic  = pandas.read_csv(os.path.join(dir, LOG_UDP_PERIODIC), sep=" ")
    intervals = periods(os.path.join(dir, LOG_BOT_COMPLETE))

    # Define x and y values
    xs, xe = "xs", "xe"

    # Convert timestamps to datetime in complete document
    complete[xs] = pandas.to_datetime(complete["ts"], unit="ms", origin="unix")
    complete[xe] = pandas.to_datetime(complete["te"], unit="ms", origin="unix")
    
    # Convert timstamps to datetime in periodic documents
    periodic[xs] = pandas.to_datetime(periodic["ts"], unit="ms", origin="unix")
    periodic[xe] = pandas.to_datetime(periodic["te"], unit="ms", origin="unix")

    # Add info
    complete["info"] = complete.apply(tcp_info, axis=1)
    periodic["info"] = periodic.apply(tcp_info, axis=1)

    # CNAME selection
    cnames = streamlit.multiselect("Select CNAMEs from in UDP flows", sorted(set(complete["cn"])))

    # Filter data based on selected Canonical Names
    selected_complete = complete[complete["cn"].isin(cnames)]
    selected_periodic = periodic[periodic["cn"].isin(cnames)]
    
    # If the CNAMEs are not selected, return
    if cnames:
        xaxis_title = "time [mm:ss]"
        yaxis_title = "id [#]"
        chart_title = "UDP flows reconstructed by Tstat in log_udp_complete"
        plot_timeline(flows=selected_complete, intervals=intervals, x_start=xs, x_end=xe, y="id", color="cn",
                    xaxis_title=xaxis_title,
                    yaxis_title=yaxis_title,
                    chart_title=chart_title)
        
        xaxis_title = "time [mm:ss]"
        yaxis_title = "id [#]"
        chart_title = "UDP flows reconstructed by Tstat in log_udp_periodic"
        plot_timeline(flows=selected_periodic, intervals=intervals, x_start=xs, x_end=xe, y="id", color="cn",
                    xaxis_title=xaxis_title,
                    yaxis_title=yaxis_title,
                    chart_title=chart_title)
    else:
        streamlit.warning("Nothing to see here, you do not have selected any CNAME")
        return

def http(dir: str):
    
    # Define the title
    streamlit.markdown("## HTTP")
    
    # Explain what HAS and how the flow is reconstructed
    streamlit.markdown(
        """
        <style>
        .justified-text {
            text-align: justify;
        }
        </style>
        <div class="justified-text">
            HTTP Adaptive Streaming (HAS) is a method for delivering multimedia content over HTTP that enables dynamic adjustment of 
            video quality based on the user's network conditions and device capabilities. In HAS protocols, video files are segmented 
            into small chunks, each encoded at multiple bitrates. The client-side player monitors the available bandwidth and selects 
            the appropriate quality level for each segment in real-time, ensuring smooth playback with minimal buffering. 
            In our analysis, we reconstructed the sequence of HTTP requests issued by the client during each streaming session by 
            capturing the video <code>video/mp4</code> and <code>audio/mp4</code> requests. These requests were then sorted based 
            on the timestamps corresponding to the exact moment each request was made by the client in the browser.
            <br/>
            <br/>
            The lower the available bandwidth on the client side, the lower the overall video quality. According to the principles 
            of HTTP Adaptive Streaming (HAS), the system dynamically adjusts the video quality based on the network conditions 
            experienced by the client. Therefore, as the network conditions degrade, it is expected that HTTP requests for video 
            segments will predominantly correspond to lower resolution video chunks, which require less bandwidth.
        </div>
        """, unsafe_allow_html=True)

    # Load data
    requests  = pandas.read_csv(os.path.join(dir, LOG_HAR_COMPLETE), sep=" ")
    intervals = periods(os.path.join(dir, LOG_BOT_COMPLETE))

    # Define x and y values
    xs, xe = "xs",   "xe"
    id, cl = "mime", "mime"

    # Convert timestamps to datetime
    requests[xs] = pandas.to_datetime(requests["ts"], unit="ms", origin="unix")
    requests[xe] = pandas.to_datetime(requests["te"], unit="ms", origin="unix")

    # Add info
    requests["info"] = requests.apply(http_info, axis=1)

    xaxis_title = "time [mm:ss]"
    yaxis_title = "mime-type []"
    chart_title = "HAS flow reconstructed in log_har_complete"
    plot_timeline(flows=requests, intervals=intervals, x_start=xs, x_end=xe, y=id, color=cl,
                  xaxis_title=xaxis_title,
                  yaxis_title=yaxis_title,
                  chart_title=chart_title)
    
    # Filter video and audio requests
    video_requests = requests[requests["mime"] == "video"]
    audio_requests = requests[requests["mime"] == "audio"]

    # Group by 'video_rate' and count occurrences for video
    video_quality_dist = video_requests.groupby("video_rate").size().reset_index(name="count")

    # Group by 'audio_rate' and count occurrences for audio
    audio_quality_dist = audio_requests.groupby("audio_rate").size().reset_index(name="count")

    # Create pie charts
    fig_video = px.pie(video_quality_dist, names="video_rate", values="count", title="Video Rate Distribution",
                       labels={"video_rate": "Video rate in (kbps)"})
    fig_audio = px.pie(audio_quality_dist, names="audio_rate", values="count", title="Audio Rate Distribution",
                       labels={"audio_rate": "Audio rate in (kbps)"})
    
    fig_video.update_layout(showlegend=False)
    fig_audio.update_layout(showlegend=False)

    # Arrange the pie charts side by side
    col1, col2 = streamlit.columns(2)
    with col1:
        streamlit.plotly_chart(fig_video)
        caption = """
        <div style="text-align: justify; font-size: 15px; color: black;">
            The pie chart presents the distribution of video requests based on their data rate. 
            The rate at which video data is encoded provides an indication of the perceived 
            quality of the video stream as experienced by the client.
        </div>
        """
        streamlit.markdown(caption, unsafe_allow_html=True)
        streamlit.text("\n")
        
    with col2:
        streamlit.plotly_chart(fig_audio)
        caption = """
        <div style="text-align: justify; font-size: 15px; color: black;">
            The pie chart illustrates the distribution of audio requests according to their encoding rate. 
            The data rate at which audio is encoded serves as a key indicator of the perceived quality 
            of the audio stream, as experienced by the client.
        </div>
        """
        streamlit.markdown(caption, unsafe_allow_html=True)
        streamlit.text("\n")

    
def main():
    
    SERVER = "dazn"
    
    # Define the title
    streamlit.title("Active Experiments")
    
    # Define what is a supervised experiment
    streamlit.markdown(
        """
        <style>
        .justified-text {
            text-align: justify;
        }
        </style>
        <div class="justified-text">
            We define an <b>active experiment</b> as an <em>organized</em>, <em>repeatable</em>, and 
            <em>automated</em> method for viewing one or more events streamed live by a Content Provider. 
            It captures three fundamental data types: data link layer network traffic, which traces every 
            individual packet on the wire; application layer network traffic, which records every HTTP 
            transaction that occurs; and, finally, the collection of instants at which the 
            streaming periods occurs.
            <br/>
            <br/>
            The time interval during which the client downloads video and audio data associated with a 
            streaming event is defined as the <b>streaming period</b>. This interval is typically represented 
            as [ts; te], where ts denotes the time at which playback begins, and te indicates the time at which 
            it concludes. These intervals are highlighted in yellow.
            <br/>
            <br/>
            Active experiments have been conducted to analyze the behavior of a DAZN user during video streaming 
            under varying network conditions, primarily influenced by differences in bandwidth. Each experiment 
            consists of the reproduction of a linear channel for 300 seconds (5 minutes), during which all client-issued
            requests at the application layer (Layer 7) are recorded, along with the network packets exchanged with 
            external servers. At the conclusion of each experiment, the network trace data is processed by Tstat, which 
            generates the following logs: <code>log_tcp_complete</code>, <code>log_tcp_periodic</code>, 
            <code>log_udp_complete</code>, and <code>log_udp_periodic</code>.
            <br/>
            <br/>
        </div>
        """, unsafe_allow_html=True)
    
    col1, col2 = streamlit.columns(2)

    with col1:
        qos = streamlit.selectbox("Choose testbed bandwidth", os.listdir(SERVER))

    with col2:
        path = os.path.join(SERVER, qos, "tests")
        opts = sorted([opt for opt in os.listdir(path)], key=get_number)
        test = streamlit.selectbox("Choose supervised experiment", options=opts[:LIMIT])

    # TCP
    tcp(dir=os.path.join(SERVER, qos, "tests", test))
    
    # UDP
    udp(dir=os.path.join(SERVER, qos, "tests", test))

    # HTTP
    http(dir=os.path.join(SERVER, qos, "tests", test))