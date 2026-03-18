---
name: console2svg
description: "Convert terminal output into SVG images using console2svg. Use this skill whenever the user wants to capture CLI output as an SVG, create animated terminal recordings, generate terminal screenshots for documentation or READMEs, or produce presentation-ready images of command output. Trigger when the user mentions console2svg, terminal SVG, terminal screenshot, animated terminal recording, or wants to visualize command output as an image. Also trigger when the user is preparing documentation assets, README visuals, or slide content that involves showing terminal sessions."
---

# console2svg — Terminal Output to SVG

Convert terminal output into static or animated SVG images with [console2svg](https://github.com/arika0093/console2svg). Supports truecolor, window chrome, cropping, backgrounds, and animated recordings.

## Installation

```bash
# npm
npm install -g console2svg

# dotnet
dotnet tool install -g ConsoleToSvg
```

Standalone binaries are available on the [releases page](https://github.com/arika0093/console2svg/releases).

## Quick Reference

| Task | Command |
|------|---------|
| Capture piped output | `my-command \| console2svg -o output.svg` |
| Capture a command directly | `console2svg -- git log --oneline` |
| Animated recording | `console2svg -v -c -d macos -- my-command` |
| Set terminal size | `console2svg -w 120 -h 20 -- my-command` |
| macOS window chrome | `console2svg -d macos -- my-command` |
| macOS with shadow | `console2svg -d macos-pc -- my-command` |
| Windows chrome | `console2svg -d windows -- my-command` |
| Output to stdout | `console2svg --stdout -- my-command` |
| Custom output file | `console2svg -o demo.svg -- my-command` |

## Usage Modes

### Pipe Mode

Pipe any command's output. Inherits the current terminal dimensions.

```bash
my-command | console2svg -o output.svg
```

### PTY Command Mode

Run a command inside a pseudo-terminal for accurate capture (preserves colors and formatting):

```bash
console2svg -- git log --oneline
console2svg -w 100 -h 25 -- htop
```

Default width is 100 characters; height is auto-detected.

### Animated Mode (`-v`)

Record command execution as an animated SVG. Use `-c` to show the command being typed and `-d` to add window chrome:

```bash
console2svg -v -c -d macos -- my-command
```

For commands that don't exit on their own, set a timeout:

```bash
console2svg -v -c -d macos --timeout 5 -- nyancat
```

Use `--sleep` to add a pause at the end of the animation before it loops:

```bash
console2svg -v -c -d macos --timeout 5 --sleep 1 -- my-command
```

## Window Chrome Styles (`-d`)

| Style | Description |
|-------|-------------|
| `none` | No frame (default) |
| `transparent` | Text only, no background |
| `macos` | macOS-style title bar with traffic lights |
| `windows` | Windows Terminal style |
| `macos-pc` | macOS with padding and drop shadow |
| `windows-pc` | Windows with padding and drop shadow |

Use `--pc-padding` to adjust padding for the `-pc` styles.

## Appearance

### Background

```bash
# Solid color
console2svg -d macos-pc --background "#003060" --opacity 0.85 -- my-command

# Gradient (two colors)
console2svg -d macos-pc --background "#004060" "#0080c0" -- my-command

# Image
console2svg -d macos-pc --background wallpaper.png --opacity 0.85 -- my-command
```

### Colors and Prompt

```bash
console2svg --forecolor "#00f040" --backcolor "#042515" -- echo "hi"
console2svg --prompt "[DEMO] $" --header "my-app" -- echo "hello"
```

## Cropping

Trim output by pixels, characters, or text patterns:

```bash
# By characters/pixels
console2svg --crop-top 1ch --crop-bottom 2ch -- my-command
console2svg --crop-left 5px --crop-right 30px -- my-command

# By text pattern (crop to first line matching "Host")
console2svg --crop-top "Host" -- dotnet --info
```

## Replay

Save a terminal session for later replay with different settings:

```bash
# Record
console2svg --replay-save ./session.json -- bash

# Replay with different appearance
console2svg -v -c -d macos -w 80 -h 20 --replay ./session.json -- bash
```

## Format Conversion

Convert the SVG output to other formats:

```bash
# To PNG (rsvg-convert)
console2svg --stdout -- my-command | rsvg-convert -o output.png

# To PNG (ImageMagick)
console2svg --stdout -- my-command | magick - output.png
```

## CLI Options

| Option | Purpose |
|--------|---------|
| `-o` | Output file path (default: `output.svg`) |
| `-w` | Terminal width in characters |
| `-h` | Terminal height in lines |
| `-v` | Animated/video mode |
| `-c` | Show the command being typed |
| `-d` | Window chrome style |
| `--background` | Background color, gradient, or image |
| `--opacity` | Background opacity |
| `--forecolor` | Text color override |
| `--backcolor` | Terminal background color override |
| `--header` | Custom title bar text |
| `--prompt` | Custom prompt string |
| `--crop-top/bottom/left/right` | Crop by px, ch, or text pattern |
| `--timeout` | Auto-exit after N seconds |
| `--sleep` | Pause at end of animation |
| `--stdout` | Write SVG to stdout instead of file |
| `--replay-save` | Save session for replay |
| `--replay` | Replay a saved session |
| `--verbose` | Enable detailed logging |

## Tips

- Use `-d macos-pc` or `-d windows-pc` for presentation-ready output with shadows — these look great in slides and READMEs.
- Combine `-v -c` for animated recordings that show the command being typed — effective for tutorials and demos.
- Pipe to `--stdout` and convert with `rsvg-convert` or `magick` when a PNG is needed.
- In CI, console2svg auto-sets `TERM=xterm-256color`, `COLORTERM=truecolor`, and `FORCE_COLOR=3` to preserve colors. Disable with `--no-colorenv`.
- The animated SVG output uses an opacity-based flipbook technique (not translateX film strips), which renders efficiently across all browsers including Safari.
