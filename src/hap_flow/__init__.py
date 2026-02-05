import os
import subprocess
from pathlib import Path

import click
from hapless import Hapless, Status
from hapless.formatters import TableFormatter


@click.group()
def main():
    pass


@main.command()
@click.argument("workflow", type=click.Path(path_type=Path))
@click.option("--here", is_flag=True)
def run(workflow: Path, here: bool):
    project_dir = Path.cwd().absolute()
    workspace_dir = project_dir / "workspace"

    existing_runs = (
        [int(d.name) for d in (workspace_dir / workflow.name).iterdir() if d.is_dir() and d.name.isdigit()]
        if (workspace_dir / workflow.name).exists()
        else []
    )
    run_id = str(max(existing_runs, default=0) + 1)

    if here:
        workdir = project_dir
    else:
        run_dir = workspace_dir / workflow.name / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        _link_latest(run_dir)
        workdir = run_dir

    workflow_name = f"hf-w-{workflow.name}-{run_id}"

    hapless = Hapless()

    hap = hapless.create_hap(
        cmd=f"hap-flow workflow {workflow.absolute()}",
        name=workflow_name,
        redirect_stderr=True,
        workdir=workdir,
        env={
            **os.environ,
            "HF_PROJECT_DIR": str(project_dir),
            "HF_RUN_ID": run_id,
            "HF_WORKFLOW_NAME": workflow_name,
        },
    )

    hapless.run_hap(hap, check=True)
    hapless.show(hap, formatter=TableFormatter())
    subprocess.run(["tail", "-f", "+1", hap.stderr_path])


@main.command()
@click.argument("workflow", type=click.Path(path_type=Path))
def workflow(workflow: Path):
    run_id = os.environ["HF_RUN_ID"]
    workflow_name = os.environ["HF_WORKFLOW_NAME"]

    click.echo(f"Starting workflow: {workflow.name} ({workflow_name})")

    if workflow.is_dir():
        tasks = [f for f in workflow.iterdir() if f.is_file() and os.access(f, os.X_OK)]
    else:
        tasks = [workflow]

    hapless = Hapless()

    for task in tasks:
        task_name = f"hf-t-{workflow.name}-{run_id}-{task.name}"

        if hap := hapless.get_hap(task_name):
            if hap.status == Status.SUCCESS:
                click.echo(f"Skipping task {task.name} [ hap: {hap} ]")
                continue

        hap = hapless.create_hap(
            cmd=str(task.absolute()),
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


def _link_latest(workdir: Path):
    latest = workdir.parent / "latest"

    if latest.exists() and not latest.is_symlink():
        return

    latest.unlink(missing_ok=True)
    latest.symlink_to(workdir, target_is_directory=True)
