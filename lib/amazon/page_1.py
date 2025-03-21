import os
import pandas
import humanize
import streamlit

import plotly.express as px

# log identifiers
LOG_TCP_COMPLETE = "log_tcp_complete"
LOG_TCP_PERIODIC = "log_tcp_periodic"
LOG_UDP_COMPLETE = "log_udp_complete"
LOG_UDP_PERIODIC = "log_udp_periodic"
LOG_BOT_COMPLETE = "log_bot_complete"
LOG_HAR_COMPLETE = "log_har_complete"

def format_time(tstamp: pandas.Timestamp):
    seconds = (tstamp - pandas.Timestamp("1970-01-01")) // pandas.Timedelta('1s')
    return f"{seconds // 60:02}:{seconds % 60:02}"

def format_volume(volume: int):
    return humanize.naturalsize(volume, binary=True, format="%.2f")

def tcp_info(record: pandas.Series):
    return (
        f"<b>xs</b>={format_time(record['xs'])}<br>"
        f"<b>xe</b>={format_time(record['xe'])}<br>"
        f"<b>CNAME</b>: {record['cname']}<br>"
        f"<b>ts</b>:  {format_time(record['xs'])}<br>"
        f"<b>te</b>:  {format_time(record['xe'])}<br><br>"
        f"<b>Client Socket</b>: {record['c_ip']}:{record['c_port']}<br>"
        f"<b>Server Socket</b>: {record['s_ip']}:{record['s_port']}<br>"
        f"<b>Client bytes</b>:   {format_volume(record['c_bytes_all'])}<br>"
        f"<b>Server bytes</b>:   {format_volume(record['s_bytes_all'])}<br>"
    )

def udp_info(record: pandas.Series):
    return (
        f"<b>xs</b>: {format_time(record['xs'])}<br>"
        f"<b>xe</b>: {format_time(record['xe'])}<br>"
        f"<b>cname</b>: {record['cname']}<br>"
        f"<b>ts</b>:  {format_time(record['xs'])}<br>"
        f"<b>te</b>:  {format_time(record['xe'])}<br><br>"
        f"<b>client socket</b>: {record['c_ip']}:{record['c_port']}<br>"
        f"<b>server socket</b>: {record['s_ip']}:{record['s_port']}<br>"
        f"<b>client bytes</b>:   {format_volume(record['c_bytes_all'])}<br>"
        f"<b>Server bytes</b>:   {format_volume(record['s_bytes_all'])}<br>"
    )

def http_info(record: pandas.Series):
    if record["mime"] == "video/mp4":
        return (
            f"<b>xs</b>: {format_time(record['ts'])}<br>"
            f"<b>xe</b>: {format_time(record['te'])}<br>"
            f"<b>Video quality</b>: {(record['video_rate'])} kbps<br>"
        )
    if record["mime"] == "audio/mp4":
        return (
            f"<b>xs</b>: {format_time(record['ts'])}<br>"
            f"<b>xe</b>: {format_time(record['te'])}<br>"
            f"<b>Audio quality</b>: {(record['audio_rate'])} kbps<br>"
        )


def get_number(name: str):
    return int(name.split("-")[1]) if "-" in name else 0

def time_axis(min_value, max_value):
    values = pandas.date_range(start=min_value, end=max_value, freq="10s")
    labels = [v.strftime("%M:%S") for v in values]
    return values, labels

