import enum
import pandas
import streamlit
import plotly.express as px
import plotly.graph_objects as go
import numpy


TEMPLATE = None
OPACITY  = 1.0
LIMIT    = 20

# enum for different log document types
class Document(enum.Enum):
    LOG_TCP_COMPLETE = 1
    LOG_TCP_PERIODIC = 2
    LOG_UDP_COMPLETE = 3
    LOG_UDP_PERIODIC = 4
    LOG_HAR_COMPLETE = 5

    
# enum for different protocols
class Protocol(enum.Enum):
    TCP  = 1
    UDP  = 2
    HTTP = 3

# log identifiers
LOG_TCP_COMPLETE = "log_tcp_complete"
LOG_TCP_PERIODIC = "log_tcp_periodic"
LOG_UDP_COMPLETE = "log_udp_complete"
LOG_UDP_PERIODIC = "log_udp_periodic"
LOG_BOT_COMPLETE = "log_bot_complete"
LOG_HAR_COMPLETE = "log_har_complete"

# restbed bitrate conditions
TESTBED_RATES = ["1500kbits", "3000kbits", "4500kbits", "6000kbits", "7500kbits", "50000kbits"]

# colors associated with testbed rates
TESTBED_RATES_COLORS = [
    '#8B0000',   # dark red
    '#FF0000',   # red
    '#FF4500',   # orange red
    '#FF7F00',   # orange
    '#FFFF00',   # yellow
    '#00FF00'    # green
]


# colors associated to testbed
TESTBED_RATES_COLORS = [
   '#8B0000',   # dark Red
    '#FF0000',  # red
    '#FF4500',  # orange Red
    '#FF7F00',  # orange
    '#FFFF00',  # yellow
    '#00FF00'   # green
]


def time_axis(min_value, max_value):
    values = pandas.date_range(start=min_value, end=max_value, freq="10s")
    labels = [v.strftime("%M:%S") for v in values]
    return values, labels

def periods(path: str):
    pattern = "sniffer|browser|origin|net|app"

    frame = pandas.read_csv(path, sep=r"\s+")
    frame = frame[~frame["event"].str.contains(pattern, case=False, na=False)]
    frame = frame.reset_index(drop=True)

    return [
        (frame.loc[i, "rel"], frame.loc[i + 1, "rel"]) 
            for i in range(0, len(frame) - 1, 2)]

def format_time(tstamp: pandas.Timestamp):
    """Convert a Timestamp to mm:ss format."""
    # Convert Timestamp to seconds since the Unix epoch
    seconds = (tstamp - pandas.Timestamp("1970-01-01")) // pandas.Timedelta('1s')
    # Format as mm:ss
    return f"{int(seconds // 60):02}:{int(seconds % 60):02}"


def format_volume(volume: int):
    for unit in ["B", "KiB", "MiB", "GiB", "TiB"]:
        if volume < 1024:
            return f"{volume:2.2f} {unit}"
        volume /= 1024


def tcp_info(record: pandas.Series):
    return (
        f"<b>xs</b>={format_time(record['xs'])}<br>"
        f"<b>xe</b>={format_time(record['xe'])}<br>"
        f"<b>CNAME</b>={record['cn']}<br>"
        f"<b>Client IP</b>={record['c_ip']}<br>"
        f"<b>Server IP</b>={record['s_ip']}<br>"
        f"<b>Client Port</b>={record['c_port']}<br>"
        f"<b>Server Port</b>={record['s_port']}<br>"
        f"<b>Client Bytes</b>={format_volume(record['c_bytes_all'])}<br>"
        f"<b>Server Bytes</b>={format_volume(record['s_bytes_all'])}<br>"
    )

def udp_info(record: pandas.Series):
    return (
        f"<b>xs</b>={format_time(record['xs'])}<br>"
        f"<b>xe</b>={format_time(record['xe'])}<br>"
        f"<b>CNAME</b>={record['cn']}<br>"
        f"<b>Client IP</b>={record['c_ip']}<br>"
        f"<b>Server IP</b>={record['s_ip']}<br>"
        f"<b>Client Port</b>={record['c_port']}<br>"
        f"<b>Server Port</b>={record['s_port']}<br>"
        f"<b>Client Bytes</b>={format_volume(record['c_bytes_all'])}<br>"
        f"<b>Server Bytes</b>={format_volume(record['s_bytes_all'])}<br>"
    )

def http_info(record: pandas.Series):
    return (
        f"<b>xs</b>={format_time(record['xs'])}<br>"
        f"<b>xe</b>={format_time(record['xe'])}<br>"
        #f"<b>URL</b>={record['url']:40}<br>"
    )

