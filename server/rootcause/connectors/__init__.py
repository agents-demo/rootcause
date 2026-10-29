"""Factory data connectors.

Pilots deal with messy site integration, so every connector exposes the same tiny surface:
``test()``, ``read()`` and a provenance record. Hardware libraries are optional; when they are
missing the connector runs in *simulated* mode and says so instead of pretending to be live.
"""

from __future__ import annotations

import csv
import socket
import statistics
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass
class ConnectorStatus:
    id: str
    reachable: bool
    mode: str
    detail: str
    samples: int = 0
    checked_at: str = field(default_factory=lambda: datetime.now(UTC).replace(microsecond=0).isoformat())

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "reachable": self.reachable,
            "mode": self.mode,
            "detail": self.detail,
            "samples": self.samples,
            "checked_at": self.checked_at,
        }


class Connector:
    id = "base"
    protocol = "generic"
    required_extra = ""

    def __init__(self, endpoint: str = "", *, simulate: bool = True) -> None:
        self.endpoint = endpoint
        self.simulate = simulate

    def test(self) -> ConnectorStatus:
        if self.simulate:
            return ConnectorStatus(self.id, True, "simulated", f"Simulated endpoint {self.endpoint or 'local'}")
        try:
            host, _, port = (self.endpoint or "").replace("opc.tcp://", "").partition(":")
            with socket.create_connection((host or "127.0.0.1", int(port or 0)), timeout=2):
                return ConnectorStatus(self.id, True, "live", f"TCP reachable: {self.endpoint}")
        except Exception as exc:
            return ConnectorStatus(self.id, False, "error", f"{type(exc).__name__}: {exc}")


class OpcUaConnector(Connector):
    id = "opcua"
    protocol = "OPC-UA"
    required_extra = "asyncua"

    def read(self, tags: Iterable[str] = ()) -> dict[str, Any]:
        tags = list(tags) or ["temperature", "pressure", "cycle_time"]
        if self.simulate:
            return {"mode": "simulated", "tags": {t: round(100 + (i + 1) * 7.3, 2) for i, t in enumerate(tags)}}
        try:
            from asyncua.sync import Client  # type: ignore

            with Client(self.endpoint) as client:
                values = {}
                for tag in tags:
                    node = client.get_node(tag)
                    values[tag] = node.read_value()
                return {"mode": "live", "tags": values}
        except Exception as exc:
            return {"mode": "error", "error": str(exc), "tags": {}}


class ModbusConnector(Connector):
    id = "modbus"
    protocol = "Modbus"
    required_extra = "pymodbus"

    def __init__(self, endpoint: str = "", *, unit: int = 1, simulate: bool = True) -> None:
        super().__init__(endpoint, simulate=simulate)
        self.unit = unit

    def read(self, registers: Iterable[int] = ()) -> dict[str, Any]:
        regs = list(registers) or list(range(0, 10))
        if self.simulate:
            return {"mode": "simulated", "registers": {r: round(500 + r * 13.7, 2) for r in regs}}
        try:
            from pymodbus.client import ModbusTcpClient  # type: ignore

            host, _, port = self.endpoint.partition(":")
            client = ModbusTcpClient(host, port=int(port or 502))
            client.connect()
            rr = client.read_holding_registers(regs[0], count=len(regs), slave=self.unit)
            client.close()
            return {"mode": "live", "registers": dict(zip(regs, rr.registers, strict=False))}
        except Exception as exc:
            return {"mode": "error", "error": str(exc), "registers": {}}


class CameraConnector(Connector):
    id = "camera"
    protocol = "TCP/IP"
    required_extra = ""

    def latest_frame(self) -> dict[str, Any]:
        """Return metadata for the most recent frame. Frames themselves stay on site."""
        if self.simulate:
            return {
                "mode": "simulated",
                "width": 2448,
                "height": 2048,
                "format": "jpeg",
                "note": "Frame metadata only; image bytes never leave the factory network.",
            }
        try:
            host, _, port = self.endpoint.partition(":")
            with socket.create_connection((host, int(port or 9000)), timeout=2) as sock:
                sock.sendall(b"TRIGGER\n")
                head = sock.recv(64)
                return {"mode": "live", "header": head.hex(), "note": "Camera acknowledged trigger."}
        except Exception as exc:
            return {"mode": "error", "error": str(exc)}


