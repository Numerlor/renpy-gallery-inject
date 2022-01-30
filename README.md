Patch existing Ren'Py games with a replay gallery by modifying their code at runtime, no source code modification is odne.

Configuration of the screens and replays is done in `config_.rpy`.


Patching jump labels and end replay statements is showcased in `label_patching.rpy` using function from `ast_utils.py`.

Adding the files from the `resources` directory into a default game should showcase this project in a basic setup.
