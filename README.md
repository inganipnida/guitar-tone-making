# Quad Cortex Tone Copy Assistant

A local FastAPI web app that analyzes a short guitar audio segment and recommends a **closest playable Quad Cortex approximation**. This MVP is intentionally rule-based and transparent so it is easy to understand, debug, and replace with ML later.

## Product framing

- The app does **not** promise perfect tone cloning.
- It returns a **recommended Quad Cortex starting point**.
- It is designed to be practical for musicians and maintainable for engineers.

## Architecture overview

The app uses a layered design:

- **Routes/UI layer**: FastAPI endpoints and Jinja templates for upload, result, and history pages.
- **FFmpeg + preprocessing layer**: validates durations, trims the requested segment, converts to mono, normalizes sample rate, and applies loudness normalization.
- **Feature extraction layer**: extracts RMS, spectral shape, harmonic/percussive balance, onset strength, sustain proxy, band energy ratios, distortion heuristics, ambience heuristics, and mixed-audio heuristics.
- **Tone classification layer**: maps extracted features into an intermediate `AbstractToneProfile` and classifies the archetype.
- **Guitar compensation layer**: lightly adjusts the profile depending on the selected guitar type.
- **Quad Cortex mapping layer**: maps the abstract profile to a primary chain plus three alternatives using JSON-backed device/rule data.
- **Persistence layer**: stores past analyses in SQLite for quick recall.

## Project structure

```text
app/
  main.py
  config.py
  routes/
    ui.py
    api.py
  services/
    ffmpeg_service.py
    audio_preprocess.py
    feature_extractor.py
    tone_classifier.py
    guitar_compensation.py
    qc_mapper.py
    analysis_pipeline.py
  db/
    models.py
    database.py
  schemas/
    analysis.py
  templates/
    base.html
    index.html
    result.html
    history.html
  static/
    style.css
  data/
    qc_devices.json
    qc_rules.json
  uploads/
requirements.txt
README.md
```

## MVP feature coverage

### Phase 1
- FastAPI app scaffold.
- Jinja2 templates and basic CSS.
- Audio upload flow with extension and size validation.
- Segment selection with server-side validation and a 30-second MVP cap for practical analysis.
- FFmpeg duration probing plus trimming/normalization.
- SQLite persistence via SQLModel, including stored processed segment metadata.

### Phase 2
- Audio preprocessing with librosa.
- Rule-based feature extraction and guitar-tone-oriented heuristics.
- Tone archetype classification.
- Guitar compensation adjustments.
- Mixed-audio confidence and warning heuristics.

### Phase 3
- Quad Cortex mapping engine with intermediate abstract tone profile.
- Primary recommendation plus three alternative chains.
- Musician-friendly result page.
- Recent history page.

### Phase 4
- Requirements file.
- Setup and run documentation.
- JSON data files for QC blocks/rules.
- TODO list for future extension.

## Requirements

Install system dependencies first:

- Python 3.11+
- FFmpeg available on your `PATH`

On Ubuntu/Debian:

```bash
sudo apt-get update
sudo apt-get install -y ffmpeg
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run locally

```bash
uvicorn app.main:app --reload
```

Then open `http://127.0.0.1:8000`.

## How to use

1. Upload a short guitar-focused audio clip.
2. Choose the analysis start and end time in seconds.
3. Choose the guitar type closest to the source instrument.
4. Submit the form.
5. Review the archetype, tonal summary, primary chain, alternatives, parameter ranges, diagnostics, reasoning, and any warnings.

## Notes on the URL field

The URL input is a **placeholder only** in this MVP. The app currently requires an uploaded local audio file and stores the URL string only for future expansion.

## Data files

- `app/data/qc_devices.json` stores a small knowledge base of generic Quad Cortex-compatible block categories and placeholder device names.
- `app/data/qc_rules.json` stores explainable rule templates for each archetype and variant.

## Validation and safety notes

- Uploads are sanitized with `secure_filename`.
- The selected segment length is capped for faster, more stable analysis.
- File extensions are allow-listed.
- File size is capped.
- Time ranges are validated server-side.
- FFmpeg/ffprobe missing-binary errors are converted into user-friendly responses.
- Uploaded files are stored in a dedicated `app/uploads/` folder.

## Example extension points

- Replace rule-based classification with a trained model.
- Add source separation before feature extraction.
- Add support for YouTube/video/audio URLs.
- Add waveform preview and browser-side segment selection.
- Add export to QC preset notes or structured patch format.
- Add user accounts and saved favorite presets.

## TODO

- Add async background jobs for larger files.
- Add automatic source-isolation / stem extraction.
- Improve ambience detection with decay-tail estimation.
- Improve fuzz detection with clipping and odd-harmonic heuristics.
- Add actual Quad Cortex model library mapping if product naming accuracy is needed.
- Add tests around feature extraction and classification thresholds.
- Add richer API schemas for external integrations.

## Design rationale

The central architecture choice is the `AbstractToneProfile`. Raw audio features are noisy and too low-level to map directly to musician-facing preset suggestions. By first converting them into interpretable control dimensions like gain, brightness, mid push, tightness, compression, and space, the recommendation layer becomes easier to reason about, tune, and eventually replace with learned models.
