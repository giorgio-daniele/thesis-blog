import os
import pandas
import streamlit
import humanize
import plotly.express as px
import plotly.graph_objects as go

from lib.generic import format_volume

SERVER = "dazn"

def read_file(path: str):
    return pandas.read_csv(path, sep=" ")

def analyze(frame: pandas.DataFrame):
    keywords = ["linear", "live", "origin", "vod", "dvr", "cdn", "adaptive bitrate", "multi-cdn", "hls"]
    groups   = {key: frame[frame["cname"].str.contains(key, case=False, na=False)] for key in keywords}
    
    total_download  = frame["volume"].sum()
    groups          = {gn: grp["volume"].sum() for gn, grp in groups.items()}
    
    return total_download, groups
    

def plot_pie_chart(groups: pandas.DataFrame, total: float):
    # Humanize the volume values
    humanized_values = [humanize.naturalsize(vol, binary=True) for vol in groups.values()]
    
    # Pie chart data
    labels = list(groups.keys())
    values = list(groups.values())
    
    # Calculate proportions for the chart
    proportions = [(vol / total) * 100 for vol in values]
    
    # Create the pie chart
    pie_chart = go.Figure(data=[go.Pie(
        labels=labels, 
        values=values, 
        hole=0.1, 
        text=[f"{humanized_values[i]} (scale: {proportions[i]:.2f}%)" for i in range(len(labels))],  # Text to display
        textinfo='text',  # Show text
        textposition='inside',  # Position text inside the slices
        insidetextorientation='radial'  # Rotate text for better fit
    )])
    
    # Display the pie chart (if using Streamlit)
    streamlit.plotly_chart(pie_chart)


