# XY Scope Display

A Home Assistant integration for an oscilloscope used as a vector display: a
stereo DAC drives the scope in X-Y mode, and the box behind it
([xy-bench](#the-box)) draws whatever frames it is sent as line art.

The scope shows one thing: Alfie. The Alfie
integration's scope card renders him (and his rotation of screens) and pushes
each frame to the box. This integration only exposes the display as a device:

| Entity | What it does |
|---|---|
| **Display power** (switch) | Wraps the scope's smart outlet. Off has to cut the power: a stopped signal parks the beam on one spot and burns the phosphor. |
| **Scale** (number) | 0..1 of full deflection, capped at the maximum calibrated on the box. |
| **Output** (sensor) | `playing`, `stopped` or `error`: the audio feed into the scope. |
| **Frame rate** (sensor) | Long frames run slower, down to the box's floor (50 fps by default). |

What is on the scope is Alfie's business (his rotations, `alfie.step_rotation`,
`alfie.show_rotation`); automations here only decide when the display is on.

## Install

Through [HACS](https://hacs.xyz): *HACS → ⋮ → Custom repositories*, add
`https://github.com/alfie-mitten/scope-display-integration` as an
**Integration**, install **XY Scope Display**, and restart Home Assistant.

Requires Home Assistant 2026.9 or newer.

## Set up

*Settings → Devices & services → Add integration → XY Scope Display*, then
the box's **host**, **port** (8080 by default) and **token** (its
`XYBENCH_TOKEN`). *Configure* picks the scope's outlet; a switch or light
with "scope" in its name is guessed.

## The box

```
GET /api/status    {"api": 1, "boot", "scale", "max_scale", "playing",
                    "error", "fps", "alfie": {"age", "strokes"}}
PUT /api/screen    {"scale": 0.6}        an empty body changes nothing
PUT /api/strokes   a frame of Alfie (from his scope card)
```

Writes carry `Authorization: Bearer <XYBENCH_TOKEN>`.

## Development

```
uv venv -p 3.14 .venv
VIRTUAL_ENV=.venv uv pip install -r requirements_test.txt
.venv/bin/python -m pytest -q
```
