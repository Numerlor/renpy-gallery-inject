The `gallery` package is a self contained gallery screen, and code to allow the screen and functionality to be patched
into existing games without changing their code in any way.
Configuration for the gallery is done in the `config_.rpy` file, example of patching in replay jump points can be found in `label_patching.rpy`.

The default gallery configuration which serves as an example its functionality works with the script and images in `renpy-gallery-inject-resources` directory.

The `script_jump` provides a log screen and utilities for tracing the execution of the game as it's running.
The currently executing node (usually single line) is highlighted, branching can be further explored:
![example of screen window](https://i.imgur.com/IJmI14n.png)

Arbitrary nodes in the log screen can be jumped to by left clicking them, or a line for finding the node for replay patching copied to the clipboard with the right click.
`script_jump` depends on resources in `renpy-gallery-inject-resources`.
