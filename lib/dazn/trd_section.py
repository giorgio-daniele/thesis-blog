# import os
# import pandas
# import numpy
# import streamlit
# import concurrent.futures

# from lib.generic import TESTBED_RATES
# from lib.generic import LIMIT
# from lib.generic import Protocol
# from lib.generic import __plot_scatter
# from lib.generic import __plot_trend
# from lib.generic import __cumulative_function
# from lib.generic import __signal_to_noise


import os
import pandas
import streamlit


from lib.generic import LOG_BOT_COMPLETE
from lib.generic import LOG_HAR_COMPLETE
from lib.generic import LOG_TCP_COMPLETE
from lib.generic import LOG_UDP_COMPLETE
from lib.generic import LOG_TCP_PERIODIC
from lib.generic import LOG_UDP_PERIODIC

from lib.generic import plot_trend
from lib.generic import plot_scatter
from lib.generic import cumulative_function

from lib.generic import LIMIT
from lib.generic import Protocol
from lib.generic import TESTBED_RATES


SERVER = "dazn"

@streamlit.cache_data(show_spinner=True, ttl=10_000)
def load_tcp(step: str):
    samples = {}

    for rate in TESTBED_RATES:
        dir = os.path.join(SERVER, rate, "samples", "tcp", str(step))
        
        # print("*********************")
        # print("*********************")
        # print(dir)

        # Generate a unique frame with all measurements
        # for a specific rate
        frame = pandas.concat(
            [pandas.read_csv(os.path.join(dir, file), sep=" ") 
                for file in os.listdir(dir)][:20], ignore_index=True)

        # Convert millis timestamps to seconds
        frame["ts"] = frame["ts"] / 1000
        frame["te"] = frame["te"] / 1000  

        # Define statistics to be computed at each interval [ts; te]. 
        # Some of these metrics are already in form of mean, so they 
        # will be further average
        stats = {
            "agg_avg_video_rate":    ("avg_video_rate", lambda x: x[x != 0].mean()),
            "agg_avg_c_bytes_all":   ("c_bytes_all",  "mean"),
            "agg_avg_s_ack_cnt":     ("s_ack_cnt",    "mean"),
            "agg_avg_c_ack_cnt":     ("c_ack_cnt",    "mean"),
            "agg_avg_s_ack_cnt_p":     ("s_ack_cnt_p",    "mean"),
            "agg_avg_c_ack_cnt_p":     ("c_ack_cnt_p",    "mean"),
            "agg_avg_s_bytes_all":   ("s_bytes_all",  "mean"),
            "agg_avg_avg_span":      ("avg_span", "mean"),
            "agg_avg_max_span":      ("max_span", "mean"),
            "agg_avg_min_span":      ("min_span", "mean"),
            "agg_avg_std_span":      ("std_span", "mean"),
            "agg_avg_idle":          ("idle", "mean")
        }

        # Group rows at each rate by using the time period
        data = frame.groupby(["ts", "te"], as_index=False).agg(**stats)

        # Convert timestamps to datetime
        data["xs"] = pandas.to_datetime(data["ts"], origin="unix", unit='s')
        data["xe"] = pandas.to_datetime(data["te"], origin="unix", unit='s')

        samples[rate] = data

    return samples

