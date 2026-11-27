#!/usr/bin/env python3
"""Read-only, opt-in checks for editable DXF. Requires ezdxf."""
import argparse
import hashlib
import io
import json
import math
import re
import sys
from pathlib import Path

import ezdxf
from ezdxf.lldxf.tagwriter import TagCollector


def read_dxf(path):
    # Hash the same bytes the parser receives. Never save a drawing.
    data = path.read_bytes()
    if data.startswith(b"AutoCAD Binary DXF"):
        raise ValueError("Only text DXF is supported")
    info = ezdxf.lldxf.validator.dxf_info(io.TextIOWrapper(io.BytesIO(data), encoding="ascii", errors="ignore"))
    encoding = "utf-8" if info.version >= "AC1021" else info.encoding
    doc = ezdxf.read(io.StringIO(data.decode(encoding, errors="surrogateescape"), newline=None))
    return doc, hashlib.sha256(data).hexdigest()


def handle(value):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9A-Fa-f]+", value):
        raise ValueError("Expected a hexadecimal DXF entity handle")
    return value.upper()


def checked_fields(obj, required, optional=()):
    if not isinstance(obj, dict) or not set(required) <= obj.keys() or obj.keys() - set(required) - set(optional):
        raise ValueError(f"Expected fields {required}, optional {optional}")


def finite(value):
    if type(value) not in (float, int) or not math.isfinite(value):
        raise ValueError("Expected a finite number")
    return value


def linear_dimension(entity, tolerance):
    # Angular, ordinate, radial and paper-space dimensions are outside this check.
    if entity.dimtype not in (0, 1):
        raise NotImplementedError("Only rotated and aligned model-space DIMENSION supported")
    measured = finite(entity.get_measurement())
    style = entity.override()
    factor = finite(style.get("dimlfac", 1))
    if factor <= 0 or style.get("dimalt", 0) or style.get("dimlunit", 2) != 2:
        raise NotImplementedError("Only ordinary decimal dimensions without alternate units supported")
    raw = entity.dxf.get("text", "").strip()
    if entity.dxf.get("text", "") == " ":
        return measured, False
    if raw in ("", "<>"):
        # Native measurement placeholder is not a manual value; rendered text
        # and style rounding are intentionally checked in the final PDF, not here.
        return measured, True
    if not re.fullmatch(r"[+-]?(?:[0-9]+(?:[.,][0-9]*)?|[.,][0-9]+)", raw):
        raise NotImplementedError("Unsupported dimension text formatting; inspect the exported sheet")
    shown = finite(float(raw.replace(",", ".")))
    return measured, abs(shown - measured * factor) <= tolerance


def run_rules(doc, contract, findings):
    checked_fields(contract, ("units", "checks"))
    if type(contract["units"]) is not int or contract["units"] <= 0:
        raise ValueError("Specify explicit positive INSUNITS")
    if doc.units != contract["units"]:
        findings.append({"check": "INSUNITS", "status": "failed", "expected": contract["units"], "actual": doc.units})
    rules = contract["checks"]
    if not isinstance(rules, list) or not rules:
        raise ValueError("checks must be a non-empty list")
    model = list(doc.modelspace())
    by_handle = {entity.dxf.handle: entity for entity in model}
    for i, rule in enumerate(rules, 1):
        checked_fields(rule, ("kind", "expected"), ("handle", "type", "layer", "tolerance"))
        kind, expected = rule["kind"], rule["expected"]
        item = {"check": kind, "rule": i, "expected": expected}
        if kind == "count":
            checked_fields(rule, ("kind", "expected", "type", "layer"))
            if not all(isinstance(rule[k], str) and rule[k] for k in ("type", "layer")) or type(expected) is not int or expected < 0:
                raise ValueError("count requires a type, layer and nonnegative integer")
            actual = sum(e.dxftype() == rule["type"].upper() and e.dxf.layer.casefold() == rule["layer"].casefold() for e in model)
            ok = actual == expected
        elif kind in ("length", "dimension", "closed"):
            checked_fields(rule, ("kind", "expected", "handle") + (() if kind == "closed" else ("tolerance",)))
            key = handle(rule["handle"])
            item["handle"] = key
            if kind == "closed":
                if type(expected) is not bool:
                    raise ValueError("closed requires a boolean")
            else:
                finite(expected)
                if finite(rule["tolerance"]) <= 0:
                    raise ValueError("tolerance must be positive")
            entity = by_handle.get(key)
            if entity is None:
                findings.append(dict(item, status="failed", reason="Handle not found in model space"))
                continue
            dtype = entity.dxftype()
            try:
                if kind == "length" and dtype == "LINE":
                    actual = finite((entity.dxf.end - entity.dxf.start).magnitude)
                elif kind == "dimension" and dtype == "DIMENSION":
                    actual, display_ok = linear_dimension(entity, rule["tolerance"])
                    item["manual_text_consistent"] = display_ok
                elif kind == "closed" and dtype in ("LWPOLYLINE", "POLYLINE"):
                    actual = bool(entity.closed if dtype == "LWPOLYLINE" else entity.is_closed)
                else:
                    findings.append(dict(item, status="failed", reason=f"Incompatible entity type: {dtype}"))
                    continue
            except (NotImplementedError, ValueError, TypeError, ezdxf.DXFError) as exc:
                findings.append(dict(item, status="pending", reason=str(exc)))
                continue
            ok = actual == expected if kind == "closed" else abs(actual - expected) <= rule["tolerance"]
            ok = ok and item.get("manual_text_consistent", True)
        else:
            raise ValueError(f"Unsupported check kind: {kind}")
        findings.append(dict(item, status="passed" if ok else "failed", actual=actual))