def main():
    
    SERVER = "dazn"
    
    # Define the title
    streamlit.title("DAZN Servers Profiling")
    
    # Define what is a supervised experiment
    streamlit.markdown(
        """
        <style>
        .justified-text {
            text-align: justify;
        }
        </style>
        <div class="justified-text">
            To address this, we define Content Provider Profiling as the process of scraping and identifying 
            server names associated with a Content Provider registered either in DNS or in a PKI. This is achieved by 
            leveraging the CNAME reconstructed by Tstat in both TCP and UDP flows, as recorded in 
            <code>log_tcp_complete</code> and <code>log_udp_complete</code>, respectively.
            <br/>
            <br/>
            Specifically, this technique is employed to gain an overview of the services deployed by a 
            Content Provider (e.g., video and audio distribution, authentication, telemetry, data storage, 
            general computing), which serve as a footprint for generating a set of regular expression
            by which addressing TCP and UDP flows in real-world network trace where many other services are l
            ikely to be there. As documented by M. Trevisan, D. Giordano, I. Drago, M. Mellia, and M. Munafò in Five
            years at the edge: Watching internet from the isp network in April 2020, adopting regular expressions 
            for filtering flows according to their CNAME has been demonstrated to be reliable for targeting this
            or that public company (e.g., Spotify, Facebook). We adopt a similar approach for detecting DAZN 
            related flows.
            <br/>
            <br/>
        </div>
        """, unsafe_allow_html=True)

    STREAMING_PERIODS_OBSERVED     = "streaming_periods_observed.dat"
    CPROVIDER_CNAMES_OBSERVED_TCP  = "content_provider_cnames_over_tcp.dat"
    CPROVIDER_CNAMES_OBSERVED_UDP  = "content_provider_cnames_over_udp.dat"
    
    # Generate the frames
    cnames_tcp = pandas.read_csv(os.path.join(os.getcwd(), "meta", SERVER, CPROVIDER_CNAMES_OBSERVED_TCP), sep=" ")
    cnames_udp = pandas.read_csv(os.path.join(os.getcwd(), "meta", SERVER, CPROVIDER_CNAMES_OBSERVED_UDP), sep=" ")
    
    # Generate a human readable version of the data from server
    cnames_tcp["download"] = cnames_tcp["volume"].apply(format_volume)
    cnames_udp["download"] = cnames_udp["volume"].apply(format_volume)
    
    # Compute the total
    total = cnames_tcp["volume"].sum()
    cnames_tcp["scale"] = cnames_tcp["volume"] / total * 100
    
    # Compute the total
    total = cnames_udp["volume"].sum()
    cnames_udp["scale"] = cnames_udp["volume"] / total * 100
    
    col1, col2 = streamlit.columns(2)
    
    # Display statistics observed in TCP
    with col1:
        streamlit.caption("### CNAMEs dictionary collected in TCP")
        streamlit.dataframe(cnames_tcp[["cname", "frequency", "download"]], hide_index=True, use_container_width=True)
        caption = """
        <div style="text-align: justify; font-size: 15px; color: gray;">
            This frame summarizes the frequency of CNAMEs observed over 480 streaming periods, 
            watching different linear channels, focusing on TCP layer. 
            Each record reports how many times the CNAME has been observed during a streaming period, 
            alongside the amount of the overall volume of data the client has downloaded from that 
            CNAME across all streaming periods.
        </div>
        """
        streamlit.markdown(caption, unsafe_allow_html=True)
        streamlit.text("\n")
        
    # Display statistics observed in UDP
    with col2:
        streamlit.caption("### CNAMEs dictionary collected in UDP")
        streamlit.dataframe(cnames_udp[["cname", "frequency", "download"]],  hide_index=True, use_container_width=True)
        caption = """
        <div style="text-align: justify; font-size: 15px; color: gray;">
            This frame summarizes the frequency of CNAMEs observed over 480 streaming periods, 
            watching different linear channels, focusing on UDP layer. 
            Each record reports how many times the CNAME has been observed during a streaming period, 
            alongside the amount of the overall volume of data the client has downloaded from that 
            CNAME across all streaming periods.
        </div>
        """
        streamlit.markdown(caption, unsafe_allow_html=True)
        streamlit.text("\n")
        

    col1, col2 = streamlit.columns(2)
    with col1:
        x = "cname"
        y = "volume"
        xaxis_title = "cname"
        yaxis_title = "volume [%]"
        chart_title = "Data volumes according to CNAME across all streaming periods in TCP flows"
        figure = go.Figure(data=[go.Bar(x=cnames_tcp[x], y=cnames_tcp[y], marker=dict(color="blue", opacity=0.5))])
        figure.update_layout(title=chart_title, xaxis_title=xaxis_title, yaxis_title=yaxis_title, xaxis_tickangle=-90)
        streamlit.plotly_chart(figure)
        
    with col2:
        x = "cname"
        y = "volume"
        xaxis_title = "cname"
        yaxis_title = "volume [%]"
        chart_title = "Data volumes according to CNAME across all streaming periods in UDP flows"
        figure = go.Figure(data=[go.Bar(x=cnames_udp[x], y=cnames_udp[y], marker=dict(color="blue", opacity=0.5))])
        figure.update_layout(title=chart_title, xaxis_title=xaxis_title, yaxis_title=yaxis_title, xaxis_tickangle=-90)
        streamlit.plotly_chart(figure)
        
    cname_tcp_sorted = cnames_tcp.sort_values(by="volume", ascending=False)
    cname_udp_sorted = cnames_udp.sort_values(by="volume", ascending=False)
    
    cname_tcp_top = cname_tcp_sorted.head(3)[["cname", "scale"]]
    cname_udp_top = cname_udp_sorted.head(3)[["cname", "scale"]]
        
    # Create pie chart for TCP data using plotly
    fig_tcp = px.pie(cname_tcp_top, names="cname", values="scale", title="")
    fig_tcp.update_layout(legend=dict(orientation="h"))

    # Create pie chart for UDP data using plotly
    fig_udp = px.pie(cname_udp_top, names="cname", values="scale", title="")
    fig_udp.update_layout(legend=dict(orientation="h"))
    
    
    with col1:
        streamlit.dataframe(cname_tcp_sorted.head(3), hide_index=True, use_container_width=True)
        caption = """
        <div style="text-align: justify; font-size: 15px; color: gray;">
            Analysis of TCP flows reveals that CNAME entries containing the term <code>live</code>
            are likely associated with the HAS (HTTP Adaptive Streaming) server, as they account for
            a significant portion of the total download volume recorded across various streaming periods.
            This observation suggests that a regular expression designed to filter primary flows for DAZN
            should include the keyword <code>live</code>. Additionally, the inclusion of the DAZN name
            further enhances the specificity of the filter.
        </div>
        """
        streamlit.markdown(caption, unsafe_allow_html=True)
        streamlit.text("\n")
        streamlit.plotly_chart(fig_tcp)

    with col2:
        streamlit.dataframe(cname_udp_sorted.head(3), hide_index=True, use_container_width=True)
        caption = """
        <div style="text-align: justify; font-size: 15px; color: gray;">
            Analyzing UDP flows indicates that CNAMEs containing the term <code>live</code>
            are similarly indicative of the HAS server, as they represent the majority of the
            recorded download volume across the observed periods. This reinforces the hypothesis that
            a regular expression for filtering DAZN's primary UDP flows should incorporate the keyword
            <code>live</code>. Furthermore, the inclusion of DAZN's name in the CNAME also proves
            to be a valuable criterion for filtering.
        </div>
        """
        streamlit.markdown(caption, unsafe_allow_html=True)
        streamlit.text("\n")
        streamlit.plotly_chart(fig_udp)

