"""Configuration constants for the framework."""

import os
from os.path import join
from dotenv import load_dotenv

# constants
MQSS_VALID_PROFILING_METRICS = frozenset({
    "mqp_api",
    "quantum_database",
    "quantum_job_runner",
    "isv_job_runner",
    "quantum_daemon_job_runner",
    "generator",
    "scheduler",
    "pass_runner",
    "transpiler",
    "submitter",
    "pass_selection",
    "knitter",
    "job_execution",
})

# environment variables
# TODO: this is a legacy behavior, remove dotenv loading later
dotenv_path = join(os.getcwd(), ".env")
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

MQSS_TOKEN = os.getenv("MQSS_TOKEN", "")
MQSS_PORT = os.getenv("MQSS_PORT", "4000")
MQSS_URL = os.getenv("MQSS_URL", "https://portal.quantum.lrz.de")
MQSS_URL = f"{MQSS_URL}:{MQSS_PORT}"
MQSS_BACKEND = os.getenv("MQSS_BACKEND", "QExa20")
