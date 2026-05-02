# Retriever Lab CLI walkthrough — regenerate with:
#   vhs docs/tapes/retriever-lab.tape
# Output: docs/demo-retriever-lab-cli.gif

Output docs/demo-retriever-lab-cli.gif

Set FontSize 16
Set Width 1280
Set Height 720
Set Theme "Catppuccin Mocha"
Set Padding 20
Set TypingSpeed 35ms
Set Shell zsh

Hide
Type "cd /Users/xavier/Desktop/kb-arena && source .venv/bin/activate && clear"
Enter
Sleep 500ms
Show

# Show what label-chunks does at the help level — actually running it
# requires API credit, which we don't burn during a recording.
Type "kb-arena label-chunks --help"
Sleep 400ms
Enter
Sleep 2500ms

Type "kb-arena retriever-lab --help"
Sleep 400ms
Enter
Sleep 2500ms

# Tease the metric output by inspecting an existing run
Type "ls results/run_* 2>/dev/null | head -3"
Sleep 400ms
Enter
Sleep 2000ms

Type "# 'kb-arena retriever-lab --corpus aws-compute' streams a live Recall@k / NDCG@k table per strategy"
Sleep 1500ms
Enter
