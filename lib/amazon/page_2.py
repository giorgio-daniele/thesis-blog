# Define the imports
import os
import streamlit
import pandas
import itertools
import numpy

import plotly.express as px
import plotly.graph_objects as go

TESTBED_RATES_COLORS = [
    '#000000',  # Black (lowest quality)
    '#8B0000',  # Dark Red
    '#FF0000',  # Red
    '#FF7F00',  # Orange
    '#FFFF00',  # Yellow
    '#00FF00',  # Green
    '#0000FF'   # Blue (highest quality)
]

def downsample_data(x, y, max_points=100):
    if len(x) > max_points:
        step = len(x) // max_points
        x = x[::step]
        y = y[::step]
    return x, y

def cdf_chart(data: dict,  
              var:  str, 
              fam:  str, 
              xaxis_title: str,
              yaxis_title: str,
              chart_title: str):
    
    colors = [
        '#000000',  # Black (lowest quality)
        '#8B0000',  # Dark Red
        '#FF0000',  # Red
        '#FF7F00',  # Orange
        '#FFFF00',  # Yellow
        '#00FF00',  # Green
        '#0000FF'   # Blue (highest quality)
    ]

    # Define the points
    points = {}
    
    figure = go.Figure()
    
    for i, rate in enumerate(data.keys()):
        # Define the x-axis values and the y-axis values
        x = numpy.sort(data[rate][fam][var])
        y = numpy.arange(1, len(x) + 1) / len(x)
        
        # Reduce the data
        x, y = downsample_data(x, y)
        
        points[rate] = len(x)
        
        # Get the color
        color = colors[i]
        
        # Adding the trace
        figure.add_trace(go.Scatter(x=x, 
                                    y=y, mode="lines+markers", 
                                    name=rate,
                                    line=dict(width=2, color=color), 
                                    marker=dict(size=2, color=color)))
        
    # Updating the layout
    figure.update_layout(title=chart_title, 
                         xaxis_title=xaxis_title, 
                         yaxis_title=yaxis_title,
                         xaxis=dict(showgrid=True, gridcolor="lightgray", gridwidth=0.3),
                         yaxis=dict(showgrid=True, gridcolor="lightgray", gridwidth=0.3))
    
    # Render the figure
    streamlit.plotly_chart(figure_or_data=figure)

def sct_chart(data: dict, x_fam: str, x_var: str, y_fam: str, y_var: str,
              xaxis_title: str,
              yaxis_title: str,
              chart_title: str):
    
    colors = [
        '#000000',  # Black (lowest quality)
        '#8B0000',  # Dark Red
        '#FF0000',  # Red
        '#FF7F00',  # Orange
        '#FFFF00',  # Yellow
        '#00FF00',  # Green
        '#0000FF'   # Blue (highest quality)
    ]
    
    # Generate a new figure
    figure = go.Figure()
    
    for i, rate in enumerate(data.keys()):
        x = data[rate][x_fam][x_var]
        y = data[rate][x_fam][y_var]
        
        # Get the color
        color = colors[i]
        
        # Adding the trace
        figure.add_trace(go.Scatter(x=x, 
                                    y=y, mode="markers", name=rate,
                                    marker=dict(size=5, color=color, opacity=0.8)))
        
    # Updating the layout
    figure.update_layout(title=chart_title, 
                         xaxis_title=xaxis_title, 
                         yaxis_title=yaxis_title,
                         xaxis=dict(showgrid=True, gridcolor="lightgray", gridwidth=0.3),
                         yaxis=dict(showgrid=True, gridcolor="lightgray", gridwidth=0.3, type="log"))
    
    # Render the figure
    streamlit.plotly_chart(figure_or_data=figure)

