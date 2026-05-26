"""Unit tests for the Pydantic configuration schema."""

from pathlib import Path

import pytest

from quantipy_polarity.config import (
    Config,
    InputMasks,
    InputND2,
    InputTIF,
)


def _minimal_masks_dict() -> dict:
    return {
        "input": {
            "mode": "masks",
            "path": "./raw",
            "masks_dir": "./masks",
            "pixel_size_um": 0.65,
        }
    }


def _minimal_nd2_dict() -> dict:
    return {
        "input": {
            "mode": "nd2",
            "path": "./raw",
            "channel_membrane": 1,
            "channel_segmentation": 1,
            "pixel_size_um": 0.65,
        }
    }


def test_masks_minimal_config_parses() -> None:
    cfg = Config.model_validate(_minimal_masks_dict())
    assert isinstance(cfg.input, InputMasks)
    assert cfg.input.mode == "masks"
    assert cfg.input.pixel_size_um == 0.65
    assert cfg.project.name == "my_experiment"  # default


def test_nd2_minimal_config_parses() -> None:
    cfg = Config.model_validate(_minimal_nd2_dict())
    assert isinstance(cfg.input, InputND2)
    assert cfg.input.z_policy == "mip"  # default


def test_tif_mode_parses() -> None:
    data = {
        "input": {
            "mode": "tif",
            "path": "./tifs",
            "channel_membrane": 0,
            "channel_segmentation": 0,
            "pixel_size_um": 0.5,
        }
    }
    cfg = Config.model_validate(data)
    assert isinstance(cfg.input, InputTIF)


def test_substack_requires_range() -> None:
    data = _minimal_nd2_dict()
    data["input"]["z_policy"] = "substack"
    with pytest.raises(ValueError, match="substack_range required"):
        Config.model_validate(data)


def test_substack_range_must_be_ordered() -> None:
    data = _minimal_nd2_dict()
    data["input"]["z_policy"] = "substack"
    data["input"]["substack_range"] = [10, 3]
    with pytest.raises(ValueError, match="must be <"):
        Config.model_validate(data)


def test_negative_channel_rejected() -> None:
    data = _minimal_nd2_dict()
    data["input"]["channel_membrane"] = -1
    with pytest.raises(ValueError):
        Config.model_validate(data)


def test_pixel_size_must_be_positive() -> None:
    data = _minimal_masks_dict()
    data["input"]["pixel_size_um"] = 0.0
    with pytest.raises(ValueError):
        Config.model_validate(data)


def test_round_trip_yaml(tmp_path: Path) -> None:
    cfg = Config.model_validate(_minimal_masks_dict())
    yaml_path = tmp_path / "c.yaml"
    cfg.to_yaml(yaml_path)
    loaded = Config.from_yaml(yaml_path)
    assert loaded.input.mode == "masks"
    assert loaded.input.pixel_size_um == 0.65


def test_unknown_mode_rejected() -> None:
    data = {"input": {"mode": "xyz", "path": "./raw", "pixel_size_um": 0.5}}
    with pytest.raises(ValueError):
        Config.model_validate(data)
