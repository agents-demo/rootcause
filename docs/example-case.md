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

## The trust beat to run

1. **Open the case.** The canvas shows the pores and the crack; the working cause is *Ejector pin
   over-travel*.
2. **Read the note.** The crack starts 0.4 mm below the surface and does not follow the ejector-pin
   witness marks; vacuum drifted from 118 to 221 mbar; the batch was accepted at 1.9 ppm hydrogen
   against 1.4.
3. **Reject the cause.** In Review, reject *Ejector pin over-travel* with:
   *"Crack starts below the surface; the ejector marks are on the opposite face."*
4. **Add the real cause.** Add *Gas porosity from insufficient die venting* with the vacuum and
   hydrogen reasoning.
5. **Accept and sign.** Approve the report and check the audit trail and the report version.

This is the same shape as the reference trust beat, but with your own case and your own files.

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
