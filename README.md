The `gallery` package is a self contained gallery screen, and code to allow the screen and functionality to be patched
into existing games without changing their code in any way.
Configuration for the gallery is done in the `config_.rpy` file, example of patching in replay jump points can be found in `label_patching.rpy`.

The default gallery configuration which serves as an example its functionality works with the script and images in `renpy-gallery-inject-resources` directory.

The `script_jump` provides a log screen and utilities for tracing the execution of the game as it's running.
The currently executing node (usually single line) is highlighted, branching can be further explored:
![example of screen window](https://i.imgur.com/IJmI14n.png)

The leftmost button parses all the reachable (non branching) lines from the current executing point, and creates a new log from them.
The logs are paginated to prevent them from slowing down the game considerably; the arrows can be used to navigate the pages.
The hamburger menu display all the logs that are currently kept.
Clicking on the road fork at the end of an entry's creates new logs for all of the branches of that entry, and allows you to use them as the current log.

Arbitrary nodes in the log screen can be jumped to by left clicking them, or a line for finding the node for replay patching copied to the clipboard with the right click.
`script_jump` depends on resources in `renpy-gallery-inject-resources`.
