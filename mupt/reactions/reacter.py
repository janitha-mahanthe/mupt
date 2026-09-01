"""
Engine-agnostic entry point for reaction workflows described by a MuPT reactions config using the REACTER engine.
"""
import yaml
import json
from pathlib import Path
try:
    import AutoREACTER as arx
except ImportError:
    print(
        "[ERROR] Failed to import AutoREACTER.\n"
        "Install it with:\n\n"
        "    python -m pip install AutoREACTER\n"
    )
    raise
    
print("[OK] AutoREACTER imported successfully.")
print(f"[INFO] AutoREACTER version: {arx.__version__}")

def _yaml_to_json(yaml_input: dict | str | Path) -> str:
    """Convert a YAML input (dict or file path) to a JSON string."""

    if isinstance(yaml_input, dict):
        data = yaml_input
    elif isinstance(yaml_input, (str, Path)):
        with open(yaml_input, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    else:
        raise TypeError(
            f'Expected a dict or path, got {type(yaml_input).__name__}.'
        )

    if not isinstance(data, dict):
        raise ValueError(
            'YAML input must contain a mapping at the top level.'
        )

    try:
        return json.dumps(data)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f'YAML contains values that cannot be represented as JSON: {exc}'
        ) from exc

def _system_parameters_2_systems(input_data: dict) -> dict:
    """
    MuPT will read the system as system parameters while AutoREACTER expects them as systems.
    This function transforms the input dictionary from the MuPT format to the AutoREACTER format.
    """
    if "system_parameters" not in input_data:
        raise ValueError("Missing 'system_parameters' key in input data.")

    systems = input_data.pop("system_parameters")
    input_data["systems"] = systems
    return input_data

def _call_warning(type: str) -> None:
    """Print a warning message indicating that the REACTER workflow is being called."""
    print(f"""
    [WARNING] In this input, there is a section '{type}' which will not be required for 
    the AutoREACTER workflow.
    """)

def arx_phaser(yaml_input: dict | str | Path) -> str:
    """Convert a YAML input to JSON and return it as a string for REACTER.

    This function takes a YAML input (either a dictionary or a file path),
    converts it to a JSON string, and then runs the REACTER workflow using
    the AutoREACTER engine.

    Args:
        yaml_input (dict or str or Path): The YAML input to be converted and processed.

    Returns:
        str: The JSON string representation of the input.
    """
    json_input = _yaml_to_json(yaml_input)
    json_input = _system_parameters_2_systems(json.loads(json_input))
    if 'reactions' in yaml_input if isinstance(yaml_input, dict) else False:
        _call_warning("reactions")
    
    if json_input.get("reaction_engine", {}).get("inputs", None) is not None:
        _call_warning("reaction_engine inputs")
    arx.run(json_input)
    arx.select_reactions()
    arx.select_non_reactants()
    arx.prepare_reactions()
    arx.process()
    return json_input
    