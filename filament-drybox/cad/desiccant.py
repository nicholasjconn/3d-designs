"""Export the two matching desiccant parts and the optional refill funnel."""
import argparse
from pathlib import Path

import cadquery as cq

import desiccant_box
import desiccant_cap
import desiccant_funnel
from direct_interfaces import one


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    for name, module in (
        ("desiccant-box", desiccant_box),
        ("desiccant-cap", desiccant_cap),
        ("desiccant-funnel", desiccant_funnel),
    ):
        part = one(module.build(), name)
        cq.exporters.export(part, str(args.output / f"{name}.step"))


if __name__ == "__main__":
    main()
