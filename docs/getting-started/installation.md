# Installation Guide

This guide will walk you through the process of installing Arsla, whether you're a user looking to run programs or a developer interested in contributing.

---

## Prerequisites

Before you begin, ensure you have the following installed on your system:

* **Python 3.8 or higher:** Arsla is developed and tested with Python 3.8+. You can download Python from [python.org](https://www.python.org/downloads/).

---

## Installation via pip (Recommended)

The easiest and recommended way to install Arsla is using `pip`, Python's package installer. It's good practice to install Arsla into a [virtual environment](https://docs.python.org/3/library/venv.html) to avoid conflicts with other Python projects.

1.  **Create a Virtual Environment (Optional but Recommended):**
    Navigate to your project directory (or any preferred location) in your terminal and create a new virtual environment:

    ```bash
    python3 -m venv venv
    ```

2.  **Activate the Virtual Environment:**
    * **On macOS/Linux:**
        ```bash
        source venv/bin/activate
        ```
    * **On Windows (Command Prompt):**
        ```bash
        venv\Scripts\activate.bat
        ```
    * **On Windows (PowerShell):**
        ```bash
        venv\Scripts\Activate.ps1
        ```
    (Your terminal prompt should now show `(venv)` or similar, indicating the virtual environment is active.)

3.  **Install Arsla:**
    With your virtual environment active, install Arsla directly from PyPI:

    ```bash
    pip install arsla-lang
    ```

4.  **Verify Installation:**
    You can check if Arsla is installed correctly by running a simple command:

    ```bash
    arsla --version
    ```
    If successful, this command should print the installed version of Arsla.

---

## Installation from Source (For Developers)

If you plan to contribute to Arsla or want the very latest unreleased features, you can install it directly from its source code.

1.  **Clone the Repository:**
    First, clone the Arsla GitHub repository to your local machine:

    ```bash
    git clone https://github.com/aitzazimtiaz/arsla-lang.git
    ```

2.  **Navigate to the Project Directory:**
    Change your current directory to the newly cloned `arsla-lang` folder:

    ```bash
    cd arsla-lang
    ```

3.  **Create and Activate a Virtual Environment (Recommended):**
    As with `pip` installation, it's best to use a virtual environment:

    ```bash
    python3 -m venv venv
    # Activate:
    # On macOS/Linux: source venv/bin/activate
    # On Windows (Command Prompt): venv\Scripts\activate.bat
    # On Windows (PowerShell): venv\Scripts\Activate.ps1
    ```

4.  **Install Dependencies:**
    Install the project's dependencies from `requirements.txt`:

    ```bash
    pip install -r requirements.txt
    ```

5.  **Install Arsla in Editable Mode:**
    Install Arsla in "editable" mode. This allows you to make changes to the source code, and those changes will be reflected without needing to reinstall:

    ```bash
    pip install -e .
    ```

6.  **Verify Installation:**
    Confirm your installation:

    ```bash
    arsla --version
    ```
    You should see the development version or the version from the `pyproject.toml` file.

---

## Next Steps

With Arsla installed, you're ready to start coding! Proceed to the [Basic Usage](basic-usage.md) guide to learn how to write and run your first Arsla programs.