@streamlit.cache_data(show_spinner=True, ttl=10_000)
def load_samples(step: str, proto: str):
    data = {}

    for rate in [1500, 3000, 4500, 6000, 7500, 50000]:

        # Define the folder with the samples
        fold = os.path.join("amazon", "dataset2", f"{str(rate)}kbits", "samples", proto, str(step))

        # Init the dictionary
        data[rate] = {"t": {}, "v": {}, "g": {}}

        # Load all files
        docs  = (os.path.join(fold, f) for f in os.listdir(fold))

        # Limit the files
        files = itertools.islice(docs, 25)
        
        # Generate a unique frame
        frame = pandas.concat((pandas.read_csv(f, sep=" ") for f in files), ignore_index=True)

        # Convert windows limits into milliseconds
        frame["ts"] = frame["ts"] / 1000
        frame["te"] = frame["te"] / 1000  

        # Collect useful temporal metrics
        data[rate]["t"]["avg_span"] = frame["avg_span"].tolist()
        data[rate]["t"]["max_span"] = frame["max_span"].tolist()
        data[rate]["t"]["min_span"] = frame["min_span"].tolist()
        data[rate]["t"]["std_span"] = frame["std_span"].tolist()
        data[rate]["t"]["avg_idle"] = frame["idle"].tolist()

        # Collect useful volumetric metrics
        data[rate]["v"]["s_bytes_all"] = frame["s_bytes_all"].tolist()
        data[rate]["v"]["c_bytes_all"] = frame["c_bytes_all"].tolist()
        data[rate]["v"]["s_pkts_all"]  = frame["s_pkts_all"].tolist()
        data[rate]["v"]["c_pkts_all"]  = frame["c_pkts_all"].tolist()

        if proto == "tcp":
            # Additional volumetric metrics  
            data[rate]["v"]["s_pkts_data"]  = frame["s_pkts_data"].tolist()
            data[rate]["v"]["c_pkts_data"]  = frame["c_pkts_data"].tolist()
            data[rate]["v"]["s_ack_cnt"]    = frame["s_ack_cnt"].tolist()
            data[rate]["v"]["c_ack_cnt"]    = frame["c_ack_cnt"].tolist() 
            data[rate]["v"]["s_ack_cnt_p"]  = frame["s_ack_cnt_p"].tolist()
            data[rate]["v"]["c_ack_cnt_p"]  = frame["c_ack_cnt_p"].tolist()   

        # Define the ground-truth
        data[rate]["g"]["videorate"]   = frame["videorate"].tolist() 

        # Define the statistics
        statistics = {
            "avg_video_rate":    ("videorate",     lambda x: x[x != 0].mean()),
            "avg_c_bytes_all":   ("c_bytes_all",  "mean"),
            "avg_s_bytes_all":   ("s_bytes_all",  "mean"),
            "avg_c_pkts_all":    ("c_pkts_all",   "mean"),
            "avg_s_pkts_all":    ("s_pkts_all",   "mean"),
        }

        if proto == "tcp":
            statistics["avg_s_ack_cnt"]   = ("s_ack_cnt",    "mean")
            statistics["avg_c_ack_cnt"]   = ("c_ack_cnt",    "mean")
            statistics["avg_s_ack_cnt_p"] = ("s_ack_cnt_p",  "mean")
            statistics["avg_c_ack_cnt_p"] = ("c_ack_cnt_p",  "mean")
            statistics["avg_s_pkts_data"] = ("s_pkts_data",  "mean")
            statistics["avg_c_pkts_data"] = ("c_pkts_data",  "mean")

        result = frame.groupby(["ts", "te"], as_index=False).agg(**statistics)

        # Convert timestamps to datetime
        result["xs"] = pandas.to_datetime(result["ts"], origin="unix", unit='s')
        result["xe"] = pandas.to_datetime(result["te"], origin="unix", unit='s')

        # Add the result to current statistics
        data[rate]["statistics"] = result

    return data

