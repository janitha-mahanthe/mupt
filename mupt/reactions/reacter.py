"""
Engine-agnostic entry point for reaction workflows described by a MuPT
reactions config using the REACTER engine.
"""

import json
import tempfile
from pathlib import Path

import yaml

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
        with open(yaml_input, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

    else:
        raise TypeError(
            f"Expected a dict or path, got {type(yaml_input).__name__}."
        )

    if not isinstance(data, dict):
        raise ValueError(
            "YAML input must contain a mapping at the top level."
        )

    try:
        return json.dumps(data)

    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"YAML contains values that cannot be represented as JSON: {exc}"
        ) from exc


def _dirname_2_simulation_name(input_data: dict) -> dict:
    """
    MuPT uses 'dirname' while AutoREACTER expects 'simulation_name'.
    """

    if "simulation_name" not in input_data:
        if "dirname" not in input_data:
            raise ValueError(
                "Missing 'dirname' key required to create 'simulation_name'."
            )

        input_data["simulation_name"] = input_data.pop("dirname")

    return input_data


def _system_parameters_2_simulations(input_data: dict) -> dict:
    """
    MuPT uses 'system_parameters' while AutoREACTER expects 'simulations'.
    """

    if "simulations" not in input_data:
        if "system_parameters" not in input_data:
            raise ValueError(
                "Missing 'system_parameters' key in input data."
            )

        input_data["simulations"] = input_data.pop("system_parameters")

    return input_data


def _call_warning(section: str) -> None:
    """Print a warning for MuPT sections not required by AutoREACTER."""

    print(
        f"""
    [WARNING] In this input, there is a section '{section}' which will not be required for
    the AutoREACTER workflow.
    """
    )


def _temp_file_gen(inputs: dict | str | Path) -> None:
    """
    Write the converted MuPT input to a temporary JSON file
    and initialize AutoREACTER with it.
    """

    if not isinstance(inputs, dict):
        with open(inputs, "r", encoding="utf-8") as f:
            inputs = yaml.safe_load(f)

    if not isinstance(inputs, dict):
        raise ValueError(
            "AutoREACTER input must contain a mapping at the top level."
        )

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".json",
        delete=False,
        encoding="utf-8",
    ) as f:
        json.dump(inputs, f, indent=4)
        json_path = Path(f.name)

    try:
        arx.run(json_path)

    finally:
        json_path.unlink(missing_ok=True)


def arx_phaser(yaml_input: dict | str | Path) -> dict:
    """
    Convert a MuPT YAML input to the format expected by AutoREACTER
    and run the REACTER workflow.

    Parameters
    ----------
    yaml_input : dict or str or Path
        MuPT reaction configuration as a dictionary or YAML file path.

    Returns
    -------
    dict
        The converted AutoREACTER-compatible input dictionary.
    """

    json_input = _yaml_to_json(yaml_input)
    json_input = json.loads(json_input)

    # Convert MuPT schema to AutoREACTER schema.
    json_input = _dirname_2_simulation_name(json_input)
    json_input = _system_parameters_2_simulations(json_input)

    # Warn about MuPT-specific sections not required by AutoREACTER.
    if "reactions" in json_input:
        _call_warning("reactions")

    if json_input.get("reaction_engine", {}).get("inputs") is not None:
        _call_warning("reaction_engine inputs")

    # Create the temporary JSON input and initialize AutoREACTER.
    _temp_file_gen(json_input)

    # Run the AutoREACTER workflow.
    arx.select_reactions()
    arx.select_non_reactants()
    arx.prepare_reactions()
    arx.process()

    return json_input

