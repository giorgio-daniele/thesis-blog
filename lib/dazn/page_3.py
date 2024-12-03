import os
import pandas    as pd
import streamlit as st

from lib.generic import LIMIT
from lib.generic import TESTBED_RATES

from lib.generic import plot_cumulative_function
from lib.generic import plot_scattering_function
from lib.generic import plot_trend_function

from lib.generic import trend_function_caption
from lib.generic import cumulative_function_caption
from lib.generic import scatter_plot_caption


SERVER = "dazn"

@st.cache_data(show_spinner=True, ttl=10_000)
def load_tcp(step: str):
    samples = {}

    for rate in TESTBED_RATES:
        # Define the directory
        dir = os.path.join(SERVER, rate, "samples", "tcp", str(step))
        
        # Init the value
        samples[rate] = {"temporal": {}, "volumetric": {}, "groundtruth": {}}

        # Generate a unique dataframe with all periods conducted
        frame = pd.concat(
            [pd.read_csv(os.path.join(dir, file), sep=" ") 
                for file in os.listdir(dir)][:LIMIT], ignore_index=True)

        # Convert timestamps from millisecond to seconds
        frame["ts"] = frame["ts"] / 1000
        frame["te"] = frame["te"] / 1000  
        
        # Collect temporal statistics
        samples[rate]["temporal"]["avg_span"] = frame["avg_span"].tolist()
        samples[rate]["temporal"]["avg_idle"] = frame["idle"].tolist()
        
        # Collect volumetric statistics
        samples[rate]["volumetric"]["s_bytes_all"]  = frame["s_bytes_all"].tolist()
        samples[rate]["volumetric"]["c_bytes_all"]  = frame["c_bytes_all"].tolist()
        samples[rate]["volumetric"]["s_bytes_uniq"] = frame["s_bytes_uniq"].tolist()
        samples[rate]["volumetric"]["c_bytes_uniq"] = frame["c_bytes_uniq"].tolist()
        samples[rate]["volumetric"]["s_ack_cnt"]    = frame["s_ack_cnt"].tolist()
        samples[rate]["volumetric"]["c_ack_cnt"]    = frame["c_ack_cnt"].tolist()
        
        # Collect groundtruth statitistics
        samples[rate]["groundtruth"]["avg_video_rate"] = frame["avg_video_rate"].tolist()

        # Define statistics aggregated by [ts; te]
        statistics = {
            "avg_video_rate":    ("avg_video_rate", lambda x: x[x != 0].mean()),
            "avg_c_bytes_all":   ("c_bytes_all",  "mean"),
            "avg_s_bytes_all":   ("s_bytes_all",  "mean"),
        }

        # Group rows at each rate by using the time period
        data = frame.groupby(["ts", "te"], as_index=False).agg(**statistics)

        # Convert timestamps to datetime
        data["xs"] = pd.to_datetime(data["ts"], origin="unix", unit='s')
        data["xe"] = pd.to_datetime(data["te"], origin="unix", unit='s')

        samples[rate]["statistics"] = data

    return samples

@st.cache_data(show_spinner=True, ttl=10_000)
def load_udp(step: str):
    samples = {}

    for rate in TESTBED_RATES:
        # Define the directory
        dir = os.path.join(SERVER, rate, "samples", "udp", str(step))
        
        # Init the value
        samples[rate] = {"temporal": {}, "volumetric": {}, "groundtruth": {}}

        # Generate a unique dataframe with all periods conducted
        frame = pd.concat(
            [pd.read_csv(os.path.join(dir, file), sep=" ") 
                for file in os.listdir(dir)][:LIMIT], ignore_index=True)

        # Convert timestamps from millisecond to seconds
        frame["ts"] = frame["ts"] / 1000
        frame["te"] = frame["te"] / 1000  
        
        # Collect temporal statistics
        samples[rate]["temporal"]["avg_span"] = frame["avg_span"].tolist()
        samples[rate]["temporal"]["avg_idle"] = frame["idle"].tolist()
        
        # Collect volumetric statistics
        samples[rate]["volumetric"]["s_bytes_all"]  = frame["s_bytes_all"].tolist()
        samples[rate]["volumetric"]["c_bytes_all"]  = frame["c_bytes_all"].tolist()

        # Collect groundtruth statitistics
        samples[rate]["groundtruth"]["avg_video_rate"] = frame["avg_video_rate"].tolist()

        # Define statistics aggregated by [ts; te]
        statistics = {
            "avg_video_rate":    ("avg_video_rate", lambda x: x[x != 0].mean()),
            "avg_c_bytes_all":   ("c_bytes_all",  "mean"),
            "avg_s_bytes_all":   ("s_bytes_all",  "mean"),
        }

        # Group rows at each rate by using the time period
        data = frame.groupby(["ts", "te"], as_index=False).agg(**statistics)

        # Convert timestamps to datetime
        data["xs"] = pd.to_datetime(data["ts"], origin="unix", unit='s')
        data["xe"] = pd.to_datetime(data["te"], origin="unix", unit='s')

        samples[rate]["statistics"] = data

    return samples

        