def timeline(data: pandas.DataFrame, 
             evns: pandas.DataFrame, xs: str, xe: str, y: str, color: str, xtitle: str, ytitle: str, ctitle: str):

    # Create a new figure
    fig = px.timeline(data, x_start=xs, x_end=xe, y=y, color=color, custom_data="info")

    # Show only custom info
    fig.update_traces(hovertemplate="%{customdata[0]}")

    # Define x-axis values and labels
    values, labels = time_axis(min_value=pandas.Timestamp('1970-01-01 00:00:00'), 
                               max_value=pandas.to_datetime(max(evns, key=lambda x: x[1])[1], unit="ms", origin="unix"))
    
    # For each streaming period, use pale yellow to highligth
    # the time period
    for evn in evns:
        x0 = pandas.to_datetime(evn[0], unit="ms", origin="unix")
        x1 = pandas.to_datetime(evn[1], unit="ms", origin="unix")

        # Add highligthed region for displaying the period
        fig.add_vrect(x0=x0, x1=x1, fillcolor="rgba(255,255,0,0.1)", line_width=0)
    
    # Update the chart
    fig.update_layout(
        xaxis=dict(
            tickvals=values,
            ticktext=labels,
            tickformat="%M:%S",
            tickfont=dict(size=12),
            title=xtitle,
            showgrid=True
        ),
        yaxis=dict(
            tickfont=dict(size=12),
            title=ytitle,
            showgrid=True
        ),
        title=dict(
            text=ctitle,
            font=dict(size=13)
        ),
        showlegend=True
    )

    # Show the plot
    streamlit.plotly_chart(fig, use_container_width=True)


def plot_trend(x: str, y: str, xtitle: str, ytitle: str, ctitle: str, media: dict, noise: dict | None):

    fig = go.Figure()

    for i, (rate, frame) in enumerate(media.items()):

        color = TESTBED_RATES_COLORS[i]
        # mean = frame[y].mean()

        # Add trace for the rate
        fig.add_trace(go.Scatter(x=frame[x],
                                 y=frame[y], 
                                 mode="lines+markers", 
                                 line=dict(color=color, width=1),
                                 marker=dict(color=color, size=3), name=rate))

        # # Add a horizontal dotted line at the average y value
        # fig.add_trace(go.Scatter(x=[frame[x].min(), frame[x].max()],
        #                          y=[mean] * 2,
        #                          mode="lines",
        #                          name=f"avg at {rate}",
        #                          line=dict(color=color, width=1, dash='dot')))

    # Update the chart
    fig.update_layout(
        xaxis=dict(
            tickformat="%M:%S",
            tickfont=dict(size=12),
            title=xtitle,
            showgrid=True
        ),
        yaxis=dict(
            tickfont=dict(size=12),
            title=ytitle,
            showgrid=True
        ),
        title=dict(
            text=ctitle,
            font=dict(size=13)
        ),
        showlegend=True
    )

    streamlit.plotly_chart(fig, use_container_width=True)

def plot_scatter(x: str, y: str, xtitle: str, ytitle: str, ctitle: str, media: dict, noise: dict | None):

    fig = go.Figure()

    for i, (rate, frame) in enumerate(media.items()):

        color = TESTBED_RATES_COLORS[i]

        # Add trace for the rate
        fig.add_trace(go.Scatter(x=frame[x],
                                 y=frame[y], 
                                 mode="markers", 
                                 line=dict(color=color, width=1),
                                 marker=dict(color=color, size=3), name=rate))
    # Update the chart
    fig.update_layout(
        xaxis=dict(
            tickformat="%M:%S",
            tickfont=dict(size=12),
            title=xtitle,
            showgrid=True
        ),
        yaxis=dict(
            tickfont=dict(size=12),
            title=ytitle,
            showgrid=True
        ),
        title=dict(
            text=ctitle,
            font=dict(size=13)
        ),
        showlegend=True
    )

    streamlit.plotly_chart(fig, use_container_width=True)

def cumulative_function(x: str, xtitle: str,  ytitle: str, ctitle: str, media: dict, noise: dict | None):

    fig = go.Figure()

    for i, (rate, frame) in enumerate(media.items()):

        # extract x data
        x_values = frame[x]
        x_vals   = numpy.sort(x_values)
        y_vals   = numpy.arange(1, len(x_vals) + 1) / len(x_vals)

        color = TESTBED_RATES_COLORS[i]

        # add the CDF as a trace to the plot
        fig.add_trace(go.Scatter(x=x_vals, 
                                 y=y_vals,
                                 mode="lines+markers", 
                                 line=dict(color=color, width=1),
                                 marker=dict(color=color, size=3), name=rate))

    # Update the chart
    fig.update_layout(
        xaxis=dict(
            tickformat="%M:%S",
            tickfont=dict(size=12),
            title=xtitle,
            showgrid=True
        ),
        yaxis=dict(
            tickfont=dict(size=12),
            title=ytitle,
            showgrid=True
        ),
        title=dict(
            text=ctitle,
            font=dict(size=13)
        ),
        showlegend=True
    )

    streamlit.plotly_chart(fig, use_container_width=True)
