"""Optional bounded Go-syntax parser for Gno source; not a Gno compiler."""
import json
import os
import shutil
import subprocess
from .test_intelligence import recommend
from .coverage_intelligence import summarize

def analyze(source):
    binary = shutil.which(os.environ.get("REALMPROOF_SOURCE_PARSER", "realmproof-source-parser"))
    if not binary:
        return {"status": "unavailable"}
    try:
        data = source.encode("utf-8")
        if len(data) > 1048576:
            return {"status": "limit_exceeded"}
        result = subprocess.run([binary], input=data, capture_output=True, timeout=3, check=True)
        structure = json.loads(result.stdout)
        structure['recommendations'] = recommend(structure)
        structure['coverage'] = summarize(structure)
        return structure
    except (OSError, ValueError, subprocess.SubprocessError):
        return {"status": "unavailable"}
