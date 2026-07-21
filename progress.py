from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn, TimeRemainingColumn

class DubbingProgress:
    """
    Wrapper around rich.Progress to manage distinct stages of the dubbing pipeline.
    Provides a beautiful, structured CLI progress experience.
    """
    def __init__(self):
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}", justify="left"),
            BarColumn(),
            TaskProgressColumn(),
            "•",
            TimeElapsedColumn(),
            "•",
            TimeRemainingColumn(),
        )
        self.tasks = {}

    def start(self):
        self.progress.start()

    def stop(self):
        self.progress.stop()

    def add_stage(self, stage_name: str, total: float = 100.0) -> int:
        """Adds a new stage to track."""
        task_id = self.progress.add_task(f"[yellow]{stage_name}", total=total, start=False)
        self.tasks[stage_name] = task_id
        return task_id

    def start_stage(self, stage_name: str):
        """Starts a previously added stage."""
        if stage_name in self.tasks:
            self.progress.start_task(self.tasks[stage_name])

    def update_stage(self, stage_name: str, advance: float = 0, completed: float = None, description: str = None):
        """Updates progress of a specific stage."""
        if stage_name in self.tasks:
            task_id = self.tasks[stage_name]
            kwargs = {}
            if advance > 0:
                kwargs["advance"] = advance
            if completed is not None:
                kwargs["completed"] = completed
            if description:
                kwargs["description"] = f"[bold blue]{description}"
            self.progress.update(task_id, **kwargs)

    def complete_stage(self, stage_name: str):
        """Marks a stage as 100% completed."""
        if stage_name in self.tasks:
            task_id = self.tasks[stage_name]
            # Get the description of the task
            task = next(t for t in self.progress.tasks if t.id == task_id)
            desc = task.description.replace("[yellow]", "[green]").replace("[bold blue]", "[bold green]")
            if not desc.startswith("[green]"):
               desc = f"[green]✓ {desc}"
            self.progress.update(task_id, completed=task.total, description=desc)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
