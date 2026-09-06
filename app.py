"""Shiny for Python app to explore the Alone TV show contestant data."""

from pathlib import Path

import polars as pl
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_histogram,
    ggplot,
    labs,
    scale_fill_manual,
    theme,
    theme_minimal,
)
from shiny import App, reactive, render, ui

APP_DIR = Path(__file__).parent
CSV_PATH = APP_DIR / "data" / "alone-contestants.csv"
CSS_PATH = APP_DIR / "styles.css"

# Palette shared by the CSS theme and the plots.
INK = "#0f1514"
TERRACOTTA = "#c5654f"
TEAL = "#5f9e94"
TEXT = "#d8d5cf"
TEXT_FAINT = "#5f5d58"
HAIRLINE = "#1e2624"

# Ordered ramp used for discrete fills (terracotta -> sand -> teal).
CATEGORY_COLORS = [
    "#c5654f",
    "#d18a6a",
    "#dcae88",
    "#c9b394",
    "#a8ae9c",
    "#87a89f",
    "#5f9e94",
    "#4f8a86",
    "#437471",
    "#3a5f5f",
    "#8a5a4b",
    "#a3705c",
]

COLOR_CHOICES = {
    "None": None,
    "Season": "Season",
    "Gender": "Gender",
    "Status": "Status",
}

CONTESTANTS = pl.read_csv(CSV_PATH)

SEASONS = sorted(CONTESTANTS.get_column("Season").unique().to_list())
GENDERS = sorted(CONTESTANTS.get_column("Gender").unique().to_list())
STATUSES = sorted(CONTESTANTS.get_column("Status").unique().to_list())
AGE_MIN, AGE_MAX = (
    CONTESTANTS.get_column("Age").min(),
    CONTESTANTS.get_column("Age").max(),
)
DAYS_MIN, DAYS_MAX = (
    CONTESTANTS.get_column("Days Lasted").min(),
    CONTESTANTS.get_column("Days Lasted").max(),
)


def plot_theme() -> theme:
    """Dark, hairline-and-monospace theme matching the app chrome."""
    return theme_minimal() + theme(
        figure_size=(9, 4.5),
        plot_background=element_rect(fill=INK, color=INK),
        panel_background=element_rect(fill=INK, color=INK),
        panel_grid_major_y=element_line(color=HAIRLINE, size=0.5),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        axis_text=element_text(color=TEXT_FAINT, size=8, family="monospace"),
        axis_title=element_text(color=TEXT_FAINT, size=8, family="monospace"),
        axis_title_x=element_text(margin={"t": 10}),
        axis_title_y=element_text(margin={"r": 10}),
        legend_background=element_rect(fill=INK, color=INK),
        legend_key=element_rect(fill=INK, color=INK),
        legend_text=element_text(color=TEXT, size=8, family="monospace"),
        legend_title=element_text(color=TEXT_FAINT, size=8, family="monospace"),
    )


def stat(label: str, value: str, note: str = "", tone: str = "") -> ui.Tag:
    """One cell in the readout strip above the plot."""
    return ui.div(
        ui.div(label, class_="stat-label"),
        ui.div(value, class_=f"stat-value {tone}".strip()),
        ui.div(note, class_="stat-note"),
        class_="stat",
    )


app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.input_select(
            "color_by",
            "Break down by",
            choices=list(COLOR_CHOICES.keys()),
            selected="None",
        ),
        ui.input_checkbox_group("gender", "Gender", choices=GENDERS, selected=GENDERS),
        ui.input_checkbox_group(
            "status", "Status", choices=STATUSES, selected=STATUSES
        ),
        ui.input_slider(
            "age", "Age", min=AGE_MIN, max=AGE_MAX, value=[AGE_MIN, AGE_MAX]
        ),
        ui.input_slider(
            "days",
            "Days Lasted",
            min=DAYS_MIN,
            max=DAYS_MAX,
            value=[DAYS_MIN, DAYS_MAX],
        ),
        ui.input_radio_buttons(
            "season",
            "Season",
            choices=[str(s) for s in SEASONS],
            # "" matches no choice, so nothing is checked to start, which
            # means every season is shown.
            selected="",
            inline=True,
        ),
        ui.input_action_link("clear_seasons", "show all seasons"),
        title="Filters",
        width=290,
    ),
    ui.head_content(
        ui.tags.link(rel="preconnect", href="https://fonts.googleapis.com"),
        ui.tags.link(
            rel="stylesheet",
            href=(
                "https://fonts.googleapis.com/css2"
                "?family=Inter:wght@200;300;400;600"
                "&family=JetBrains+Mono:wght@300;400&display=swap"
            ),
        ),
        ui.tags.style(CSS_PATH.read_text()),
    ),
    ui.p(
        "Twelve seasons alone. Ten items each. ",
        ui.em("Nobody is coming to help."),
        class_="lede",
    ),
    ui.output_ui("stat_strip"),
    ui.card(
        ui.card_header("Days lasted — distribution"),
        ui.output_plot("days_histogram"),
    ),
    ui.card(
        ui.card_header("Contestant log"),
        ui.output_data_frame("contestants_table"),
        ui.card_footer(ui.output_text("row_count")),
    ),
    title="Alone",
    fillable=True,
)