def plot_timeline(frame: pandas.DataFrame, events: pandas.DataFrame, x_start: str, x_end: str, y: str, color: str, 
                  xaxis_title: str, 
                  yaxis_title: str, 
                  chart_title: str):
    
    # Calculate the number of categories and define chart height
    num_categories      = frame[y].nunique()
    height_per_category = 40
    chart_height        = max(220, num_categories * height_per_category)
    
    # Define color for a streaming period
    yellow = "rgba(255,255,0,0.2)"
    
    # Generate a new figure
    figure = px.timeline(frame, 
                         x_start=x_start, 
                         x_end=x_end, y=y, color=color, custom_data="info")
    
    # Add hovertemplate
    figure.update_traces(hovertemplate="%{customdata[0]}<extra></extra>")
    
    # Define the x-axis boundaries
    min_x_axis_value = pandas.Timestamp('1970-01-01 00:00:00')
    max_x_axis_value = max(events, key=lambda x: x[1])[1]
    
    # Define the xaxis values and labels
    xaxis_values, xaxis_labels = time_axis(min_value=min_x_axis_value, 
                                           max_value=pandas.to_datetime(max_x_axis_value, unit="ms", origin="unix"))
    
    for event in events:
        ts = pandas.to_datetime(event[0], unit="ms", origin="unix")
        te = pandas.to_datetime(event[1], unit="ms", origin="unix")
        figure.add_vrect(x0=ts, x1=te, fillcolor=yellow, line_width=0)
        
    figure.update_layout(title=dict(text=chart_title, 
                                    font=dict(size=13)), 
                         xaxis_title=xaxis_title, 
                         yaxis_title=yaxis_title,
                         showlegend=True, 
                         height=chart_height,
                         xaxis=dict(showgrid=True, gridcolor="lightgray", gridwidth=0.3, tickvals=xaxis_values, ticktext=xaxis_labels), 
                         yaxis=dict(showgrid=True, gridcolor="lightgray", gridwidth=0.3))
    # Render the image
    streamlit.plotly_chart(figure_or_data=figure)

def periods(path: str):
    pattern = "sniffer|browser|origin|net|app"

    frame = pandas.read_csv(path, sep=r"\s+")
    frame = frame[~frame["event"].str.contains(pattern, case=False, na=False)]
    frame = frame.reset_index(drop=True)

    return [
        (frame.loc[i, "rel"], frame.loc[i + 1, "rel"]) 
            for i in range(0, len(frame) - 1, 2)]

def tcp(test: str):

    # Define the title of the section
    streamlit.caption("## Layer 4 Protocol TCP")

    # Load data
    complete  = pandas.read_csv(os.path.join(test, LOG_TCP_COMPLETE), sep=" ")
    periodic  = pandas.read_csv(os.path.join(test, LOG_TCP_PERIODIC), sep=" ")
    events    = periods(os.path.join(test, LOG_BOT_COMPLETE))

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
    cnames = streamlit.multiselect("Select CNAMEs from in TCP flows", sorted(set(complete["cname"])))

    # Filter data based on selected Canonical Names
    selected_complete = complete[complete["cname"].isin(cnames)]
    selected_periodic = periodic[periodic["cname"].isin(cnames)]
    
    # If the CNAMEs are not selected, return
    if cnames:
        xaxis_title = "time [mm:ss]"
        yaxis_title = "id [#]"
        chart_title = "TCP flows reconstructed by Tstat in log_tcp_complete"
        plot_timeline(frame=selected_complete, events=events, x_start=xs, x_end=xe, y="id", color="cname",
                    xaxis_title=xaxis_title,
                    yaxis_title=yaxis_title,
                    chart_title=chart_title)
        
        xaxis_title = "time [mm:ss]"
        yaxis_title = "id [#]"
        chart_title = "TCP flows reconstructed by Tstat in log_tcp_periodic"
        plot_timeline(frame=selected_periodic, events=events, x_start=xs, x_end=xe, y="id", color="cname",
                      xaxis_title=xaxis_title,
                      yaxis_title=yaxis_title,
                      chart_title=chart_title)
    else:
        streamlit.warning("Nothing to see here, you do not have selected any CNAME")
        return

