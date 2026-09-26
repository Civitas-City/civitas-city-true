# GLB EXPORT & ANIMATION CHEAT SHEET
*For dummies - Step-by-step guide to generate and view Civitas City*

## 🚀 QUICK START (3 steps)

### Step 1: Generate GLB Exports
```bash
cd /Users/anthonyleavitt/SOVEREIGN_BUILD.nosync/Developer/in-development/NOVTN-os/NOVTN-os-DESCENT/civitas-arcology
/Applications/Blender.app/Contents/MacOS/blender -b out/CIVITAS_CITY_MASTER.blend --python civitas-export-all.py -- --out out/glb
```

### Step 2: Wait for completion
- **Time**: ~5-10 minutes (depends on your Mac)
- **Files created**: ~50+ GLB files (one per major component)
- **Output folder**: `out/glb/`

### Step 3: View in browser
- Open `out/glb/` in Finder
- Double-click any `.glb` file
- Opens in default 3D viewer or drag to a web-based viewer

## 📁 WHAT YOU'LL GET

### Major Components Exported:
- `CIVITAS_ARCOLOGY.glb` - The whole city (84 km × 84 km)
- `CIVITAS_SHIP_SenMaurader.glb` - Sen's Maurader
- `CIVITAS_SHIP_Airport_210KM.glb` - The Airport flagship
- `CIVITAS_FLEET_Military.glb` - All military vessels
- `CIVITAS_FLEET_Civilian.glb` - All civilian vessels
- `CIVITAS_FLEET_Commercial.glb` - Commercial fleet
- Plus cross-sections, ships, and more...

### Animation Info:
- **Canonical Week**: 168 hours of city time
- **Playback**: 1,008,000 frames (14.4x compression)
- **Preview**: 14-minute cut of hours 0-14
- **File**: `CIVITAS-PREVIEW-14MIN` collection

## 🎬 ANIMATION DETAILS

### What Animates:
- **Fleet**: Orbiting and station-keeping movements
- **Commercial**: Speed changes and light pulses
- **Broadcast**: Pulse array runs every 14 minutes
- **Defense Systems**: Armor deployment, weapon bays
- **Sen's Maurader**: ARK mode transformation
- **Dragon Systems**: Emission intensity changes

### Timeline Events (17 canonical events):
- Threat-level changes (armor/weapons deployment)
- Diplomatic status changes (greeting protocols)
- Broadcast array pulses
- Haven engine warmups
- Dazzle state transitions

## 🛠️ ADVANCED OPTIONS

### Export Specific Components Only:
```bash
# Export just the city arcology
/Applications/Blender.app/Contents/MacOS/blender -b out/CIVITAS_CITY_MASTER.blend --python civitas-export-all.py -- --out out/glb --skip-existing
```

### Change Animation Sampling:
```bash
# Sample every 10 frames instead of default
/Applications/Blender.app/Contents/MacOS/blender -b out/CIVITAS_CITY_MASTER.blend --python civitas-export-all.py -- --out out/glb --anim-step 10
```

### Export Without Compression:
```bash
# Larger files but faster export
/Applications/Blender.app/Contents/MacOS/blender -b out/CIVITAS_CITY_MASTER.blend --python civitas-export-all.py -- --out out/glb --no-draco
```

## 🌐 VIEWING OPTIONS

### Web Viewers (Free):
1. **[three.js viewer](https://threejs.org/examples/#webgl_loader_gltf)** - Drag & drop GLB
2. **[glTF-Viewer](https://sandbox.babylonjs.com/)** - Babylon.js viewer
3. **[model-viewer.dev](https://modelviewer.dev/)** - Google's viewer

### Desktop Viewers:
- **Blender** (free) - Open GLB directly
- **Sketchfab** (online) - Upload and view
- **Windows 3D Viewer** (if on Windows)

## 🔧 TROUBLESHOOTING

### Blender not found:
```bash
# Check if Blender is installed
/Applications/Blender.app/Contents/MacOS/blender --version

# If not, download from blender.org
```

### Export fails with memory error:
- Export components one at a time
- Use `--skip-existing` to resume interrupted exports
- Close other applications to free memory

### Animation not playing:
- Some viewers don't support animation
- Try different web viewer
- Check if component has animation (not all do)

### Files too large:
- Use `--no-draco` (larger but no compression)
- Export individual components instead of everything
- Check `civitas-glb-manifest.json` for file sizes

## 📊 WHAT TO EXPECT

### File Sizes (Approximate):
- City Arcology: ~200-500 MB
- Sen's Maurader: ~50-100 MB
- The Airport: ~150-300 MB
- Individual ships: ~10-50 MB each
- Cross-sections: ~20-50 MB each

### Export Time:
- Full export: 5-10 minutes on M1/M2 Mac
- Single component: 10-30 seconds
- Animation clips add processing time

## 🎯 RECOMMENDED WORKFLOW

### For Quick Viewing:
1. Export just the city arcology first
2. View in web browser
3. Export Sen's Maurader separately
4. Export The Airport separately

### For Full Animation:
1. Export everything with default settings
2. Load into Blender for full timeline control
3. Use `CIVITAS-PREVIEW-14MIN` for 14-minute preview
4. Export animation as video if needed

### For Sharing:
1. Export specific components you want to show
2. Upload to Sketchfab or similar
3. Share link with others

## 💡 PRO TIPS

### Speed Things Up:
- Use `--skip-existing` to resume interrupted exports
- Export only what you need for viewing
- Close other apps during export

### Quality vs Size:
- Default Draco compression gives good balance
- Use `--no-draco` for maximum quality
- Adjust `--anim-step` for animation resolution

### Understanding the Timeline:
- Frame 0 = Start of canonical week
- Frame 504,000 = Midweek (84 hours)
- Frame 1,008,000 = End of week
- Preview frames = 0-21,000 (14 minutes)

## 📞 NEED HELP?

### Check These Files:
- `out/civitas-glb-manifest.json` - What was exported
- `out/civitas-build-report.json` - Build statistics
- `out/civitas-anchor-manifest.txt` - Coordinate system

### Common Issues:
- **Out of memory**: Export one component at a time
- **Blender crashes**: Check Blender version (need 5.1.1)
- **No animation**: Not all components animate
- **Empty files**: Check source .blend file

## 🎉 ENJOY YOUR CITY!

You now have:
- **84 km × 84 km Base14 city** ready to view
- **Complete fleet** including Sen's Maurader and The Airport
- **168-hour animation** showing the city's weekly cycle
- **Dragon defense systems** with sophisticated lighting
- **AI descriptor** for other models to understand the structure

Start with the city arcology export, then explore individual components. The 14-minute preview gives you a great overview of the animation system!

---
*Generated for Civitas City Base14 Foundation Build - September 7, 2026*