def main():
    
    st.title("HAS (DASH) flows metrics")

    # Define the step at which data are visualized
    step = st.select_slider("Select step value", 
                            options=[i * 1000 for i in range(1, 11)], value=10_000, 
                            format_func=lambda x: f"{x / 1000} seconds")
    """
    =============================
    =    Processing TCP Layer   =
    =============================
    """

    st.markdown("### TCP")
    protocol = "TCP"
    samples  = load_tcp(step=step)
    
    st.caption("#### Temporal metrics")
    col1, col2 = st.columns(2)
    with col1:
        side        = "server-to-client, and viceversa"
        x_family    = "temporal"
        x_feature   = "avg_span"
        xaxis_title = "time [ms]"
        yaxis_title = "probability [%]"
        chart_title = "Cumulative Distribution Function (CDF) of avg_bin_span"
        description = cumulative_function_caption(feature=x_feature, protocol=protocol, step=step, side=side)
        plot_cumulative_function(series=samples, x_family=x_family, x_feature=x_feature,
                                 xaxis_title=xaxis_title,
                                 yaxis_title=yaxis_title,
                                 chart_title=chart_title, caption=description)
        
    with col2:
        side        = "server-to-client, and viceversa"
        x_family    = "temporal"
        x_feature   = "avg_idle"
        xaxis_title = "time [ms]"
        yaxis_title = "probability [%]"
        chart_title = "Cumulative Distribution Function (CDF) of idle"
        description = cumulative_function_caption(feature=x_feature, protocol=protocol, step=step, side=side)
        plot_cumulative_function(series=samples, x_family=x_family, x_feature=x_feature,
                                 xaxis_title=xaxis_title,
                                 yaxis_title=yaxis_title,
                                 chart_title=chart_title, caption=description)

    st.caption("#### Volumetric metrics")
    col1, col2 = st.columns(2)
    with col1:
        side        = "server-to-client"
        feature     = "idle"
        x_family    = "volumetric"
        x_feature   = "s_bytes_all"
        xaxis_title = "byte [B]"
        yaxis_title = "probability [%]"
        chart_title = "Cumulative Distribution Function (CDF) of s_bytes_all"
        description = cumulative_function_caption(feature=feature, protocol=protocol, step=step, side=side)
        plot_cumulative_function(series=samples, x_family=x_family, x_feature=x_feature,
                                xaxis_title=xaxis_title,
                                yaxis_title=yaxis_title,
                                chart_title=chart_title, caption=description)
        
        side        = "server-to-client"
        x_family    = "statistics"
        x_feature   = "ts"
        y_family    = "statistics"
        y_feature   = "avg_s_bytes_all"
        xaxis_title = "time [s]"
        yaxis_title = "byte [B]"
        chart_title = "Evolutionary Function of s_bytes_all"
        description = trend_function_caption(feature=feature, protocol=protocol, step=step, side=side)
        plot_trend_function(x_family=x_family, x_feature=x_feature, 
                            y_family=y_family, y_feature=y_feature,
                            xaxis_title=xaxis_title,
                            yaxis_title=yaxis_title,
                            chart_title=chart_title, series=samples, caption=description)
        
    with col2:
        side        = "client-to-server"
        feature     = "idle"
        x_family    = "volumetric"
        x_feature   = "c_bytes_all"
        xaxis_title = "byte [B]"
        yaxis_title = "probability [%]"
        chart_title = "Cumulative Distribution Function (CDF) of c_bytes_all"
        description = cumulative_function_caption(feature=x_feature, protocol=protocol, step=step, side=side)
        plot_cumulative_function(series=samples, x_family=x_family, x_feature=x_feature,
                                xaxis_title=xaxis_title,
                                yaxis_title=yaxis_title,
                                chart_title=chart_title, caption=description)
        
        side        = "client-to-server"
        x_family    = "statistics"
        x_feature   = "ts"
        y_family    = "statistics"
        y_feature   = "avg_c_bytes_all"
        xaxis_title = "time [s]"
        yaxis_title = "byte [B]"
        chart_title = "Evolutionary Function of c_bytes_all"
        description = trend_function_caption(feature=x_feature, protocol=protocol, step=step, side=side)
        plot_trend_function(x_family=x_family, x_feature=x_feature, 
                            y_family=y_family, y_feature=y_feature,
                            xaxis_title=xaxis_title,
                            yaxis_title=yaxis_title,
                            chart_title=chart_title, series=samples, caption=description)
        
    st.caption("#### Groundtruth metrics")
    col1, col2 = st.columns(2)
    with col1:
        side        = "server-to-client"
        x_family    = "volumetric"
        x_feature   = "s_bytes_all"
        y_family    = "groundtruth"
        y_feature   = "avg_video_rate"
        xaxis_title = "bytes [B]"
        yaxis_title = "rate [kbits]"
        chart_title = "Correlation Function s_bytes_all versus avg_video_rate"
        description = scatter_plot_caption(feature_x=x_feature, feature_y=y_feature, protocol=protocol, step=step, side=side)
        plot_scattering_function(x_family=x_family, x_feature=x_feature, 
                                 y_family=y_family, y_feature=y_feature,
                                 xaxis_title=xaxis_title,
                                 yaxis_title=yaxis_title,
                                 chart_title=chart_title, series=samples, caption=description)
    with col2:
        side        = "client-to-server"
        x_family    = "volumetric"
        x_feature   = "c_bytes_all"
        y_family    = "groundtruth"
        y_feature   = "avg_video_rate"
        xaxis_title = "bytes [B]"
        yaxis_title = "rate [kbits]"
        chart_title = "Correlation Function c_bytes_all versus avg_video_rate"
        description = scatter_plot_caption(feature_x=x_feature, feature_y=y_feature, protocol=protocol, step=step, side=side)
        plot_scattering_function(x_family=x_family, x_feature=x_feature, 
                                 y_family=y_family, y_feature=y_feature,
                                 xaxis_title=xaxis_title,
                                 yaxis_title=yaxis_title,
                                 chart_title=chart_title, series=samples, caption=description)
        
    """
    =============================
    =    Processing UDP Layer   =
    =============================
    """

    st.markdown("### UDP")
    protocol = "UDP"
    samples  = load_udp(step=step)
    
    st.caption("#### Temporal metrics")
    col1, col2 = st.columns(2)
    with col1:
        side        = "server-to-client, and viceversa"
        x_family    = "temporal"
        x_feature   = "avg_span"
        xaxis_title = "time [ms]"
        yaxis_title = "probability [%]"
        chart_title = "Cumulative Distribution Function (CDF) of avg_bin_span"
        description = cumulative_function_caption(feature=x_feature, protocol=protocol, step=step, side=side)
        plot_cumulative_function(series=samples, x_family=x_family, x_feature=x_feature,
                                 xaxis_title=xaxis_title,
                                 yaxis_title=yaxis_title,
                                 chart_title=chart_title, caption=description)
        
    with col2:
        side        = "server-to-client, and viceversa"
        x_family    = "temporal"
        x_feature   = "avg_idle"
        xaxis_title = "time [ms]"
        yaxis_title = "probability [%]"
        chart_title = "Cumulative Distribution Function (CDF) of idle"
        description = cumulative_function_caption(feature=x_feature, protocol=protocol, step=step, side=side)
        plot_cumulative_function(series=samples, x_family=x_family, x_feature=x_feature,
                                 xaxis_title=xaxis_title,
                                 yaxis_title=yaxis_title,
                                 chart_title=chart_title, caption=description)

    st.caption("#### Volumetric metrics")
    col1, col2 = st.columns(2)
    with col1:
        side        = "server-to-client"
        feature     = "idle"
        x_family    = "volumetric"
        x_feature   = "s_bytes_all"
        xaxis_title = "byte [B]"
        yaxis_title = "probability [%]"
        chart_title = "Cumulative Distribution Function (CDF) of s_bytes_all"
        description = cumulative_function_caption(feature=feature, protocol=protocol, step=step, side=side)
        plot_cumulative_function(series=samples, x_family=x_family, x_feature=x_feature,
                                xaxis_title=xaxis_title,
                                yaxis_title=yaxis_title,
                                chart_title=chart_title, caption=description)
        
        side        = "server-to-client"
        x_family    = "statistics"
        x_feature   = "ts"
        y_family    = "statistics"
        y_feature   = "avg_s_bytes_all"
        xaxis_title = "time [s]"
        yaxis_title = "byte [B]"
        chart_title = "Evolutionary Function of s_bytes_all"
        description = trend_function_caption(feature=feature, protocol=protocol, step=step, side=side)
        plot_trend_function(x_family=x_family, x_feature=x_feature, 
                            y_family=y_family, y_feature=y_feature,
                            xaxis_title=xaxis_title,
                            yaxis_title=yaxis_title,
                            chart_title=chart_title, series=samples, caption=description)
        
    with col2:
        side        = "client-to-server"
        feature     = "idle"
        x_family    = "volumetric"
        x_feature   = "c_bytes_all"
        xaxis_title = "byte [B]"
        yaxis_title = "probability [%]"
        chart_title = "Cumulative Distribution Function (CDF) of c_bytes_all"
        description = cumulative_function_caption(feature=x_feature, protocol=protocol, step=step, side=side)
        plot_cumulative_function(series=samples, x_family=x_family, x_feature=x_feature,
                                xaxis_title=xaxis_title,
                                yaxis_title=yaxis_title,
                                chart_title=chart_title, caption=description)
        
        side        = "client-to-server"
        x_family    = "statistics"
        x_feature   = "ts"
        y_family    = "statistics"
        y_feature   = "avg_c_bytes_all"
        xaxis_title = "time [s]"
        yaxis_title = "byte [B]"
        chart_title = "Evolutionary Function of c_bytes_all"
        description = trend_function_caption(feature=x_feature, protocol=protocol, step=step, side=side)
        plot_trend_function(x_family=x_family, x_feature=x_feature, 
                            y_family=y_family, y_feature=y_feature,
                            xaxis_title=xaxis_title,
                            yaxis_title=yaxis_title,
                            chart_title=chart_title, series=samples, caption=description)
        
    st.caption("#### Groundtruth metrics")
    col1, col2 = st.columns(2)
    with col1:
        side        = "server-to-client"
        x_family    = "volumetric"
        x_feature   = "s_bytes_all"
        y_family    = "groundtruth"
        y_feature   = "avg_video_rate"
        xaxis_title = "bytes [B]"
        yaxis_title = "rate [kbits]"
        chart_title = "Correlation Function s_bytes_all versus avg_video_rate"
        description = scatter_plot_caption(feature_x=x_feature, feature_y=y_feature, protocol=protocol, step=step, side=side)
        plot_scattering_function(x_family=x_family, x_feature=x_feature, 
                                 y_family=y_family, y_feature=y_feature,
                                 xaxis_title=xaxis_title,
                                 yaxis_title=yaxis_title,
                                 chart_title=chart_title, series=samples, caption=description)
    with col2:
        side        = "client-to-server"
        x_family    = "volumetric"
        x_feature   = "c_bytes_all"
        y_family    = "groundtruth"
        y_feature   = "avg_video_rate"
        xaxis_title = "bytes [B]"
        yaxis_title = "rate [kbits]"
        chart_title = "Correlation Function c_bytes_all versus avg_video_rate"
        description = scatter_plot_caption(feature_x=x_feature, feature_y=y_feature, protocol=protocol, step=step, side=side)
        plot_scattering_function(x_family=x_family, x_feature=x_feature, 
                                 y_family=y_family, y_feature=y_feature,
                                 xaxis_title=xaxis_title,
                                 yaxis_title=yaxis_title,
                                 chart_title=chart_title, series=samples, caption=description)