class HttpCameraConnector(Connector):
    """Generic HTTP snapshot pull for cameras that expose a JPEG endpoint."""

    id = "camera-http"
    protocol = "HTTP snapshot"

    def snapshot(self, out_path: str | Path) -> dict[str, Any]:
        if self.simulate:
            return {"mode": "simulated", "note": "Set simulate=False and a real snapshot URL."}
        try:
            import urllib.request

            with urllib.request.urlopen(self.endpoint, timeout=5) as response:
                data = response.read()
            if not data:
                raise ValueError("empty snapshot")
            target = Path(out_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            return {"mode": "live", "bytes": len(data), "path": str(target), "content_type": response.headers.get("Content-Type", "")}
        except Exception as exc:
            return {"mode": "error", "error": str(exc)}


def read_csv_records(path: str | Path) -> list[dict[str, str]]:
    p = Path(path)
    if not p.exists():
        return []
    with p.open(newline="", encoding="utf-8-sig") as fh:
        return [{k.strip(): (v or "").strip() for k, v in row.items()} for row in csv.DictReader(fh)]


class CsvConnector(Connector):
    """Import MES batches, quality history or supplier certificates from a drop folder."""

    id = "csv"
    protocol = "CSV import"

    def __init__(self, path: str | Path = "", *, kind: str = "generic", simulate: bool = True) -> None:
        super().__init__(str(path), simulate=simulate)
        self.path = Path(path) if path else None
        self.kind = kind

    def records(self) -> list[dict[str, Any]]:
        if not self.path:
            return []
        return read_csv_records(self.path)


class RestConnector(Connector):
    id = "rest"
    protocol = "REST/GraphQL"

    def read(self, path: str = "/health") -> dict[str, Any]:
        if self.simulate:
            return {"mode": "simulated", "status": "ok", "path": path}
        try:
            import urllib.request

            with urllib.request.urlopen(self.endpoint.rstrip("/") + path, timeout=4) as resp:
                return {"mode": "live", "status": resp.status, "body": resp.read(2048).decode("utf-8", "replace")}
        except Exception as exc:
            return {"mode": "error", "error": str(exc)}


class SapQmConnector(RestConnector):
    id = "sap-qm"
    protocol = "SAP QM"

    def read(self, path: str = "/QM/InspectionLot") -> dict[str, Any]:
        return super().read(path)


class SapPmConnector(RestConnector):
    id = "sap-pm"
    protocol = "SAP PM"

    def read(self, path: str = "/PM/WorkOrder") -> dict[str, Any]:
        return super().read(path)


class FactoryTalkConnector(OpcUaConnector):
    id = "factorytalk"
    protocol = "FactoryTalk"


class S7Connector(Connector):
    id = "s7"
    protocol = "Siemens S7"
    required_extra = "python-snap7"

    def read(self) -> dict[str, Any]:
        if self.simulate:
            return {"mode": "simulated", "db": {"DB1.DBW0": 231, "DB1.DBW2": 1120}}
        try:
            import snap7  # type: ignore

            host, _, _ = self.endpoint.partition(":")
            client = snap7.client.Client()
            client.connect(host, 0, 1)
            data = client.db_read(1, 0, 4)
            client.disconnect()
            return {"mode": "live", "db": {"DB1.DBB0": list(data)}}
        except Exception as exc:
            return {"mode": "error", "error": str(exc)}


class CmmsConnector(RestConnector):
    id = "cmms"
    protocol = "REST"


def normalise_frame(
    raw: dict[str, float],
    mapping: dict[str, str] | None = None,
    *,
    units: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Rename tags, coerce numbers, drop impossible values and record QC counters."""
    mapping = mapping or {}
    units = units or {}
    clean: dict[str, float] = {}
    dropped: list[str] = []
    for tag, value in raw.items():
        name = mapping.get(tag, tag)
        try:
            f = float(value)
        except (TypeError, ValueError):
            dropped.append(tag)
            continue
        if f != f or abs(f) > 1e9:  # NaN or absurd
            dropped.append(tag)
            continue
        clean[name] = round(f, 4)
    return {
        "values": clean,
        "units": {k: units.get(k, "") for k in clean},
        "dropped": dropped,
        "quality": "good" if not dropped else "partial",
    }


def clean_series(values: Iterable[float], *, max_sigma: float = 4.0) -> list[float]:
    vals = [float(v) for v in values]
    if len(vals) < 3:
        return vals
    mean = statistics.fmean(vals)
    sd = statistics.pstdev(vals) or 1.0
    return [v for v in vals if abs(v - mean) <= max_sigma * sd]


def registry(endpoints: dict[str, str] | None = None) -> list[Connector]:
    endpoints = endpoints or {}
    return [
        OpcUaConnector(endpoints.get("opcua", "opc.tcp://10.8.4.21:4840"), simulate=True),
        ModbusConnector(endpoints.get("modbus", "10.8.4.39:502"), simulate=True),
        CameraConnector(endpoints.get("camera", "10.8.4.51:9000"), simulate=True),
        HttpCameraConnector(endpoints.get("camera_http", ""), simulate=True),
        CsvConnector(endpoints.get("mes", ""), kind="mes", simulate=True),
        CsvConnector(endpoints.get("quality", ""), kind="quality", simulate=True),
        RestConnector(endpoints.get("cmms", "https://cmms.local/api"), simulate=True),
        SapQmConnector(endpoints.get("sap", "https://sap.local"), simulate=True),
        SapPmConnector(endpoints.get("sap", "https://sap.local"), simulate=True),
        FactoryTalkConnector(endpoints.get("factorytalk", "opc.tcp://10.8.4.71:4840"), simulate=True),
        S7Connector(endpoints.get("s7", "10.8.4.61:102"), simulate=True),
    ]


def connector_catalog() -> list[dict[str, Any]]:
    return [
        {"id": "opcua", "name": "OPC-UA", "phase": "1.1", "status": "shipped", "extra": "asyncua", "systems": "Kepware, Siemens, Beckhoff"},
        {"id": "modbus", "name": "Modbus TCP/RTU", "phase": "1.1", "status": "shipped", "extra": "pymodbus", "systems": "Legacy PLCs"},
        {"id": "camera", "name": "Inspection camera feed", "phase": "1.1", "status": "shipped", "extra": "", "systems": "Keyence, Cognex, generic TCP/IP"},
        {"id": "camera-http", "name": "HTTP camera snapshot", "phase": "1.1", "status": "shipped", "extra": "", "systems": "Generic JPEG snapshot URL"},
        {"id": "mes", "name": "MES / ERP batch CSV", "phase": "1.1", "status": "shipped", "extra": "", "systems": "SAP, Oracle, custom"},
        {"id": "quality", "name": "Quality history loader", "phase": "1.1", "status": "shipped", "extra": "", "systems": "6-month case import"},
        {"id": "cmms", "name": "Maintenance CMMS", "phase": "1.1", "status": "shipped", "extra": "", "systems": "REST"},
        {"id": "sap-qm", "name": "SAP QM", "phase": "2.2", "status": "shipped", "extra": "", "systems": "Inspection lots"},
        {"id": "sap-pm", "name": "SAP PM", "phase": "2.2", "status": "shipped", "extra": "", "systems": "Work orders"},
        {"id": "factorytalk", "name": "Rockwell FactoryTalk", "phase": "2.2", "status": "shipped", "extra": "asyncua", "systems": "Logix tags"},
        {"id": "s7", "name": "Siemens S7 / TIA", "phase": "2.2", "status": "shipped", "extra": "python-snap7", "systems": "S7-1200/1500"},
        {"id": "rest", "name": "Generic REST/GraphQL", "phase": "2.2", "status": "shipped", "extra": "", "systems": "Any API"},
        {"id": "supplier", "name": "Supplier batch / certificate import", "phase": "2.2", "status": "shipped", "extra": "", "systems": "CoA / CoC"},
    ]


def import_batches_from_csv(path: str | Path) -> list[dict[str, Any]]:
    rows = read_csv_records(path)
    out = []
    for r in rows:
        out.append(
            {
                "id": r.get("batch_id") or r.get("id") or "",
                "material": r.get("material", ""),
                "supplier": r.get("supplier", ""),
                "lot": r.get("lot", ""),
                "received": r.get("received", ""),
                "certificate": r.get("certificate", ""),
                "moisture_pct": float(r["moisture_pct"]) if r.get("moisture_pct") else None,
                "hydrogen_ppm": float(r["hydrogen_ppm"]) if r.get("hydrogen_ppm") else None,
                "notes": r.get("notes", ""),
            }
        )
    return out
