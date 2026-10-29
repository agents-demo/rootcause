# Connectors

Every adapter exposes `test()`, a read method and a provenance record. Hardware libraries are
optional: when they are missing, the adapter runs in **simulated** mode and says so.

| Adapter | Class | Extra | Reads | Phase |
|---|---|---|---|---|
| OPC-UA | `OpcUaConnector` | `asyncua` | 10–20 machine tags, 1 s poll | 1.1 |
| Modbus TCP/RTU | `ModbusConnector` | `pymodbus` | Holding registers from older PLCs | 1.1 |
| Camera | `CameraConnector` | — | Trigger + metadata from Keyence/Cognex/generic TCP | 1.1 |
| MES / ERP CSV | `CsvConnector` | — | Batch records from a drop folder | 1.1 |
| Quality history | `CsvConnector` | — | Six-month case import | 1.1 |
| CMMS | `RestConnector` / `CmmsConnector` | — | Work orders, equipment history | 1.1 |
| SAP QM | `SapQmConnector` | — | Inspection lots | 2.2 |
| SAP PM | `SapPmConnector` | — | Work orders | 2.2 |
| Rockwell FactoryTalk | `FactoryTalkConnector` | `asyncua` | Logix tags | 2.2 |
| Siemens S7 / TIA | `S7Connector` | `python-snap7` | DB blocks | 2.2 |
| Generic REST / GraphQL | `RestConnector` | — | Any API | 2.2 |
| Supplier certificates | `CsvConnector` | — | CoA/CoC records | 2.2 |

## Configuration

```python
from rootcause.connectors import OpcUaConnector, normalise_frame

conn = OpcUaConnector("opc.tcp://10.8.4.21:4840", simulate=False)
status = conn.test()
assert status.reachable, status.detail
raw = conn.read(["ns=2;s=Furnace.Temp", "ns=2;s=Furnace.Pressure"])

clean = normalise_frame(
    raw["tags"],
    mapping={"Furnace.Temp": "pour_temp", "Furnace.Pressure": "pressure"},
    units={"pour_temp": "C", "pressure": "bar"},
)
```

Rules:

- Never silently average a bad value. `normalise_frame` drops non-numeric/NaN/absurd values and
  reports `quality: "partial"` with the dropped tags.
- Keep the raw tag name and the mapped name in the provenance record.
- The API never writes to a machine. Connectors are read-only by design.
- Camera images stay on site. The demo returns metadata only; production passes bytes to the NPU
  broker inside the factory network.

## Tag map checklist for a pilot

- [ ] Faceplate value and tag name agreed with the customer.
- [ ] Unit and scaling confirmed against the SCADA screen.
- [ ] Sample interval and expected jitter recorded.
- [ ] Spec limits agreed; out-of-spec counters reconciled.
- [ ] Timestamp source (PLC vs SCADA vs MES) recorded; clock drift measured.
- [ ] Read-only service account, no write permissions.
- [ ] 24-hour soak test with a known defect.

## Failure modes

| Symptom | Likely cause | Action |
|---|---|---|
| `test()` false, timeout | VLAN/firewall | Open the port from the RootCause host only |
| Values match but timestamps drift | PLC clock | Record the offset; do not “fix” it in the ranking |
| Bad values every shift change | Gateway restart | Drop and flag; do not interpolate |
| Camera trigger returns no image | Vendor SDK / port | Use the generic TCP reader or the vendor export |
| SAP QM returns 401 | Service account | Read-only role, ticket refresh |
| Duplicate batch ids | ERP reuse | Add supplier + received date to the key |

## Adding an adapter

1. Subclass `Connector` and set `id`, `protocol`.
2. Implement `test()` and a read method that returns a plain dict.
3. Use `simulate=True` as the default so the demo and tests run without hardware.
4. Add a `Connector` entry in `demo/build_pack.py`, a backend test, and a row in this table.
5. Return a provenance record: endpoint, tag, unit, timestamp, quality.
