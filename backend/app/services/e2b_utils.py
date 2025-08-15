from rich.console import Console
from rich.traceback import Traceback
from rich.theme import Theme
from rich.syntax import Syntax
from rich.panel import Panel
from datetime import datetime
from e2b_code_interpreter import Sandbox
from typing import Optional, Dict

custom_theme = Theme(
    {
        "info": "cyan",
        "success": "green",
        "warning": "yellow",
        "error": "bold red",
        "header": "magenta",
        "bold": "bold",
        "dim": "dim",
    }
)
console = Console(theme=custom_theme)


def _format_timestamp():
    return datetime.now().strftime("%H:%M:%S")


class E2BPythonInterpreter:
    """A simple Python interpreter for executing code in a sandboxed environment."""

    def __init__(
        self,
        sandbox: Optional[Sandbox] = None,
        template: Optional[str] = None,
        sandbox_id: Optional[str] = None,
        **kwargs: Dict,
    ):
        self.sandbox = (
            sandbox
            if sandbox
            else Sandbox(template=template, sandbox_id=sandbox_id, **kwargs)
        )
        self.template = template
        self.sandbox_id = sandbox_id
        self.sandbox_kwargs = kwargs

    def _prepare_sandbox(self) -> None:
        """Prepare the sandbox for running code."""
        if self.sandbox is None:
            console.print(
                "No sandbox instance provided. Creating a new sandbox.", style="warning"
            )
            self.sandbox = Sandbox(
                template=self.template,
                sandbox_id=self.sandbox_id,
                **self.sandbox_kwargs,
            )

        if not self.sandbox.is_running():
            console.print(
                "The sandbox was not running. Restarting the sandbox.", style="warning"
            )
            self.sandbox = Sandbox(
                template=self.template,
                sandbox_id=self.sandbox_id,
                **self.sandbox_kwargs,
            )

    def run_code(self, code, show_code=True):
        """Execute Python code inside the e2b Sandbox with pretty, IPython-like output.

        Args:
            code (str): Python source code to execute.
            sandbox (Sandbox|None): Optional existing sandbox instance.
            show_code (bool): Echo the code block before execution.
        Returns:
            list[str] | [] | None: Captured stdout lines, empty list if none, or None on error.
        """
        self._prepare_sandbox()

        if show_code:
            header = f"In  [ ]  { _format_timestamp() }"
            console.print(header, style="bold")
            console.print(
                Panel.fit(
                    Syntax(code, "python", theme="monokai", line_numbers=False),
                    title="Code",
                    border_style="header",
                )
            )

        res = self.sandbox.run_code(code)
        exception = res.error

        if exception:
            console.print(f"Out [ ]:", style="error")
            try:
                console.print(
                    Traceback.from_exception(
                        type(exception), exception, exception.__traceback__
                    ),
                    style="error",
                )
            except Exception:
                console.print(f"{exception}", style="error")
            return None

        stdouts = res.logs.stdout
        execution_count = res.execution_count

        if stdouts:
            num_outs = len(stdouts)
            if num_outs > 1:
                console.print(
                    f"Out[{execution_count}]: {num_outs} outputs", style="info"
                )
                for i, stdout in enumerate(stdouts):
                    prefix = f"[{execution_count}] Out {i + 1}:"
                    console.print(prefix, style="bold", end=" ")
                    console.print(stdout.rstrip(), style="success")
            else:
                content = stdouts[0].rstrip()
                console.print(f"Out[{execution_count}]:", style="bold", end=" ")
                console.print(content, style="success")
        else:
            console.print(f"Out[{execution_count}]: <no output>", style="warning")
        return stdouts if stdouts else []

    def show_files(self):
        """Display the files in the sandbox."""
        files = self.sandbox.list_files()
        if not files:
            console.print("No files in the sandbox.", style="warning")
            return

        console.print("Files in the sandbox:", style="header")
        for file in files:
            console.print(f"- {file}", style="info")

    def kill(self):
        """Terminate the sandbox."""
        if self.sandbox.is_running():
            self.sandbox.kill()
            console.print("Sandbox terminated.", style="success")
        else:
            console.print("Sandbox was not running.", style="warning")

    def __del__(self):
        self.kill()

    def __enter__(self):
        """Enter the context manager."""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Exit the context manager."""
        self.kill()
        if exc_type is not None:
            console.print(f"An exception occurred: {exc_value}", style="error")
        return False

    def __repr__(self):
        return f"E2BPythonInterpreter(sandbox={self.sandbox})"
