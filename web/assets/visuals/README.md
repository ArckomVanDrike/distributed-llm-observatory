# DLLO Visual Asset Bank

This directory contains the canonical visual asset bank for the current
Distributed LLM Observatory (DLLO) UI direction.

## Design language

The asset set uses a consistent visual vocabulary:

- deep blue, violet, and cyan;
- distributed networks and connected globes;
- observatory / telescope imagery;
- scientific dashboards and measurement systems;
- AI agents and laboratory imagery.

The detailed dashboard-style illustrations are intended as visual/hero artwork,
not as literal screenshots of the DLLO application.

## Asset roles

| File | Category | Intended use |
| --- | --- | --- |
| `experiment-failed.webp` | State | Failed experiment / execution error |
| `experiment-complete.webp` | State | Successful experiment / completed run |
| `no-agent.webp` | State | No agent connected or configured |
| `no-data.webp` | State | Empty history / no observations yet |
| `network-background.webp` | Background | Distributed network sections and geographic views |
| `starfield-background.webp` | Background | Neutral Observatory background |
| `observatory-poster.webp` | Hero | About / landing / Observatory overview |
| `technical-report.webp` | Feature | Agent technical report introduction |
| `benchmark-lab.webp` | Feature | Benchmark execution / model measurement |
| `distributed-observer-node.webp` | Feature | Observer node / distributed observation concept |
| `agent-lab.webp` | Feature | Agent Lab and Test Your Agent |
| `observatory-hero.webp` | Hero | Primary Observatory landing visual |
| `network-globe-eurasia.webp` | Geographic | Geographic observation / Europe-Asia view |
| `network-globe-americas.webp` | Geographic | Geographic observation / Americas view |
| `earth-horizon.webp` | Background | Wide geographic / network hero background |
| `observatory-mark.webp` | Brand | Detailed emblem, splash, profile, large-format brand use |

## Usage guidance

### State illustrations

`experiment-failed.webp`, `experiment-complete.webp`, `no-agent.webp`, and
`no-data.webp` work best as empty/error/success states. Their lighter 3D style
is intentionally distinct from the darker Observatory hero artwork.

### Hero and feature illustrations

`observatory-poster.webp`, `technical-report.webp`, `benchmark-lab.webp`,
`distributed-observer-node.webp`, `agent-lab.webp`, and
`observatory-hero.webp` should be treated as illustrations. Some contain
stylized generated dashboard text and should not be presented as screenshots
of real DLLO output.

### Geographic assets

The globe assets communicate observations from distributed locations. They
must not be used to imply provider datacenter or serving location.

Use wording such as:

> Observed from CL-Los-Lagos

rather than claims about where a model or provider is hosted.

### Brand mark

`observatory-mark.webp` is a detailed emblem and works best at medium or large
sizes. A simplified mark should eventually be created for favicon, compact
navbar, and very small app-icon use.

## Image processing

The assets are stored as WebP without resizing.

- Transparent source images retain alpha and are encoded losslessly.
- Opaque backgrounds use high-quality WebP encoding.
- Original source dimensions are preserved.
- No artificial upscaling has been applied.

See `manifest.json` for dimensions, alpha information, category, intended use,
and original source filenames.
