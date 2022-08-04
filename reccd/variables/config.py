# -*- coding: utf-8 -*-

ENVIRONMENT_PREFIX = "RECCD_"
ENVIRONMENT_SUFFIX = ""

ENVIRONMENT_FILE_PREFIX = "RECCD_"
ENVIRONMENT_FILE_SUFFIX = "_FILE"

CFG_ENCODING = "utf-8"
CFG_SECTION = "reccd"

SKIP_MODULE = "-"

SERVICER_PROG = "reccd"
SERVICER_DESCRIPTION = "Daemon helper for the ANSWER"
SERVICER_EPILOG = f"""
Use '{SKIP_MODULE}' to skip module names in command line arguments.
"""
