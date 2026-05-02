# KB Arena hero — terminal portion. Regenerate with:
#   vhs docs/tapes/hero-demo.tape
# Output: docs/demo.gif (~10s, then optimized with gifsicle).

Output docs/demo.gif

Set FontSize 16
Set Width 1200
Set Height 600
Set Theme "Catppuccin Mocha"
Set Padding 20
Set TypingSpeed 35ms
Set Shell zsh

# Project-local deps so we hit the v0.6.0 wheel we just built
Hide
Type "cd /Users/xavier/Desktop/kb-arena && source .venv/bin/activate && clear"
Enter
Sleep 500ms
Show

# Title beat
Type "# KB Arena — eight retrieval architectures, your docs, one winner"
Sleep 1200ms
Enter
Sleep 600ms

Type "kb-arena --version"
Sleep 400ms
Enter
Sleep 1500ms

# Show the strategy roster live
Type "kb-arena --help 2>&1 | head -25"
Sleep 400ms
Enter
Sleep 2500ms

# Final beat — point at the dashboard
Type "# Run 'kb-arena demo' (zero-config, no API keys) and open localhost:8000/benchmark/"
Sleep 2000ms
Enter
Sleep 1000ms
