import os
import subprocess
from pathlib import Path

import click
from hapless import Hapless, Status
from hapless.formatters import TableFormatter
from rich.padding import Padding


@click.group()
def main():
    pass


@main.command()
@click.argument("workflow", type=click.Path(path_type=Path))
@click.option("--here", is_flag=True)
def run(workflow: Path, here: bool):
    project_dir = Path.cwd().absolute()
    workspace_dir = project_dir / "workspace"

    hapless = Hapless()

    previous_runs = []
    for hap in hapless.get_haps():
        if hap.name.startswith(f"hf-w-{workflow.name}-") and hap.env and "HF_RUN_ID" in hap.env:
            previous_runs.append(int(hap.env["HF_RUN_ID"]))
    run_id = str(max(previous_runs, default=0) + 1)

    if here:
        workdir = project_dir
    else:
        run_dir = workspace_dir / workflow.name / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        _link_latest(run_dir)
        workdir = run_dir

    workflow_name = f"hf-w-{workflow.name}-{run_id}"

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
    subprocess.run(["tail", "-n", "+1", "-f", str(hap.stderr_path)])


@main.command()
@click.argument("workflow", type=click.Path(path_type=Path))
def workflow(workflow: Path):
    run_id = os.environ["HF_RUN_ID"]

    hapless = Hapless()

    hapless.ui.print()
    hapless.ui.console.rule(rf"WORKFLOW \[{workflow.name}]", align="left", characters="*")

    if workflow.is_dir():
        tasks = [f for f in workflow.iterdir() if f.is_file() and os.access(f, os.X_OK)]
    else:
        tasks = [workflow]

    for task in sorted(tasks):
        task_name = f"hf-t-{workflow.name}-{run_id}-{task.name}"

        if hap := hapless.get_hap(task_name):
            if hap.status == Status.SUCCESS:
                click.echo(f"Skipping task {task.name}")
                continue

        hap = hapless.create_hap(
            cmd=str(task.absolute()),
            name=task_name,
            redirect_stderr=True,
        )

        hapless.ui.print()
        hapless.ui.console.rule(rf"TASK \[{task.name}]", align="left", characters="*")
        hapless.run_hap(hap, blocking=True)

        hap = hapless.get_hap(task_name)
        assert hap is not None

        hapless.logs(hap)

        if hap.status != Status.SUCCESS:
            hapless.ui.print(rf"TASK FAILED \[{task.name}]")
            return

    click.echo("Workflow finished")


def _link_latest(workdir: Path):
    latest = workdir.parent / "latest"

    if latest.exists() and not latest.is_symlink():
        return

    latest.unlink(missing_ok=True)
    latest.symlink_to(workdir, target_is_directory=True)
