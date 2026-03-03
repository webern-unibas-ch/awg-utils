# Unify Link Box IDs

## Overview

This utility unifies the `svgGroupId` attributes in linkBoxes from the textcritics JSON file and the corresponding `id` attributes with `class="link-box"` in SVG files.

## Purpose

Link boxes in the textcritics JSON represent cross-references between document scans. When unifying IDs, this tool ensures consistency between:
- The `svgGroupId` in JSON linkBoxes
- The corresponding `id` attribute in SVG elements with `class="link-box"`

## Naming Convention

The new ID format for each linkBox is: **`{entry_id}to{sheetId}`**

Where:
- `entry_id`: The `id` field of the textcritics entry (e.g., `M_317_Sk1`)
- `sheetId`: The target sheet ID from the linkBox's `linkTo.sheetId` field (e.g., `M_317_Sk2`)

### Example Transformation

**Before:**
```json
{
  "id": "M_317_Sk1",
  "linkBoxes": [
    {
      "svgGroupId": "g6407",
      "linkTo": {
        "complexId": "op25",
        "sheetId": "M_317_Sk2"
      }
    }
  ]
}
```

**SVG Before:**
```xml
<g id="g6407" class="link-box">
  <path/>
</g>
```

**After:**
```json
{
  "id": "M_317_Sk1",
  "linkBoxes": [
    {
      "svgGroupId": "M_317_Sk1toM_317_Sk2",
      "linkTo": {
        "complexId": "op25",
        "sheetId": "M_317_Sk2"
      }
    }
  ]
}
```

**SVG After:**
```xml
<g id="M_317_Sk1toM_317_Sk2" class="link-box">
  <path/>
</g>
```

## Usage

### Python Script

Run the script directly (edit the paths first):

```bash
cd /path/to/unify_tkk_ids
python3 unify_link_box_ids.py
```

### Configuration

Edit `unify_link_box_ids.py` and modify these paths:

```python
json_path = './tests/data/textcritics.json'  # Path to textcritics JSON
svg_folder = './tests/img/'                  # Path to SVG files folder
```

### Programmatic Usage

```python
from unify_link_box_ids import unify_link_box_ids

json_path = 'path/to/textcritics.json'
svg_folder = 'path/to/svg/files'

success = unify_link_box_ids(json_path, svg_folder)
if success:
    print("Link box IDs unified successfully!")
```

## Processing Steps

1. **Load and Validate**: Loads JSON and identifies all SVG files
2. **Extract LinkBoxes**: For each entry, extracts all linkBoxes
3. **Find Matching SVGs**: Locates SVG files containing each linkBox ID
4. **Update JSON**: Changes `svgGroupId` to new format
5. **Update SVGs**: Updates corresponding `id` attributes in SVG files
6. **Save Results**: Writes modified JSON and SVG files

## Error Handling

The tool handles several error conditions:

- **Missing sheetId**: Reports entries where no `sheetId` is found
- **Missing svgGroupId**: Skips malformed linkBox entries
- **Multiple Occurrences**: Warns if an ID appears in multiple SVG files
- **No SVG Match**: Reports when linkBox ID cannot be found in any SVG

## Related Tools

- **unify_tkk_ids.py**: Unifies TKK group IDs (class="tkk") - similar tool for music annotation comments
- **utils/extraction_utils.py**: Helper functions for data extraction
- **utils/svg_utils.py**: SVG file utilities and regex patterns

## Technical Details

### Modified Files

1. **utils/extraction_utils.py**: Added `extract_link_boxes()` function
2. **utils/svg_utils.py**: Added:
   - `update_svg_id_by_class()`: Generic SVG ID updater for any CSS class
   - `find_matching_svg_files_by_class()`: Find SVG files by class name
3. **unify_link_box_ids.py**: New file with main unification logic

### SVG Class Matching

The tool searches for SVG elements with:
```xml
<g id="old-id" class="link-box">
```

Both single and double quotes are supported:
```xml
<g id='old-id' class='link-box'>
```

And flexible attribute ordering.

## Testing

Test with the included test data:

```bash
cd unify_tkk_ids
python3 -c "
import json
with open('tests/data/textcritics.json') as f:
    data = json.load(f)
for entry in data['textcritics'][:3]:
    if entry.get('linkBoxes'):
        print(f\"{entry['id']}: {len(entry['linkBoxes'])} linkBoxes\")
"
```

Then run the unification to see it in action.
