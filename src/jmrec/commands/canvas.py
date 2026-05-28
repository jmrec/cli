import os
import webbrowser
from typing import List, cast

import typer
from canvasapi import Canvas
from canvasapi.course import Course
from dotenv import load_dotenv
from textual import work
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import (
    DataTable,
    Footer,
    Header,
    ListItem,
    ListView,
    LoadingIndicator,
    Static,
)

app = typer.Typer()


def get_canvas():
    """Lazy loader for the Canvas API object."""
    load_dotenv()
    url = os.getenv("CANVAS_API_URL")
    key = os.getenv("CANVAS_API_KEY")

    if not url or not key:
        typer.secho(
            "Missing Canvas Credentials. Ensure CANVAS_API_URL and CANVAS_API_KEY are set.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(1)
    return Canvas(url, key)


class LinkedListItem(ListItem):
    """A ListItem that carries a URL payload."""

    def __init__(self, label: str, url: str):
        super().__init__(Static(label))
        self.url = url


class CourseDetailScreen(Screen):
    """Displays details for a specific course."""

    BINDINGS = [
        ("escape", "app.pop_screen", "Back"),
        ("o", "open_browser", "Open highlighted item in Canvas"),
    ]

    def __init__(self, course: Course):
        super().__init__()
        self.course = course

    def compose(self) -> ComposeResult:
        yield Header()
        yield Horizontal(
            Vertical(
                Static("[bold magenta]Assignments[/bold magenta]", classes="title"),
                LoadingIndicator(id="loading_assign"),
                ListView(id="assignment_list"),
                classes="column",
            ),
            Vertical(
                Static("[bold cyan]Announcements[/bold cyan]", classes="title"),
                LoadingIndicator(id="loading_anno"),
                ListView(id="announcement_list"),
                classes="column",
            ),
        )
        yield Footer()

    def on_mount(self) -> None:
        self.sub_title = f"Details: {getattr(self.course, 'name', 'Unknown')}"
        self.fetch_course_data()

    @work(exclusive=True)
    async def fetch_course_data(self) -> None:
        """Fetch assignments with submission status and grades."""
        assign_list = self.query_one("#assignment_list", ListView)

        assignments = self.course.get_assignments(include=["submission"])

        for a in assignments:
            points_possible = getattr(a, "points_possible", 0)
            submission = getattr(a, "submission", {})
            state = submission.get("workflow_state", "unsubmitted")
            score = submission.get("score")
            percentage = (
                score / points_possible * 100 if score is not None and points_possible > 0 else 0
            )

            if state == "graded":
                color = "green" if percentage > 50 else "orange" if percentage > 0 else "red"
                label = (
                    f"[{color}]{a.name} ({score}/{points_possible} - {percentage:.1f}%)[/{color}]"
                )
            elif state in ["submitted", "pending_review"]:
                label = f"[yellow]{a.name} (Submitted - Pending Grade)[/yellow]"
            else:
                label = f"[dim]{a.name} (Not Submitted - /{points_possible})[/dim]"

            assign_list.append(LinkedListItem(label, a.html_url))

        self.query_one("#loading_assign").remove()

        anno_list = self.query_one("#announcement_list", ListView)
        for d in self.course.get_discussion_topics(only_announcements=True):
            anno_list.append(LinkedListItem(f"[cyan]{d.title}[/cyan]", d.html_url))

        self.query_one("#loading_anno").remove()

    def action_open_browser(self) -> None:
        focused_widget = self.focused
        url = f"{os.getenv('CANVAS_API_URL')}/courses/{self.course.id}"

        if isinstance(focused_widget, ListView):
            item = focused_widget.highlighted_child
            if isinstance(item, LinkedListItem):
                url = item.url

        if not webbrowser.open(url):
            self.app.copy_to_clipboard(url)

            self.notify(
                "Link copied to clipboard.",
                title="Browser not found",
                severity="information",
                timeout=5,
            )


class CourseListScreen(Screen):
    """Main course list including grades."""

    def compose(self) -> ComposeResult:
        yield Header()
        yield DataTable(id="course_table")
        yield Footer()

    def on_mount(self) -> None:
        self.sub_title = "Select a course"
        table = self.query_one(DataTable)
        table.add_columns("ID", "Course Name", "Grade")
        table.cursor_type = "row"

        explorer = cast("CanvasExplorer", self.app)
        for course in explorer.courses:
            grade = "N/A"
            if hasattr(course, "enrollments"):
                for e in course.enrollments:
                    if "computed_current_score" in e and e["computed_current_score"] is not None:
                        grade = f"{e['computed_current_score']}%"

            table.add_row(
                str(course.id),
                getattr(course, "name", "N/A"),
                grade,
                key=str(course.id),
            )

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        key_value = event.row_key.value
        if key_value is None:
            return

        explorer = cast("CanvasExplorer", self.app)
        selected_course = next(c for c in explorer.courses if c.id == int(key_value))
        self.app.push_screen(CourseDetailScreen(selected_course))


class CanvasExplorer(App):
    """The main App controller."""

    CSS = """
    .column {
        width: 50%;
        border: solid $accent;
        padding: 1;
        margin: 1;
    }
    .title {
        text-align: center;
        background: $boost;
        margin-bottom: 1;
    }
    """

    BINDINGS = [("q", "quit", "Quit"), ("r", "refresh", "Refresh")]
    TITLE = "Canvas CLI Explorer"

    def __init__(self, courses: List[Course]):
        super().__init__()
        self.courses = courses

    def on_mount(self) -> None:
        self.push_screen(CourseListScreen())


@app.command()
def explore():
    """
    Open the Canvas Explorer TUI.
    """
    canvas = get_canvas()

    try:
        with typer.progressbar(length=1, label="Connecting to Canvas...") as progress:
            courses = list(canvas.get_courses(enrollment_state="active", include=["total_scores"]))
            progress.update(1)
        CanvasExplorer(courses).run()

    except Exception as e:
        typer.secho(f"❌ Connection Error: {e}", fg="red", err=True)
        raise typer.Exit(1) from e