@streamlit.cache_data(show_spinner=True, ttl=10_000)
def load_udp(step: str):
    samples = {}

    for rate in TESTBED_RATES:
        dir = os.path.join(SERVER, rate, "samples", "udp", str(step))
        
        #print("*********************")
        #print(f"Processing rate: {rate}")
        #print(f"Directory: {dir}")
        
        # Check if directory exists
        if not os.path.exists(dir):
            print(f"Directory does not exist: {dir}")
            continue
        
        files = os.listdir(dir)
        #print(f"Files in directory ({len(files)}): {files}")

        # Generate a unique frame with all measurements
        # for a specific rate
        frame = pandas.concat(
            [pandas.read_csv(os.path.join(dir, file), sep=" ") 
                for file in files][:20], ignore_index=True)
        #print("Dataframe shape after concatenation:", frame.shape)

        # Convert millis timestamps to seconds
        frame["ts"] = frame["ts"] / 1000
        frame["te"] = frame["te"] / 1000
        #print("Timestamps converted to seconds.")

        # Define statistics to be computed at each interval [ts; te]. 
        # Some of these metrics are already in form of mean, so they 
        # will be further average
        stats = {
            "agg_avg_video_rate":    ("avg_video_rate", lambda x: x[x != 0].mean()),
            "agg_avg_c_bytes_all":   ("c_bytes_all",    "mean"),
            "agg_avg_s_bytes_all":   ("s_bytes_all",    "mean"),
            "agg_avg_avg_span":      ("avg_span",       "mean"),
            "agg_avg_max_span":      ("max_span",       "mean"),
            "agg_avg_min_span":      ("min_span",       "mean"),
            "agg_avg_std_span":      ("std_span",       "mean"),
            "agg_avg_idle":          ("idle",           "mean")
        }

        # Group rows at each rate by using the time period
        data = frame.groupby(["ts", "te"], as_index=False).agg(**stats)
        #print("Grouped data shape:", data.shape)

        # Convert timestamps to datetime
        data["xs"] = pandas.to_datetime(data["ts"], origin="unix", unit='s')
        data["xe"] = pandas.to_datetime(data["te"], origin="unix", unit='s')
        #print("Timestamps converted to datetime.")

        samples[rate] = data

    return samples




def plot_protocol(media: pandas.DataFrame, proto: Protocol, step: float):

    """
    =============================
    =     Volumetric stats      =
    =============================
    """

    streamlit.caption("#### Volumetric measures")
    server, client = streamlit.columns(2)

    with server:
        x = "xs"
        y = "agg_avg_s_bytes_all"
        xtitle = "time [mm:ss]"
        ytitle = "bytes [B]"
        ctitle = f"Average bytes from server each {step / 1000} seconds"
        plot_trend(x=x, y=y, xtitle=xtitle, ytitle=ytitle, ctitle=ctitle, media=media, noise=None)
        
        if proto == Protocol.TCP:
            x = "xs"
            y = "agg_avg_s_ack_cnt"
            xtitle = "time [mm:ss]"
            ytitle = "packets [#]"
            ctitle = f"Average piggybacking ACKs packets from server each {step / 1000} seconds"
            plot_trend(x=x, y=y, xtitle=xtitle, ytitle=ytitle, ctitle=ctitle, media=media, noise=None)
            
            x = "xs"
            y = "agg_avg_s_ack_cnt_p"
            xtitle = "time [mm:ss]"
            ytitle = "packets [#]"
            ctitle = f"Average pure ACKs packets from server each {step / 1000} seconds"
            plot_trend(x=x, y=y, xtitle=xtitle, ytitle=ytitle, ctitle=ctitle, media=media, noise=None)

    with client:
        x = "xs"
        y = "agg_avg_c_bytes_all"
        xtitle = "time [mm:ss]"
        ytitle = "bytes [B]"
        ctitle = f"Average bytes from client each {step / 1000} seconds"
        plot_trend(x=x, y=y, xtitle=xtitle, ytitle=ytitle, ctitle=ctitle, media=media, noise=None)
        
        if proto == Protocol.TCP:
            x = "xs"
            y = "agg_avg_c_ack_cnt"
            xtitle = "time [mm:ss]"
            ytitle = "packets [#]"
            ctitle = f"Average piggybacking ACKs packets from client each {step / 1000} seconds"
            plot_trend(x=x, y=y, xtitle=xtitle, ytitle=ytitle, ctitle=ctitle, media=media, noise=None)
            

            x = "xs"
            y = "agg_avg_c_ack_cnt_p"
            xtitle = "time [mm:ss]"
            ytitle = "packets [#]"
            ctitle = f"Average pure ACKs packets from client each {step / 1000} seconds"
            plot_trend(x=x, y=y, xtitle=xtitle, ytitle=ytitle, ctitle=ctitle, media=media, noise=None)


    """
    =============================
    =      Temporal stats       =
    =============================
    """
    streamlit.caption("#### Temporal measures")
    col1, col2, col3, col4 = streamlit.columns(4)

    with col1:
        x = "agg_avg_avg_span"
        xtitle = "time [ms]"
        ytitle = "probability [%]"
        ctitle = f"CDF of average bin span"
        cumulative_function(x=x, xtitle=xtitle, ytitle=ytitle, ctitle=ctitle, media=media, noise=None)
        
    with col2:
        x = "agg_avg_max_span"
        xtitle = "time [ms]"
        ytitle = "probability [%]"
        ctitle = f"CDF of average max bin span each {step / 1000} seconds"
        cumulative_function(x=x, xtitle=xtitle, ytitle=ytitle, ctitle=ctitle, media=media, noise=None)
        
    with col3:
        x = "agg_avg_min_span"
        xtitle = "time [ms]"
        ytitle = "probability [%]"
        ctitle = f"CDF of average min bin span each {step / 1000} seconds"
        cumulative_function(x=x, xtitle=xtitle, ytitle=ytitle, ctitle=ctitle, media=media, noise=None)

    with col4:
        x = "agg_avg_idle"
        xtitle = "time [ms]"
        ytitle = "probability [%]"
        ctitle = f"CDF of average idle time each {step / 1000} seconds"
        cumulative_function(x=x, xtitle=xtitle, ytitle=ytitle, ctitle=ctitle, media=media, noise=None)


    """
    =============================
    =        Ground Truth       =
    =============================
    """
    streamlit.caption("#### Statistics measures")
    col1, col2 = streamlit.columns(2)

    with col1:
        x = "agg_avg_s_bytes_all"
        y = "agg_avg_video_rate"
        xtitle = "bytes [B]"
        ytitle = "rate [kbits]"
        ctitle = f"Relationship among server bytes and average video rate at {step / 1000} seconds"
        plot_scatter(x=x, y=y, xtitle=xtitle, ytitle=ytitle, ctitle=ctitle, media=media, noise=None)

    with col2:
        x = "agg_avg_avg_span"
        y = "agg_avg_video_rate"
        xtitle = "time [ms]"
        ytitle = "rate [kbits]"
        ctitle = f"Relationship among average bin span and average video rate at {step / 1000} seconds"
        plot_scatter(x=x, y=y, xtitle=xtitle, ytitle=ytitle, ctitle=ctitle, media=media, noise=None)