def server(input, output, session):
    @reactive.calc
    def filtered_data() -> pl.DataFrame:
        season = input.season()
        # No season checked means no season filter at all.
        seasons_selected = SEASONS if not season else [int(season)]
        return CONTESTANTS.filter(
            pl.col("Season").is_in(seasons_selected),
            pl.col("Gender").is_in(input.gender()),
            pl.col("Status").is_in(input.status()),
            pl.col("Age").is_between(input.age()[0], input.age()[1]),
            pl.col("Days Lasted").is_between(input.days()[0], input.days()[1]),
        ).sort("Season", "Days Lasted")

    @reactive.effect
    @reactive.event(input.clear_seasons)
    def _clear_seasons():
        ui.update_radio_buttons("season", selected="")

    @render.ui
    def stat_strip():
        data = filtered_data()
        n = data.height

        if n == 0:
            return ui.div(
                stat("Contestants", "0", "no rows match these filters"),
                class_="stat-strip",
            )

        days = data.get_column("Days Lasted")
        longest = data.sort("Days Lasted", descending=True).row(0, named=True)
        winners = data.filter(pl.col("Status") == "Winner").height

        return ui.div(
            stat("Contestants", f"{n}", f"of {CONTESTANTS.height} on record"),
            stat("Median days", f"{days.median():.0f}", "half made it this far"),
            stat(
                "Longest run",
                f"{longest['Days Lasted']:.0f}",
                f"{longest['Name']} · S{longest['Season']}",
                tone="cool",
            ),
            stat("Winners", f"{winners}", "last one standing", tone="accent"),
            stat("Median age", f"{data.get_column('Age').median():.0f}", "years"),
            class_="stat-strip",
        )

    @render.plot
    def days_histogram():
        color_column = COLOR_CHOICES[input.color_by()]
        data = filtered_data()

        if data.height == 0:
            return (
                ggplot(pl.DataFrame({"Days Lasted": []}), aes(x="Days Lasted"))
                + labs(x="DAYS LASTED", y="CONTESTANTS", title="No rows match")
                + plot_theme()
                + theme(plot_title=element_text(color=TEXT_FAINT, size=9))
            )

        if color_column is None:
            plot = ggplot(data, aes(x="Days Lasted")) + geom_histogram(
                binwidth=10, boundary=0, fill=TERRACOTTA, color=INK, size=0.7
            )
        else:
            # Cast to string so numeric columns like Season are treated as
            # discrete groups rather than a continuous color gradient.
            data = data.with_columns(pl.col(color_column).cast(pl.String))
            levels = sorted(data.get_column(color_column).unique().to_list())
            palette = [
                CATEGORY_COLORS[i % len(CATEGORY_COLORS)] for i in range(len(levels))
            ]
            plot = (
                ggplot(data, aes(x="Days Lasted", fill=color_column))
                + geom_histogram(binwidth=5, boundary=0, color=INK, size=0.5)
                + scale_fill_manual(values=palette)
            )

        return (
            plot
            + labs(x="DAYS LASTED", y="CONTESTANTS", fill=input.color_by().upper())
            + plot_theme()
        )

    @render.text
    def row_count():
        return f"{filtered_data().height} rows shown"

    @render.data_frame
    def contestants_table():
        return render.DataGrid(
            filtered_data().select(
                "Season",
                "Name",
                "Gender",
                "Country",
                "Days Lasted",
                "Reason / Outcome",
                "Status",
            ),
            filters=False,
        )


app = App(app_ui, server)
