import os
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
def execute_workflow(workspace: Path, workflow: Path, run_id: str):
    workdir = workspace / workflow.name / run_id
    workdir.mkdir(parents=True, exist_ok=True)

    if workflow.is_dir():
        tasks = [f for f in workflow.iterdir() if f.is_file() and os.access(f, os.X_OK)]
    else:
        tasks = [workflow]

    hapless = Hapless(hapless_dir=workspace / ".hapless")

    # Get the project directory (current working directory where hap-flow was invoked)
    project_dir = Path.cwd().absolute()

    for task in tasks:
        task_name = f"hf-{workflow.name}-{run_id}-{task.name}"

        if hap := hapless.get_hap(task_name):
            if hap.status == Status.SUCCESS:
                click.echo(f"Skipping task {task.name} [ hap: {hap} ]")
                continue

        click.echo(f"Executing task: {task.name}")
        hapless.run_command(
            cmd=str(task.absolute()),
            env={"HAP_FLOW_PROJECT_DIR": str(project_dir)},
            workdir=workdir.absolute(),
            name=task_name,
            redirect_stderr=True,
            blocking=True,
        )

        hap = hapless.get_hap(task_name)
        assert hap is not None

        hapless.logs(hap)

        if hap.status != Status.SUCCESS:
            click.echo(f"Task failed: {task.name} [ hap: {hap} ]")
            return

        if hap.status == Status.SUCCESS:
            click.echo(f"Task finished: {task.name} [ hap: {hap} ]")