#############################
#           MAIN            #
#############################

def main():
    streamlit.html(os.path.join("www", SERVER, "__trd_section", "0.html"))

    # Let the user choose the step to be used
    step = streamlit.select_slider("Select step value", 
                                   options=[i * 1000 for i in range(1, 11)], value=2000, 
                                                format_func=lambda x: f"{x / 1000} seconds")

    """
    =============================
    =    Processing TCP Layer   =
    =============================
    """

    streamlit.markdown("### TCP")
    samples = load_tcp(step=step)
    plot_protocol(media=samples, proto=Protocol.TCP, step=step)


    """
    =============================
    =    Processing UDP Layer   =
    =============================
    """
    streamlit.markdown("### UDP")
    samples = load_udp(step=step)
    plot_protocol(media=samples, proto=Protocol.UDP, step=step)



# ##########################################################################
# ##########################################################################
# #                                                                        #
# #                               MAIN                                     #
# #                                                                        #
# ##########################################################################
# ##########################################################################

# def __main():

#     steps = [i * 1000 for i in range(1, 11)]

#     # Create a slider with specific values
#     step = streamlit.select_slider("Select step value", options=steps, value=2000, format_func=lambda x: f"{x}")

#     tcp_media_samples = load_samples(step=str(step), mode="media", protocol=Protocol.TCP)

#     # Load and plot samples for TCP protocol
#     plot_protocol(protocol=Protocol.TCP, media_samples=tcp_media_samples, noise_samples=None)

#     streamlit.caption("---")

#     # Load and plot samples for UDP protocol
#     udp_media_samples = load_samples(step=str(step), mode="media", protocol=Protocol.UDP)

#     plot_protocol(protocol=Protocol.UDP, media_samples=udp_media_samples, noise_samples=None)
