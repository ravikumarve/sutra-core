# Assets

| File | Purpose |
|------|---------|
| `logo.svg` | Scalable vector logo for GitHub README |
| `logo.png` | Rendered PNG 512×512 (generate from SVG) |

## Generating PNG from SVG

```bash
# Using Inkscape
inkscape logo.svg -o logo.png -w 512 -h 512

# Or ImageMagick
convert logo.svg -resize 512x512 logo.png
```

## Social Preview

For the GitHub social preview image (1280×640px), create a banner combining:
- Logo (centered left)
- "SUTRA Core" + tagline
- A screenshot of the WhatsApp flow

Set it in: Repository → Settings → Social preview
