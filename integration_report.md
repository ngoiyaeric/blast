# Integration Report: Replacing the Frontend with QCX

This document summarizes the process of replacing the existing frontend with the QCX (Quality Computer Experiences) application from the `https://github.com/queuelab/qcx` repository.

## Changes Made

The following changes were made to integrate the new frontend:

1.  **Replaced the Frontend Application:** The `blastai/frontend` directory was removed and replaced with a clone of the `qcx` repository.

2.  **Updated Startup Scripts:** The `blastai/cli_frontend.py` script was modified to use `bun` instead of `npm` for installing dependencies and starting the frontend server. This was necessary because the `qcx` application uses `bun` as its package manager. A new function, `check_bun_installation`, was added to `blastai/cli_installation.py` to check for the presence of `bun`.

3.  **Configured Backend Connection:** The `qcx` application uses the Vercel AI SDK to communicate with the backend. The `blastai/frontend/lib/utils/index.ts` file was modified to configure the AI SDK to use the BLAST backend. The following changes were made:
    *   The `baseURL` was set to `http://localhost:${process.env.NEXT_PUBLIC_SERVER_PORT}`.
    *   The `apiKey` was set to `"not-needed"`.
    *   The model name was set to `"blast-default"`.

## Recommendations

*   **Python Dependency Management:** The project is missing a `requirements.txt` or a `pyproject.toml` file for managing Python dependencies. This makes the setup process difficult and error-prone. I recommend creating one of these files to ensure a consistent and reliable development environment.

## Errors Encountered

During the verification process, I encountered a series of `ModuleNotFoundError`s for the following Python packages:

*   `pydantic`
*   `yaml`
*   `browser_use`

I have been installing these dependencies one by one. The `browser_use` package is a local package that I installed in editable mode using `pip install -e ./browser-use`.

The integration is not yet fully verified due to these dependency issues. Once all the dependencies are installed, the application should be tested to ensure that the new frontend communicates correctly with the backend.
