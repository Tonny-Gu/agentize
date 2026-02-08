This folder includes the templates for the supported language SDK.
Currently, supported languages are C, C++, and Python.
All the languages share a similar structure and interfaces with some language-specific files and folders.

All the templates have:

- A `Makefile` in the root folder, which defines the following commands:
    - `make setup`: Generates a `setup.sh` script (per-project) to set up environment variables for the SDK.
    - This differs from the agentize repo's `make setup` which generates a cross-project `setup.sh` for `wt` and `agentize` CLI functions.
    - `make env`: Prints environment export statements to stdout. Usage: `eval $(make env)` to set up the environment in the current shell without generating a file.
    - `make env-script`: Generates/regenerates `setup.sh` with current paths using `$(CURDIR)` for proper `make -C` handling.
    - `make build`: Builds the SDK.
    - `make clean`: Cleans all the build files.
    - `make test`: Runs the test cases.
    - `make help`: Displays available targets and usage instructions.

- A `bootstrap.sh` script in the root folder, which initializes the SDK from the template.
    - This makes `make agentize` (see ../Makefile) as simple as copying this script to the target folder and run this script.
    - This script will make necessary modifications to the template files.
    - After it is done, it will delete itself.