def udp(test: str):
    
    # Define the title of the section
    streamlit.caption("## Layer 4 Protocol UDP")
    
    # Load data
    complete  = pandas.read_csv(os.path.join(test, LOG_UDP_COMPLETE), sep=" ")
    periodic  = pandas.read_csv(os.path.join(test, LOG_UDP_PERIODIC), sep=" ")
    events    = periods(os.path.join(test, LOG_BOT_COMPLETE))

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
    cnames = streamlit.multiselect("Select CNAMEs from in UDP flows", sorted(set(complete["cname"])))

    # Filter data based on selected Canonical Names
    selected_complete = complete[complete["cname"].isin(cnames)]
    selected_periodic = periodic[periodic["cname"].isin(cnames)]
    
    # If the CNAMEs are not selected, return
    if cnames:
        xaxis_title = "time [mm:ss]"
        yaxis_title = "id [#]"
        chart_title = "UDP flows reconstructed by Tstat in log_udp_complete"
        plot_timeline(frame=selected_complete, events=events, x_start=xs, x_end=xe, y="id", color="cname",
                      xaxis_title=xaxis_title,
                      yaxis_title=yaxis_title,
                      chart_title=chart_title)
        
        xaxis_title = "time [mm:ss]"
        yaxis_title = "id [#]"
        chart_title = "UDP flows reconstructed by Tstat in log_udp_periodic"
        plot_timeline(frame=selected_periodic, events=events, x_start=xs, x_end=xe, y="id", color="cname",
                      xaxis_title=xaxis_title,
                      yaxis_title=yaxis_title,
                      chart_title=chart_title)
    else:
        streamlit.warning("Nothing to see here, you do not have selected any CNAME")
        return

def http(test: str):
    
    # Define the title of the section
    streamlit.caption("## Layer 7 Protocol HTTP")
    
    # Load data
    requests = pandas.read_csv(os.path.join(test, LOG_HAR_COMPLETE), sep=" ")
    events   = periods(os.path.join(test, LOG_BOT_COMPLETE))

    # Define x and y values
    xs, xe = "ts",   "te"
    id, cl = "mime", "mime"

    # Convert timestamps to datetime
    requests[xs] = pandas.to_datetime(requests["ts"], unit="ms", origin="unix")
    requests[xe] = pandas.to_datetime(requests["te"], unit="ms", origin="unix")

    # Add info
    requests["info"] = requests.apply(http_info, axis=1)

    xaxis_title = "time [mm:ss]"
    yaxis_title = "mime-type []"
    chart_title = "HTTP flow reconstructed in log_har_complete"
    plot_timeline(frame=requests, events=events, x_start=xs, x_end=xe, y=id, color=cl,
                  xaxis_title=xaxis_title,
                  yaxis_title=yaxis_title,
                  chart_title=chart_title)
    
def main():
    
    streamlit.title("Supervised Experiments")

    root = None
    test = None
    band = None
    
    col1, col2, col3 = streamlit.columns(3)

    with col1:
        # Define the dataset to use
        root = streamlit.selectbox("Choose testbed bandwidth", ["dataset1", "dataset2"])

    with col2:
        path = os.path.join("amazon", root)

        if root == "dataset1":
            path = os.path.join(path, "tests")
            opts = sorted(os.listdir(path), key=get_number) if os.path.exists(path) else []
            test = streamlit.selectbox("Choose supervised test", options=opts[:25] if opts else ["no tests available"])

        elif root == "dataset2":
            opts = sorted(os.listdir(path)) if os.path.exists(path) else []
            band = streamlit.selectbox("Choose tested bandwidth", options=opts if opts else ["no bands available"])

    with col3:
        if root == "dataset1":
            _ = streamlit.selectbox("Choose extra option for dataset1", options=[])
        elif root == "dataset2" and band:
            path = os.path.join(path, band, "tests")
            opts = sorted(os.listdir(path), key=get_number) if os.path.exists(path) else []
            test = streamlit.selectbox("Choose supervised test", options=opts[:25] if opts else ["no tests available"])

    # Display the result
    if test and test != "no tests available":
        tcp(test=os.path.join(path,  test))
        udp(test=os.path.join(path,  test))
        http(test=os.path.join(path, test))