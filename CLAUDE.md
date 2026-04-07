# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

### Running Tests
- Run all tests: `python tests/test.py`
- Run a specific test module: `python -m pytest tests/test_geometry.py` (if pytest installed)
- The test suite includes: geometry block tests, full file roundtrip tests, river modification tests, cross-section modification tests.
- **Important**: Before adding new test files, preprocess them with sed to normalize formatting (spaces around `=`, `,`, trailing whitespace). Use commands from README:
  ```bash
  sed -i -e 's/ *= */=/g' -e 's/ *, */,/g' -e 's/ \./0\./g' -e 's/[[:space:]]*$//' tests/leak.g01
  sed -i -e '/^$/N;/^\n$/D' tests/leak.g01
  ```

### Linting and Formatting
- Ruff is configured for linting (see `ruff.toml`). Run with `ruff check .`
- Line length limit: 120 characters.

### Package Management
- No `setup.py` or `pyproject.toml` found; treat as a local module.
- Optional dependencies: `rasterio` and `numpy` are used only in `CrossSectionModel` for DEM elevation extraction. Install with `pip install rasterio numpy` if needed.
- No virtual environment management files; assume user manages their own environment.

## Architecture Overview

### Three‑Layer Design
1. **Core Layer** (`parseras/core/`): Low‑level file parsing and generation.
   - `file.py`: `GeometryFile` class – main entry point. Splits `.g01` files into blocks, determines block type, instantiates appropriate `RASStructure` subclass.
   - `structures.py`: Abstract `RASStructure` base class and concrete block types (`River`, `CrossSection`, `Head`, etc.). Each subclass defines `_key_value_types` mapping keys to `Value` types.
   - `values.py`: `Value` hierarchy (`StringValue`, `IntValue`, `FloatValue`, `CommaSeparatedValue`, `SpaceSeparatedValue`, `LinesValue`, `DataBlockValue`). Handles parsing, formatting, and type‑safe access.

2. **Model Layer** (`parseras/models/`): Business‑logic wrappers that operate on `GeometryFile` objects.
   - `cross_section.py`: `CrossSectionModel` – provides methods to query/update cross‑section geometry, Manning values, bank stations, and Sta/Elev tables. Can integrate with DEM rasters (optional `rasterio` dependency).
   - `river.py`: `RiverModel` – manages river reach polylines and creation/updating of river blocks.
   - Models return JSON strings with `{"status": "...", "data": {...}, "message": "..."}` pattern.

3. **Public API** (`parseras/__init__.py`):
   - Exports `GeometryFile`, all block structure classes, all value classes, and the two models.

### Block Ordering
- Each block type has an `order` attribute (float). `GeometryFile.generate()` sorts blocks by `order` to produce a correctly ordered `.g01` file.
- Order defaults: Head (0), River (10), CrossSection (30), StorageArea (50), BreakLine (150), Foot (200). Cross‑section and lateral‑weir order is refined by station (30 + 1/station).

### Key‑Value Parsing
- Blocks are lists of lines; each non‑empty line is a `key=value` pair.
- `RASStructure._parse_lines` uses `_key_value_types` to decide how to parse each key:
  - Simple types (`StringValue`, `IntValue`, `FloatValue`): direct conversion.
  - `CommaSeparatedValue` / `SpaceSeparatedValue`: split by delimiter, wrap each element in a `Value` subclass.
  - `DataBlockValue`: multi‑line data blocks with fixed‑width columns. Header line contains count; subsequent lines contain formatted numbers.
  - `LinesValue`: multi‑line text blocks where the first line gives the line count.
- The system automatically skips unrecognized keys (e.g., "Permanent Ineff").

### Adding a New Block Type
1. Create a new subclass of `RASStructure` in `structures.py`.
2. Define `_key_value_types` dictionary mapping keys to value type (or tuple with type + kwargs).
3. Set `order` class attribute.
4. Add mapping in `GeometryFile._determine_block_type` (or extend `block_type_map`).

### Adding a New Value Type
1. Subclass `Value` in `values.py` and implement `__init__`, `__str__`, `value` property.
2. Update `RASStructure._parse_lines` if needed (the generic handling works for simple types).

## Development Notes

### Test Data
- Test `.g01` files live in `tests/data/`. The repository includes `all.g01`, `leak.g01`, `thin.g01`, `Muncie.g01`, and individual block examples.
- Generated output files end with `.output.g01` (git‑ignored).

### Git Status
- The `main` branch currently has modified `tests/test_full_file.py` and untracked test data files (`leak.tif`, `leak_updated.g01`, `thin.g01`). Verify whether these should be committed.

### External Dependencies
- The library itself has no hard dependencies; it can be used standalone.
- For DEM elevation extraction (`CrossSectionModel.update_or_create_cross_section` with `tif_path`), `rasterio` and `numpy` must be installed.
- No version pinning; assume latest compatible versions.

### Error Handling
- Models return JSON with `status` ("success" or "error") and `message` fields.
- Parsing errors raise `ValueError`; calling code should catch exceptions.

### Performance Considerations
- Data blocks are stored as tuples of `Value` objects; operations are in‑memory.
- Large geometry files may have many points; consider memory usage when processing.

### HEC‑RAS File Format Notes
- The `.g01` format is line‑oriented, block‑based, with loose spacing rules.
- The parser normalizes spaces around `=` and `,`; trailing whitespace is removed.
- Empty lines separate blocks.
- The library aims to preserve the exact numeric formatting (fixed‑width columns) when regenerating files.