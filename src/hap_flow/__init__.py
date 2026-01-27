from pathlib import Path

import click
from hapless import Hapless, Status


@click.group()
def main():
    pass


@main.command()
@click.argument("workspace", type=click.Path(path_type=Path))
@click.argument("workflow", type=click.Path(path_type=Path))
@click.argument("run_id")
def run(workspace: Path, workflow: Path, run_id: str):
    workdir = workspace / workflow.name / run_id
    workdir.mkdir(parents=True, exist_ok=True)

    task = workflow  # single file workflow

    hapless = Hapless(hapless_dir=workspace / ".hapless")

    task_name = f"hf-{workflow.name}-{run_id}-{task.name}"

    if hap := hapless.get_hap(task_name):
        # if hap.status == Status.SUCCESS:
        #     return

        hapless.run_command(
            cmd=str(workflow.absolute()),
            workdir=workdir.absolute(),
            name=task_name,
            redirect_stderr=True,
            blocking=True,
        )
