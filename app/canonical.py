import hashlib
import json
from datetime import datetime, timezone

from .clock import stamp
from .config import RULE_VERSION, ZONE


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def manifest(sources, elapsed_ms):
    inputs = {name: {'bytes': len(raw), 'sha256': digest(raw)} for name, raw in sources.items()}
    identity = {'inputs': inputs, 'rule_version': RULE_VERSION}
    return dict(identity, id=digest(canonical(identity).encode()), timezone=ZONE,
                created=stamp(datetime.now(timezone.utc)), elapsed_ms=elapsed_ms)