def print_tcp():

    # Load samples about TCP
    step     = 10_000
    proto    = "tcp"
    samples  = load_samples(step=step, proto=proto)

    streamlit.caption("### TCP - Volumetric Features (Server Side)")
    col1, col2, col3 = streamlit.columns(3)
    with col1:
        var = "s_bytes_all"
        cdf_chart(data=samples, var=var, fam="v", xaxis_title=var, yaxis_title="probability", chart_title=f"CDF of {var}")
    with col2:
        var = "s_pkts_data"
        cdf_chart(data=samples, var=var, fam="v", xaxis_title=var, yaxis_title="probability", chart_title=f"CDF of {var}")
    with col3:
        x_fet = "s_pkts_data"
        y_fet = "s_bytes_all"
        sct_chart(data=samples, x_fam="v", y_fam="v", x_var=x_fet, y_var=y_fet, xaxis_title=x_fet, yaxis_title=y_fet, chart_title=f"Scatter {x_fet} vs {y_fet}")

    col1, col2, col3, col4 = streamlit.columns(4)
    with col1:
        var = "s_ack_cnt"
        cdf_chart(data=samples, var=var, fam="v", xaxis_title=var, yaxis_title="probability", chart_title=f"CDF of {var}")
    with col2:
        var = "s_ack_cnt_p"
        cdf_chart(data=samples, var=var, fam="v", xaxis_title=var, yaxis_title="probability", chart_title=f"CDF of {var}")
    with col3:
        x_fet = "s_pkts_data"
        y_fet = "s_ack_cnt"
        sct_chart(data=samples, x_fam="v", y_fam="v", x_var=x_fet, y_var=y_fet, xaxis_title=x_fet, yaxis_title=y_fet, chart_title=f"Scatter {x_fet} vs {y_fet}")
    with col4:
        x_fet = "s_pkts_data"
        y_fet = "s_ack_cnt_p"
        sct_chart(data=samples, x_fam="v", y_fam="v", x_var=x_fet, y_var=y_fet, xaxis_title=x_fet, yaxis_title=y_fet, chart_title=f"Scatter {x_fet} vs {y_fet}")

    streamlit.markdown("---")

    streamlit.caption("### TCP - Volumetric Features (Client Side)")
    col1, col2, col3 = streamlit.columns(3)
    with col1:
        var = "c_bytes_all"
        cdf_chart(data=samples, var=var, fam="v", xaxis_title=var, yaxis_title="probability", chart_title=f"CDF of {var}")
    with col2:
        var = "c_pkts_data"
        cdf_chart(data=samples, var=var, fam="v", xaxis_title=var, yaxis_title="probability", chart_title=f"CDF of {var}")
    with col3:
        x_fet = "c_pkts_data"
        y_fet = "c_bytes_all"
        sct_chart(data=samples, x_fam="v", y_fam="v", x_var=x_fet, y_var=y_fet, xaxis_title=x_fet, yaxis_title=y_fet, chart_title=f"Scatter {x_fet} vs {y_fet}")

    col1, col2, col3, col4 = streamlit.columns(4)
    with col1:
        var = "c_ack_cnt"
        cdf_chart(data=samples, var=var, fam="v", xaxis_title=var, yaxis_title="probability", chart_title=f"CDF of {var}")
    with col2:
        var = "c_ack_cnt_p"
        cdf_chart(data=samples, var=var, fam="v", xaxis_title=var, yaxis_title="probability", chart_title=f"CDF of {var}")
    with col3:
        x_fet = "c_pkts_data"
        y_fet = "c_ack_cnt"
        sct_chart(data=samples, x_fam="v", y_fam="v", x_var=x_fet, y_var=y_fet, xaxis_title=x_fet, yaxis_title=y_fet, chart_title=f"Scatter {x_fet} vs {y_fet}")
    with col4:
        x_fet = "c_pkts_data"
        y_fet = "c_ack_cnt_p"
        sct_chart(data=samples, x_fam="v", y_fam="v", x_var=x_fet, y_var=y_fet, xaxis_title=x_fet, yaxis_title=y_fet, chart_title=f"Scatter {x_fet} vs {y_fet}")

    
    streamlit.markdown("---")

    streamlit.caption("### TCP - Temporal Features")
    col1, col2, col3, col4, col5 = streamlit.columns(5)
    with col1:
        var = "avg_idle"
        cdf_chart(data=samples, var=var, fam="t", xaxis_title=f"{var} [ms]", yaxis_title="probability", chart_title=f"CDF of {var}")
    with col2:
        var = "avg_span"
        cdf_chart(data=samples, var=var, fam="t", xaxis_title=f"{var} [ms]", yaxis_title="probability", chart_title=f"CDF of {var}")
    with col3:
        var = "std_span"
        cdf_chart(data=samples, var=var, fam="t", xaxis_title=f"{var} [ms]", yaxis_title="probability", chart_title=f"CDF of {var}")
    with col4:
        var = "max_span"
        cdf_chart(data=samples, var=var, fam="t", xaxis_title=f"{var} [ms]", yaxis_title="probability", chart_title=f"CDF of {var}")
    with col5:
        var = "min_span"
        cdf_chart(data=samples, var=var, fam="t", xaxis_title=f"{var} [ms]", yaxis_title="probability", chart_title=f"CDF of {var}")

