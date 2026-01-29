import os
from pathlib import Path

import click
from hapless import Hapless, Status


@click.group()
def main():
    pass


@main.command()
@click.argument("workflow", type=click.Path(path_type=Path))
def run(workflow: Path):
    project_dir = Path.cwd().absolute()
    workspace_dir = project_dir / "workspace"

    hapless = Hapless(hapless_dir=workspace_dir / ".hapless")

    existing_runs = [int(d.name) for d in (workspace_dir / workflow.name).iterdir() if d.is_dir() and d.name.isdigit()]
    new_run_id = max(existing_runs, default=0) + 1

    workflow_name = f"hf-{workflow.name}-{new_run_id}"

    hap = hapless.create_hap(
        cmd=f"hap-flow execute-workflow {workspace_dir} {workflow} {new_run_id}",
        name=workflow_name,
        redirect_stderr=True,
    )

    click.echo(f"Executing workflow: {workflow.name} [ hap: {hap} ]")
    hapless.run_hap(hap, blocking=True)

    hapless.logs(hap, follow=True)


@main.command()
@click.argument("workspace", type=click.Path(path_type=Path))
@click.argument("workflow", type=click.Path(path_type=Path))
@click.argument("run_id")
def execute_workflow(workspace: Path, workflow: Path, run_id: str):
    click.echo("Starting workflow")

    workdir = workspace / workflow.name / run_id
    workdir.mkdir(parents=True, exist_ok=True)

    if workflow.is_dir():
        tasks = [f for f in workflow.iterdir() if f.is_file() and os.access(f, os.X_OK)]
    else:
        tasks = [workflow]

    hapless = Hapless(hapless_dir=workspace / ".hapless")

    for task in tasks:
        task_name = f"hf-{workflow.name}-{run_id}-{task.name}"

        if hap := hapless.get_hap(task_name):
            if hap.status == Status.SUCCESS:
                click.echo(f"Skipping task {task.name} [ hap: {hap} ]")
                continue

        hap = hapless.create_hap(
            cmd=str(task.absolute()),
            workdir=workdir.absolute(),
            name=task_name,
            redirect_stderr=True,
        )

        click.echo(f"Executing task: {task.name} [ hap: {hap} ]")
        hapless.run_hap(hap, blocking=True)

        hap = hapless.get_hap(task_name)
        assert hap is not None

        hapless.logs(hap)

        if hap.status != Status.SUCCESS:
            click.echo(f"Task failed: {task.name} [ hap: {hap} ]")
            return

        if hap.status == Status.SUCCESS:
            click.echo(f"Task finished: {task.name} [ hap: {hap} ]")

    click.echo("Workflow finished")
