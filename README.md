```markdown
# Empire Builder — board data

Machine-readable data for the Mayfair *Empire Builder* board (5th edition,
North America), rebuilt from photographs of the six physical board pieces.

## Contents

```
Cards/                        photos of the demand cards + eb-demand-cards.json
Map/                          photos of the six board pieces + the board data
Tools/                        the pipeline that produced it
```

### Data files

| File | What it holds |
|---|---|
| `Map/eb-board-mileposts.json` | 4,510 lattice cells: 1,415 clear mileposts, 623 mountains, 104 city cells |
| `Map/eb-cities-verified.json` | all 62 cities with tier and loads |
| `Map/eb-crossings-verified.json` | 385 crossings at +$2M, 59 impassable edges, 198 confirmed-normal |
| `Cards/eb-demand-cards.json` | all 136 demand cards |

## Coordinate frame

Everything uses one triangular-lattice frame, `(a, b)`.

- Axis **a** runs at 30° (down and to the right on the printed board);
  axis **b** runs at 90° (straight down).
- The six neighbours of a cell are `(±1,0)`, `(0,±1)`, `(1,-1)`, `(-1,1)`.
- The frame is **pinned to Phoenix at (1,16)**. Per-piece lattice origins are
  arbitrary and shift if the detector is re-run, so this anchor is what keeps
  coordinates stable across rebuilds. Don't remove it.

Earlier data was tagged in a different frame taken from a black-and-white scan.
It converts with:

```
(a, b) = [[1, -1], [0, 1]] · (col, row) + (-16, -6)
```

That mapped 60 of the 62 original city entries straight onto detected cities,
which is what confirmed the transform.

## Cost model (from the board's printed legend)

- Clear milepost $1M, mountain $2M
- Major city $5M, medium city $3M (max 3 players), small city $3M (max 2)
- River or lake channel: **+$2M** on top of the milepost cost
- Ocean inlets and most lake coastlines are impassable
- Major city hexagons: the 7 cells (centre + ring) are pre-built free track
  everyone may use, so each contracts to one zero-cost node
- $20M build cap per turn · 2 build turns at start · $50M starting cash
- Win: $250M and 6 major cities connected

## Caveats

- **The crossing set follows house rules**, not the printed rules. The legend
  states there are exactly 9 legal lake-channel crossings; which 9 those are was
  never independently confirmed. `house_marked_crossings` in the crossings file
  records the hand-marked set separately if you ever want to reconcile it.
- `corrections_local.json` holds 169 manual review marks made against the
  photos. These are re-applied on every run and override the detector — a
  rebuild without this file will silently revert them.

## Rebuilding

```
python Tools/eb_classify.py Map/NorthWest.jpg    NorthWest
python Tools/eb_classify.py Map/NorthCentral.jpg NorthCentral
python Tools/eb_classify.py Map/NorthEast.jpg    NorthEast
python Tools/eb_classify.py Map/SouthWest.jpg    SouthWest
python Tools/eb_classify.py Map/SouthCentral.jpg SouthCentral
python Tools/eb_classify.py Map/SouthEast.jpg    SouthEast 1400,2950,4050,4950

python Tools/register.py     # canonical basis per piece  -> K.json
python Tools/offsets2.py     # pairwise piece offsets
python Tools/assemble.py     # global placement           -> placement.json
python Tools/merge.py        # single board               -> eb-board-mileposts.json
```

SouthEast takes a fourth argument: the bounding box of the printed rules legend,
which must be excluded or its example symbols are detected as map features.

Crossings are handled separately by `rivers.py` (river edges by colour),
`channels.py` (lake channels by blue coastline) and `lakemarks.py` (reads
hand-drawn crossing marks off annotated photos).

Requires Python 3 with `opencv-python`, `numpy` and `scipy`.

## How the board was read

Mileposts are found by fitting the lattice to each photo and then classifying by
what sits at each predicted position — not by detecting blobs and clustering
them, which false-positives badly on city label text. The fit is quadratic in
`(a, b)`; a plain affine fit leaves ~20px of residual because a handheld photo
of a thick board isn't planar. Correspondences are grown outward from a small
central patch rather than fitted globally, since perspective drift otherwise
snaps cells onto the wrong lattice position.

Symbols bisected by a die-cut edge are matched against only the part of the
template that lies on that piece, then resolved against the neighbouring piece
during the merge.
```