def print_udp():
    # Load samples about UDP
    step     = 10_000
    proto    = "udp"
    samples  = load_samples(step=step, proto=proto)

    streamlit.caption("### UDP - Volumetric Features (Server Side)")
    col1, col2, col3 = streamlit.columns(3)
    with col1:
        var = "s_bytes_all"
        cdf_chart(data=samples, var=var, fam="v", xaxis_title=var, yaxis_title="probability", chart_title=f"CDF of {var}")
    with col2:
        var = "s_pkts_all"
        cdf_chart(data=samples, var=var, fam="v", xaxis_title=var, yaxis_title="probability", chart_title=f"CDF of {var}")
    with col3:
        x_fet = "s_pkts_all"
        y_fet = "s_bytes_all"
        sct_chart(data=samples, x_fam="v", y_fam="v", x_var=x_fet, y_var=y_fet, xaxis_title=x_fet, yaxis_title=y_fet, chart_title=f"Scatter {x_fet} vs {y_fet}")

    # col1, col2, col3, col4 = streamlit.columns(4)
    # with col1:
    #     var = "s_ack_cnt"
    #     cdf_chart(data=samples, var=var, fam="v", xaxis_title=var, yaxis_title="probability", chart_title=f"CDF of {var}")
    # with col2:
    #     var = "s_ack_cnt_p"
    #     cdf_chart(data=samples, var=var, fam="v", xaxis_title=var, yaxis_title="probability", chart_title=f"CDF of {var}")
    # with col3:
    #     x_fet = "s_pkts_data"
    #     y_fet = "s_ack_cnt"
    #     sct_chart(data=samples, x_fam="v", y_fam="v", x_var=x_fet, y_var=y_fet, xaxis_title=x_fet, yaxis_title=y_fet, chart_title=f"Scatter {x_fet} vs {y_fet}")
    # with col4:
    #     x_fet = "s_pkts_data"
    #     y_fet = "s_ack_cnt_p"
    #     sct_chart(data=samples, x_fam="v", y_fam="v", x_var=x_fet, y_var=y_fet, xaxis_title=x_fet, yaxis_title=y_fet, chart_title=f"Scatter {x_fet} vs {y_fet}")

    streamlit.markdown("---")

    streamlit.caption("### UDP - Volumetric Features (Client Side)")
    col1, col2, col3 = streamlit.columns(3)
    with col1:
        var = "c_bytes_all"
        cdf_chart(data=samples, var=var, fam="v", xaxis_title=var, yaxis_title="probability", chart_title=f"CDF of {var}")
    with col2:
        var = "c_pkts_all"
        cdf_chart(data=samples, var=var, fam="v", xaxis_title=var, yaxis_title="probability", chart_title=f"CDF of {var}")
    with col3:
        x_fet = "c_pkts_all"
        y_fet = "c_bytes_all"
        sct_chart(data=samples, x_fam="v", y_fam="v", x_var=x_fet, y_var=y_fet, xaxis_title=x_fet, yaxis_title=y_fet, chart_title=f"Scatter {x_fet} vs {y_fet}")

    # col1, col2, col3, col4 = streamlit.columns(4)
    # with col1:
    #     var = "c_ack_cnt"
    #     cdf_chart(data=samples, var=var, fam="v", xaxis_title=var, yaxis_title="probability", chart_title=f"CDF of {var}")
    # with col2:
    #     var = "c_ack_cnt_p"
    #     cdf_chart(data=samples, var=var, fam="v", xaxis_title=var, yaxis_title="probability", chart_title=f"CDF of {var}")
    # with col3:
    #     x_fet = "c_pkts_data"
    #     y_fet = "c_ack_cnt"
    #     sct_chart(data=samples, x_fam="v", y_fam="v", x_var=x_fet, y_var=y_fet, xaxis_title=x_fet, yaxis_title=y_fet, chart_title=f"Scatter {x_fet} vs {y_fet}")
    # with col4:
    #     x_fet = "c_pkts_data"
    #     y_fet = "c_ack_cnt_p"
    #     sct_chart(data=samples, x_fam="v", y_fam="v", x_var=x_fet, y_var=y_fet, xaxis_title=x_fet, yaxis_title=y_fet, chart_title=f"Scatter {x_fet} vs {y_fet}")

    
    streamlit.markdown("---")

    streamlit.caption("### UDP - Temporal Features")
    col1, col2, col3, col4, col5 = streamlit.columns(5)
    with col1:
        var = "avg_idle"
        cdf_chart(data=samples, var=var, fam="t", xaxis_title=f"{var} [ms]", yaxis_title="probability", chart_title=f"CDF of {var}")
    with col2:
        var = "avg_span"
        cdf_chart(data=samples, var=var, fam="t", xaxis_title=f"{var} [ms]", yaxis_title="probability", chart_title=f"CDF of {var}")
    with col3:
        var = "std_span"
        cdf_chart(data=samples, var=var, fam="t", xaxis_title=f"{var} [ms]", yaxis_title="probability", chart_title=f"CDF of {var}")
    with col4:
        var = "max_span"
        cdf_chart(data=samples, var=var, fam="t", xaxis_title=f"{var} [ms]", yaxis_title="probability", chart_title=f"CDF of {var}")
    with col5:
        var = "min_span"
        cdf_chart(data=samples, var=var, fam="t", xaxis_title=f"{var} [ms]", yaxis_title="probability", chart_title=f"CDF of {var}")

# Main function
def main():
    
    streamlit.title("Live Streaming Flows Metrics")

    print_tcp()
    print_udp()