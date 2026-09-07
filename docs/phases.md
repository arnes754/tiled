# Build phases

## P1 - Floors, manual corners, ten SKUs   (2-3 weeks)
No models at all. Four draggable corners, warp, shading transfer, slider.
Proves the only question that matters - does it look convincing - before a
single GPU is paid for. If it does not convince here, ML does not rescue it.

## P2 - Automatic detection   (3-4 weeks)
Segmentation and depth propose the quad and the occlusion masks. Manual
handles stay forever as the correction path. Measure how often they get
touched; that number is the real accuracy metric.

## P3 - Walls   (3-4 weeks)
Multi-plane. Per-wall quads, the floor line as layout datum, courses running
up from it, correct behaviour at internal corners, around windows, behind the
vanity. Meaningfully harder than floors - its own phase for a reason.

## P4 - Catalogue and commerce   (2-3 weeks)
Full SKU import, filtering, m2 calculator from detected floor area, save and
share, hand-off to a quote or a showroom appointment. Where the retailer gets
its return.

## P5 - Generative finish   (ongoing)
Lighting harmonisation, contact shadows, a side-by-side quality gate against
the geometric render, per-SKU opt-out.

## Open questions for the retailer

- What do their tile assets look like today - flat, seamless, scale-known
  images per SKU, or catalogue photography? Ask for ten real SKUs before
  committing to any schedule.
- How many SKUs at launch, and who produces textures for the rest?
- Where does this live - product pages, standalone, or a showroom tablet?
  (A tablet is a far easier first target: controlled light, staff on hand,
  no mobile browser variance.)
- Is success more online orders, or more people walking into the branch?
  The whole funnel depends on the answer.
