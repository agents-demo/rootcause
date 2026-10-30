# Example own case: pump housing porosity

A complete example for **My workspace**, with a filled-in case and real files to upload. It is a
teaching case, not a customer record: the image and CSVs are generated for this repository and are
labelled as such.

Files live in [`web/public/examples/pump-housing`](../web/public/examples/pump-housing):

| File | What it is | Use it as |
|---|---|---|
| `case.json` | The fields to fill in, plus the file list | Loaded by **Load the example case** |
| `casting-ct.jpg` | A loupe/borescope-style capture of the boss with pores and a hairline crack | Attach as the inspection image |
| `sensor-window.csv` | 24 rows of die temperature, injection pressure, cycle time and cavity vacuum across the shift | Attach as evidence |
| `batch-record.csv` | Three batches, including B-7781 at 1.9 ppm hydrogen against a 1.4 ppm limit | Attach as evidence |

The image is synthetic (generated with a fixed script, no customer or third-party data). The CSVs are
realistic but generated for the example. Do not present them as measured plant data.

## Load it

1. Open **My cases** (the home screen).
2. Press **Load the example case**.
3. The case opens as `RC-2026-0001` with the image on the canvas, the two CSVs under **Attached
   files**, and the working cause **Ejector pin over-travel**.

The same case can be created by hand with **New case** and the values below.

## What to fill in

| Field | Example value | Why |
|---|---|---|
| Defect | `Porosity cluster at the bearing boss` | What failed, in the language of the line |
| Part | `Pump housing, die-cast AlSi9Cu3` | Material matters for the cause |
| Line | `Line 4` | Which line owns the case |
| Batch / lot | `B-7781` | Links to the batch record |
| Severity | `High` | Drives the decision queue |
| Station | `End-of-line inspection` | Where it was found |
| Shift | `B` | Who was running |
| Working cause | `Ejector pin over-travel` | A deliberate first hypothesis, not the answer |
| What did you observe? | See `case.json` | The evidence that lets the engineer reject the first cause |
| Evidence files | The JPG and two CSVs | Real files, stored in this browser |

## What the app computes

When you create the case with the image and the two CSVs attached, the app parses the files — not
the prose — and shows the analysis above the workspace:

| Signal | Value | Verdict |
|---|---|---|
| Cavity vacuum | 135.25 → 211.88 mbar | +56.7%, sustained rise |
| Hydrogen | 1.9 ppm vs 1.4 limit | batch exception |

It then ranks the causes on the evidence factors:

| Cause | Confidence | Why |
|---|---|---|
| **Gas porosity from insufficient die venting** | **86%** | hydrogen over limit, vacuum rise, subsurface voids |
| Ejector pin over-travel (your first guess) | 2% | a surface feature cannot initiate a crack 0.4 mm below the surface |

It also names the **prevention checks** (die venting below 180 mbar, revalidate the door seal,
hold the rest of the batch) and what would **falsify** the answer (a CT with no voids, or hydrogen
below the limit). That is the smart part: the app argues with your first guess using the files you
attached.

## The trust beat to run

1. **Open the case.** The image shows the pores and the crack; the analysis strip reports the two
   signals; the ranked causes put gas porosity first and your ejector-pin guess second.
2. **Read the disagreement.** The crack starts 0.4 mm below the surface; the ejector marks are on
   the opposite face. The app shows the evidence IDs and the falsifier.
3. **Accept the evidence-backed cause.** In Review, accept *Gas porosity from insufficient die
   venting*. If you disagree, reject it with the reason; the ranking stores the correction.
4. **Sign the report.** Approve it and check the audit trail, the report version and the attached
   files.
5. **Read the prevention checks.** The app names what to fix before the next batch, not just what
   happened.

## Watch the walkthrough

A 1:39 narrated walkthrough of this flow, built from real app states:
[`web/public/demo/rootcause-walkthrough.mp4`](../web/public/demo/rootcause-walkthrough.mp4)
(or https://jiuwendemos.github.io/rootcause/demo/rootcause-walkthrough.mp4).

## How attachments behave

- Accepted: PNG, JPEG, WebP and CSV, up to 1.5 MB each.
- Images appear on the case canvas; every file is listed under **Attached files** with a download link.
- Each file becomes an evidence item (`EV-02`, `EV-03`, …) in the case and in the report's evidence
  section.
- Files are stored as data URLs in this browser's local storage, together with the case. They do not
  leave the browser. Large sets will hit the browser storage limit; use one or two files per case.

## What the example does not prove

- No machine, MES or camera connection: the CSVs are attached, not read from a line.
- No detector run on the image: the case is entered by hand.
- No server persistence: clearing site data deletes the case and its files.
- The numbers in the CSVs are realistic but not measured; the image is synthetic.

For the reference pack with live-style sensor series, switch to **Reference data** from Admin, the
command palette or the More sheet.
