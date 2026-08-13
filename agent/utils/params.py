import json
from typing import Any

from .logger import logger


def parse_params(raw: str | None, *required_keys: str) -> dict[str, Any]:
    """
    Parse custom_action_param / custom_recognition_param JSON string.

    Args:
        raw: Raw JSON string, may be None or empty.
        required_keys: Keys that must be present in the parsed object.

    Returns:
        Parsed dict (empty dict when raw is None or empty).

    Raises:
        ValueError: Invalid JSON, non-object type, or missing required keys.
    """
    if not raw:
        if required_keys:
            raise ValueError(f"missing required params: {list(required_keys)}")
        return {}
    try:
        params = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"invalid JSON params: {e}") from e
    if not isinstance(params, dict):
        raise ValueError(f"params must be an object, got: {type(params).__name__}")
    if required_keys:
        missing = [k for k in required_keys if k not in params]
        if missing:
            raise ValueError(f"missing required params: {missing}")
    return params


def coerce_like(value: Any, default: Any, key: str) -> Any:
    """
    Coerce a JSON-deserialized value into the shape of *default* for param overriding.

    - default is tuple/list: accept list/tuple, length must match (e.g. ROI must be 4 elements),
      elements must be numbers, return the same type as default.
    - default is bool: only accept bool (note: bool is int subclass, checked first).
    - default is int/float: accept numbers and convert to the matching type.
    - default is str: only accept str.
    - other types: require exact type match.

    Raises:
        ValueError: Shape or type mismatch.
    """
    if isinstance(default, (tuple, list)):
        if not isinstance(value, (list, tuple)):
            raise ValueError(f"{key} should be a list, got {type(value).__name__}")
        if len(value) != len(default):
            raise ValueError(f"{key} should have length {len(default)}, got {len(value)}")
        if not all(isinstance(v, (int, float)) for v in value):
            raise ValueError(f"{key} elements must be numbers")
        return type(default)(value)
    if isinstance(default, bool):
        if not isinstance(value, bool):
            raise ValueError(f"{key} should be a bool, got {type(value).__name__}")
        return value
    if isinstance(default, int):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{key} should be a number, got {type(value).__name__}")
        return int(value)
    if isinstance(default, float):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{key} should be a number, got {type(value).__name__}")
        return float(value)
    if isinstance(default, str):
        if not isinstance(value, str):
            raise ValueError(f"{key} should be a string, got {type(value).__name__}")
        return value
    if type(value) is not type(default):
        raise ValueError(f"{key} should be {type(default).__name__}, got {type(value).__name__}")
    return value


class ParamOverrideMixin:
    """
    Mixin that overrides instance attributes from custom_recognition_param.

    Lowercase keys from the JSON param dict are overlaid onto instance attributes
    (shadowing the same-named uppercase class constants), providing a layered
    approach: pipeline JSON for overrides, Python class constants as defaults.

    - JSON key convention = class constant name in lowercase (e.g. sat_min -> SAT_MIN).
    - Only constants listed in OVERRIDABLE may be overridden; unknown keys are
      logged as warnings and ignored.
    - Values are coerced via coerce_like into the shape of the default; invalid
      values fall back to the default with an error log.
    - Existing instance overrides are cleared at each entry to avoid cross-node
      interference.
    - Thread safety: MaaFramework calls recognition callbacks serially per Tasker.
    """

    OVERRIDABLE: frozenset[str] = frozenset()

    def apply_param_overrides(self, params: dict[str, Any]) -> None:
        for const in self.OVERRIDABLE:
            self.__dict__.pop(const, None)
        for key, value in params.items():
            if key == "query":
                continue
            const = key.upper()
            if const not in self.OVERRIDABLE:
                logger.warning(f"[{type(self).__name__}] unknown param {key}, ignored")
                continue
            try:
                setattr(self, const, coerce_like(value, getattr(type(self), const), key))
            except ValueError as e:
                logger.error(f"[{type(self).__name__}] parameter {key} is invalid ({e}), falling back to default")
