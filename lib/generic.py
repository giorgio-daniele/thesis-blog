import enum
import pandas
import streamlit
import numpy
import plotly.express as px
import plotly.graph_objects as go

import random
import string
import kaleido


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

# Testbed bitrate conditions
TESTBED_RATES = ["1500kbits", "3000kbits", "4500kbits", "6000kbits", "7500kbits", "50000kbits"]

TESTBED_RATES_COLORS = [
    '#000000',  # Black (low quality)
    '#6A1B9A',  # Medium purple
    '#9C27B0',  # Vibrant purple
    '#FF0000',  # Red
    '#D4A200',  # Yellow
    '#00AF00'   # Green orange (high quality)
]

def generate_random_filename(extension="svg", length=8):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length)) + f".{extension}"

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
    seconds = (tstamp - pandas.Timestamp("1970-01-01")) // pandas.Timedelta('1s')
    return f"{int(seconds // 60):02}:{int(seconds % 60):02}"


def format_volume(volume: int):
    for unit in ["B", "KiB", "MiB", "GiB", "TiB"]:
        if volume < 1024:
            return f"{volume:2.2f} {unit}"
        volume /= 1024


def tcp_info(record: pandas.Series):
    return (
        f"<b>CNAME</b>: {record['cn']}<br>"
        f"<b>ts</b>:  {format_time(record['xs'])}<br>"
        f"<b>te</b>: {format_time(record['xe'])}<br><br>"
        f"<b>Client Socket</b>: {record['c_ip']}:{record['c_port']}<br>"
        f"<b>Server Socket</b>: {record['s_ip']}:{record['s_port']}<br>"
        f"<b>Client Data</b>:  {format_volume(record['c_bytes_all'])}<br>"
        f"<b>Server Data</b>:  {format_volume(record['s_bytes_all'])}<br>"
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
    if record["mime"] == "video":
        return (
            f"<b>xs</b>: {format_time(record['xs'])}<br>"
            f"<b>xe</b>: {format_time(record['xe'])}<br>"
            f"<b>Video quality</b>: {(record['video_rate'])} kbps<br>"
        )
    if record["mime"] == "audio":
        return (
            f"<b>xs</b>: {format_time(record['xs'])}<br>"
            f"<b>xe</b>: {format_time(record['xe'])}<br>"
            f"<b>Audio quality</b>: {(record['audio_rate'])} kbps<br>"
        )


def downsample_data(x, y, max_points=100):
    if len(x) > max_points:
        step = len(x) // max_points
        x = x[::step]
        y = y[::step]
    return x, y

def plot_timeline(data: pandas.DataFrame, 
                  evns: pandas.DataFrame, xs: str, xe: str, y: str, color: str, 
                  xaxis_title: str, 
                  yaxis_title: str, 
                  chart_title: str):

    # Create a new figure
    figure = px.timeline(data, x_start=xs, x_end=xe, y=y, color=color, custom_data="info")

    # Show only custom info
    figure.update_traces(hovertemplate="%{customdata[0]}")

    # Define x-axis values and labels
    values, labels = time_axis(min_value=pandas.Timestamp('1970-01-01 00:00:00'), 
                               max_value=pandas.to_datetime(max(evns, key=lambda x: x[1])[1], unit="ms", origin="unix"))
    
    # For each streaming period, use pale yellow to highligth
    for evn in evns:
        x0 = pandas.to_datetime(evn[0], unit="ms", origin="unix")
        x1 = pandas.to_datetime(evn[1], unit="ms", origin="unix")

        # Add highligthed region for displaying the period
        figure.add_vrect(x0=x0, x1=x1, fillcolor="rgba(255,255,0,0.1)", line_width=0)
    
    # Update the chart
    figure.update_layout(
        xaxis=dict(tickvals=values, ticktext=labels, tickformat="%M:%S", tickfont=dict(size=12), title=xaxis_title, showgrid=True),
        yaxis=dict(tickfont=dict(size=12), title=yaxis_title, showgrid=True),
        title=dict(text=chart_title, font=dict(size=13)), showlegend=True)

    # Show the plot
    streamlit.plotly_chart(figure, use_container_width=True)

    
def plot_cumulative_function(series: dict, x_family: str, x_feature: str,
                             xaxis_title: str,
                             yaxis_title: str,
                             chart_title: str, caption: str | None):
    
    points = {}
    
    # Generate a new figure
    figure = go.Figure()
    
    for i, rate in enumerate(series.keys()):
        x = numpy.sort(series[rate][x_family][x_feature])
        y = numpy.arange(1, len(x) + 1) / len(x)
        
        x, y = downsample_data(x, y)
        
        points[rate] = len(x)
        
        # Get the color
        color = TESTBED_RATES_COLORS[i]
        
        # Adding the trace
        figure.add_trace(go.Scatter(x=x, y=y, mode="lines+markers", name=rate,
                                    line=dict(width=2, color=color), marker=dict(size=2, color=color)))
        
    # Updating the layout
    figure.update_layout(title=chart_title, 
                         xaxis_title=xaxis_title, 
                         yaxis_title=yaxis_title,
                         xaxis=dict(showgrid=True, gridcolor="lightgray", gridwidth=0.3),
                         yaxis=dict(showgrid=True, gridcolor="lightgray", gridwidth=0.3))
    
    # Render the figure
    streamlit.plotly_chart(figure_or_data=figure)
    
    if caption is not None:
        streamlit.markdown(
            f"""<div style="text-align: justify; font-size: 15px; color: gray;">{caption} </div>""", 
            unsafe_allow_html=True)
    
def plot_scattering_function(series: dict, 
                             x_family: str, x_feature: str,
                             y_family: str, y_feature: str,
                             xaxis_title: str,
                             yaxis_title: str,
                             chart_title: str, caption: str | None):
    
    # Generate a new figure
    figure = go.Figure()
    
    for i, rate in enumerate(series.keys()):
        x = series[rate][x_family][x_feature]
        y = series[rate][y_family][y_feature]
        
        # Get the color
        color = TESTBED_RATES_COLORS[i]
        
        # Adding the trace
        figure.add_trace(go.Scatter(x=x, y=y, mode="markers", name=rate,
                                    marker=dict(size=5, color=color, opacity=0.8)))
        
    # Updating the layout
    figure.update_layout(title=chart_title, 
                         xaxis_title=xaxis_title, 
                         yaxis_title=yaxis_title,
                         xaxis=dict(showgrid=True, gridcolor="lightgray", gridwidth=0.3),
                         yaxis=dict(showgrid=True, gridcolor="lightgray", gridwidth=0.3, type="log"))
    
    # Render the figure
    streamlit.plotly_chart(figure_or_data=figure)
    
    if caption is not None:
        streamlit.markdown(
            f"""<div style="text-align: justify; font-size: 15px; color: gray;">{caption} </div>""", 
            unsafe_allow_html=True)

def plot_trend_function(x_family: str, x_feature: str,
                        y_family: str, y_feature: str,
                        xaxis_title: str, 
                        yaxis_title: str, 
                        chart_title: str, series: dict, caption: str | None):
    
    figure = go.Figure()

    for i, (rate, frame) in enumerate(series.items()):
        
        xvalues = frame[x_family][x_feature]
        yvalues = frame[y_family][y_feature]

        # Define the color to use
        color = TESTBED_RATES_COLORS[i]

        # Add trace for the rate
        figure.add_trace(go.Scatter(x=xvalues,
                                    y=yvalues, 
                                    mode="lines+markers", 
                                    line=dict(color=color, width=1),
                                    marker=dict(color=color, size=3), name=rate))
        
        # Compute the average y-value
        avg_y = numpy.mean(yvalues)
        
        # Add an annotation for the average y-value
        figure.add_annotation(
            x=xvalues.iloc[-1], y=avg_y, text=f"Avg: {format_volume(avg_y)}",
            showarrow=False, font=dict(size=8, color=color, family="Courier"), bgcolor="white", opacity=1.0)
        
    # Updating the layout
    figure.update_layout(title=chart_title, 
                         xaxis_title=xaxis_title, 
                         yaxis_title=yaxis_title,
                         xaxis=dict(showgrid=True, gridcolor="lightgray", gridwidth=0.3),
                         yaxis=dict(showgrid=True, gridcolor="lightgray", gridwidth=0.3))
    
    # Render the figure
    streamlit.plotly_chart(figure_or_data=figure)
    
    if caption is not None:
        streamlit.markdown(
            f"""<div style="text-align: justify; font-size: 15px; color: gray;">{caption} </div>""", 
            unsafe_allow_html=True)