"""命令行参数解析。"""

import argparse


def parse_args():
    parser = argparse.ArgumentParser(description="Llama Server Launcher")
    parser.add_argument("--no-mmap", action="store_true", help="Disable memory mapping")
    parser.add_argument(
        "--flash-attention",
        choices=["auto", "on", "off"],
        default=None,
        help="Flash attention mode",
    )
    parser.add_argument("-m", "--model", help="Model file path")
    parser.add_argument("--host", default="0.0.0.0", help="Server host")
    parser.add_argument("--port", type=int, default=8080, help="Server port")
    parser.add_argument("-c", "--ctx-size", type=int, help="Context size")
    parser.add_argument("-n", "--n-predict", type=int, help="Max tokens to predict")
    parser.add_argument("-ngl", "--n-gpu-layers", type=int, help="GPU layers")
    parser.add_argument("-t", "--threads", type=int, help="Number of threads")
    parser.add_argument(
        "--threads-batch", type=int, help="Number of threads for batch processing"
    )
    parser.add_argument("-b", "--batch-size", type=int, help="Batch size")
    parser.add_argument("--ubatch-size", type=int, help="Physical batch size")
    parser.add_argument("--temp", type=float, help="Temperature")

    parser.add_argument("--server", help="llama-server executable path")
    parser.add_argument("--mmproj", help="Vision projector file")
    parser.add_argument("--timeout", type=int, help="Timeout in seconds")
    parser.add_argument("--sleep-idle-seconds", type=int, help="Sleep idle seconds")
    parser.add_argument("--tools", help="Enable built-in tools for AI agents (e.g. 'all' or 'read_file,grep_search')")
    parser.add_argument(
        "--chat-template-kwargs",
        help="Chat template kwargs JSON",
    )
    return parser.parse_args()