def snapshot(doc):
    entities = {}
    # Layouts are represented by block records, alongside reusable block definitions.
    for block in doc.blocks:
        for entity in (block.block, *block, block.endblk):
            key = handle(entity.dxf.handle)
            if key in entities:
                raise ValueError("Duplicate DXF handle")
            # export_dxf (used by dxftags) also emits attached ATTRIB/VERTEX data.
            tags = TagCollector.dxftags(entity, dxfversion=doc.dxfversion)
            if not tags or entity.dxftype() == "ACAD_PROXY_ENTITY":
                raise NotImplementedError(f"Uncomparable record {key}: {entity.dxftype()}")
            entities[key] = (block.name, entity.dxftype(), tuple(tags))
    return entities


def run_diff(before, after, policy, findings):
    checked_fields(policy, ("allow",))
    allowed = policy["allow"]
    if not isinstance(allowed, list):
        raise ValueError("allow must be a list")
    permits = set()
    for entry in allowed:
        checked_fields(entry, ("handle", "operation"))
        if entry["operation"] not in ("added", "removed", "modified"):
            raise ValueError("Unknown operation")
        item = (handle(entry["handle"]), entry["operation"])
        if item in permits:
            raise ValueError("Duplicate allowed change")
        permits.add(item)
    old_guid, new_guid = (doc.header.get("$FINGERPRINTGUID", "") for doc in (before, after))
    if (not old_guid or not new_guid or str(old_guid).upper() != str(new_guid).upper()
            or str(old_guid).strip("{}0- ") == "" or before.dxfversion != after.dxfversion):
        findings.append({"check": "lineage", "status": "pending", "reason": "Use same-version saved copies from the same source DXF with a matching nonzero fingerprint"})
        return
    if before.units != after.units:
        findings.append({"check": "INSUNITS", "status": "failed", "expected": before.units, "actual": after.units})
    a, b = snapshot(before), snapshot(after)
    for key in sorted(a.keys() | b.keys(), key=lambda x: int(x, 16)):
        if key in a and key in b and a[key] == b[key]:
            continue
        operation = "added" if key not in a else "removed" if key not in b else "modified"
        container, dtype, _ = b[key] if key in b else a[key]
        findings.append({"check": "scope", "handle": key, "operation": operation, "container": container,
                         "type": dtype, "status": "passed" if (key, operation) in permits else "failed"})
    if not any(item["check"] == "scope" for item in findings):
        findings.append({"check": "scope", "status": "passed", "reason": "No covered entity changes"})


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    audit = sub.add_parser("check")
    audit.add_argument("drawing", type=Path)
    audit.add_argument("--rules", required=True, type=Path)
    diff = sub.add_parser("diff")
    diff.add_argument("before", type=Path)
    diff.add_argument("after", type=Path)
    diff.add_argument("--policy", required=True, type=Path)
    args = parser.parse_args(argv)
    findings, inputs = [], {}
    try:
        if args.mode == "check":
            doc, inputs["drawing_sha256"] = read_dxf(args.drawing)
            rule_bytes = args.rules.read_bytes()
            inputs["rules_sha256"] = hashlib.sha256(rule_bytes).hexdigest()
            run_rules(doc, json.loads(rule_bytes), findings)
        else:
            before, inputs["before_sha256"] = read_dxf(args.before)
            after, inputs["after_sha256"] = read_dxf(args.after)
            policy_bytes = args.policy.read_bytes()
            inputs["policy_sha256"] = hashlib.sha256(policy_bytes).hexdigest()
            run_diff(before, after, json.loads(policy_bytes), findings)
    except (OSError, ValueError, TypeError, AttributeError, KeyError, NotImplementedError, ezdxf.DXFError) as exc:
        findings.append({"check": "input_or_coverage", "status": "pending", "reason": str(exc)})
    statuses = {item["status"] for item in findings}
    status = "failed" if "failed" in statuses else "pending" if "pending" in statuses else "passed"
    print(json.dumps({"schema_version": 1, "mode": args.mode, "status": status,
                      "inputs": inputs, "findings": findings}, ensure_ascii=False, indent=2))
    return {"passed": 0, "failed": 1, "pending": 2}[status]


if __name__ == "__main__":
    sys.exit(main())
