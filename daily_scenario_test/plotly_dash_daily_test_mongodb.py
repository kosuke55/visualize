import os
from pymongo import MongoClient
import pandas as pd
import dash
from dash import dcc, html, dash_table
import plotly.graph_objs as go
import plotly.express as px
from dash.dependencies import Input, Output


# MongoDB接続設定
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "testDatabase"
COLLECTION_NAME = "testResults"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# Define color theme
color_theme = {
    "background": "rgb(6, 30, 68)",
    "light-background": "rgb(8, 34, 84)",
    "dark-background": "rgb(0, 20, 48)",
    "text": "rgb(196, 205, 213)",
    "title-text": "rgb(255, 255, 255)",
    "grid": "rgb(24, 58, 84)",
    "gray": "rgb(50, 50, 50)",
    "dark-gray": "rgb(20, 20, 20)",
}


def fetch_data():
    data = list(collection.find())
    return pd.DataFrame(data)


def fetch_and_prepare_data_for_datatable():
    all_suites = set()  # すべてのSuiteの名前を保存するセット
    documents = list(collection.find())

    # まずは、存在するすべてのSuiteの名前を収集
    for doc in documents:
        for suite in doc["Suite"]:
            all_suites.add(suite["name"])

    prepared_data = []

    for doc in documents:
        row = {
            "Date": doc["Date"],
            "OK": doc["OK"],
            "NG": doc["NG"],
            "Total": doc["Total"],
            "Success Rate (%)": doc["Success Rate (%)"],
        }

        # すべてのSuiteについて、値が存在するか確認し、存在しない場合はNoneを設定
        for suite_name in all_suites:
            suite_data = next(
                (item for item in doc["Suite"] if item["name"] == suite_name), None
            )
            for key in ["OK", "NG", "Total"]:
                if suite_data and key in suite_data:
                    row[f"{suite_name}_{key}"] = suite_data[key]
                else:
                    row[f"{suite_name}_{key}"] = (
                        None  # 該当するキーがない場合はNoneを設定
                    )

        prepared_data.append(row)

    # 新しいDataFrameを作成
    df_prepared = pd.DataFrame(prepared_data)
    return df_prepared


def create_time_series_plot():
    df = fetch_data()
    plot = go.Figure()
    if df.empty:
        plot.update_layout(title="No data available")
        return plot

    plot.add_trace(
        go.Scatter(
            x=df["Date"],
            y=df["Total"],
            mode="lines+markers",
            name="Total",
            line=dict(color="rgb(50, 205, 50)"),
            fill="tozeroy",
            fillcolor="rgba(50, 205, 50, 0.2)",
        )
    )

    plot.add_trace(
        go.Scatter(
            x=df["Date"],
            y=df["OK"],
            mode="lines+markers",
            name="Success",
            line=dict(color="#00CED1"),
            fill="tozeroy",
            fillcolor="rgba(0, 206, 209, 0.3)",
        )
    )

    plot.add_trace(
        go.Scatter(
            x=df["Date"],
            y=df["NG"],
            mode="lines+markers",
            name="Failure",
            line=dict(color="rgb(255, 100, 14)"),
            fill="tozeroy",
            fillcolor="rgba(255, 100, 14, 0.4)",
        )
    )
    # Update plot layout
    plot.update_layout(
        plot_bgcolor=color_theme["light-background"],
        paper_bgcolor=color_theme["light-background"],
        font_color=color_theme["text"],
        title_font_color=color_theme["text"],
        title="History of Daily Scenario Tests",
        xaxis_title="Date",
        yaxis_title="Count",
        legend_title_text="Scenario",
        xaxis=dict(gridcolor=color_theme["grid"], nticks=20),
        yaxis=dict(gridcolor=color_theme["grid"], nticks=20),
    )
    return plot


def create_pie_chart():
    df = fetch_data()
    if df.empty:
        return px.pie(title="No data available")
    latest_success_rate = df.iloc[-1]["Success Rate (%)"]
    pie_data = {
        "labels": ["Success Rate", "Failure Rate"],
        "values": [latest_success_rate, 100 - latest_success_rate],
    }

    # Create pie chart
    chart = px.pie(
        pie_data,
        values="values",
        names="labels",
        title="Latest Success Rate",
        color_discrete_sequence=["rgb(30, 150, 250)", "rgb(244, 48, 100)"],
    )
    chart.update_traces(hole=0.4)
    chart.update_layout(
        plot_bgcolor=color_theme["light-background"],
        paper_bgcolor=color_theme["light-background"],
        font_color=color_theme["text"],
        title_font_color=color_theme["text"],
    )
    return chart


def create_ng_analysis_plot():
    df = fetch_data()
    fig = go.Figure()
    if df.empty:
        # データが空の場合は空のプロットを返す
        fig.update_layout(title="No data available")
        return fig

    # 'Suite'内の各テスト項目ごとにNGの数を時系列でプロット
    # すべてのテスト項目名を保存するセット
    all_suites = set()
    for index, row in df.iterrows():
        suites = row["Suite"]  # Suiteは辞書のリストとして格納されていると仮定
        for suite in suites:
            all_suites.add(suite["name"])

    # MongoDBのデータ構造に基づいてプロットを追加
    for suite_name in all_suites:
        dates = []
        ng_counts = []
        for index, row in df.iterrows():
            suites = row["Suite"]
            date = row["Date"]
            ng_count = None
            for suite in suites:
                if suite["name"] == suite_name and "NG" in suite:
                    ng_count = suite["NG"]
            if ng_count is not None:
                dates.append(date)  # 日付を追加
                ng_counts.append(ng_count)

        # NGの数を時系列でプロット
        fig.add_trace(
            go.Scatter(x=dates, y=ng_counts, mode="lines+markers", name=suite_name)
        )

    # Update figure layout
    fig.update_layout(
        title="History of NG Scenario Suite",
        xaxis_title="Date",
        yaxis_title="Count",
        plot_bgcolor=color_theme["light-background"],
        paper_bgcolor=color_theme["light-background"],
        font_color=color_theme["text"],
        title_font_color=color_theme["text"],
        legend_title_text="Scenario",
        xaxis=dict(gridcolor=color_theme["grid"], nticks=20),
        yaxis=dict(gridcolor=color_theme["grid"], nticks=20),
    )
    return fig


# External stylesheet for Open Sans font
external_stylesheets = [
    "https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;700&display=swap"
]
# Initialize Dash app with external stylesheet
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# update plots and chart
@app.callback(
    Output("time-series-plot", "figure"), [Input("update-interval", "n_intervals")]
)
def update_time_series_plot(n_intervals):
    return create_time_series_plot()


@app.callback(Output("pie-chart", "figure"), [Input("update-interval", "n_intervals")])
def update_pie_chart(n_intervals):
    return create_pie_chart()


@app.callback(Output("pie-chart2", "figure"), [Input("update-interval", "n_intervals")])
def update_ng_analysis_plot(n_intervals):
    return create_ng_analysis_plot()


@app.callback(
    [Output("datatable-container", "columns"), Output("datatable-container", "data")],
    [Input("update-interval", "n_intervals")],
)
def update_datatable_columns_and_data(n_intervals):
    df_prepared = fetch_and_prepare_data_for_datatable()
    columns = [{"name": i, "id": i} for i in df_prepared.columns]
    data = df_prepared.to_dict("records")
    return columns, data


# Layout of the app
app.layout = html.Div(
    style={
        "backgroundColor": color_theme["background"],
        "color": color_theme["text"],
        "font-family": "Open Sans, sans-serif",
        "font-weight": "400",
        "height": "100vh",
        "display": "flex",
        "flexDirection": "column",
        "padding": "20px",
        "margin-bottom": "30px",
    },
    children=[
        dcc.Interval(id="update-interval", interval=5 * 1000, n_intervals=0),  # 5s
        html.Div(
            style={"padding": "2rem", "flexGrow": 1},
            children=[
                # -- title and other elements remain unchanged --
                # -- first layer --
                html.Div(
                    style={"display": "flex", "flexDirection": "row"},
                    children=[
                        html.Div(
                            dcc.Graph(
                                id="time-series-plot"
                            ),  # Updated: figure attribute removed
                            style={
                                "width": "80%",
                                "padding": "10px",
                                "margin-bottom": "30px",
                            },
                        ),
                        html.Div(
                            style={
                                "width": "20%",
                                "padding": "10px",
                                "margin-bottom": "30px",
                            },
                            children=[
                                dcc.Graph(id="pie-chart")
                            ],  # Updated: figure attribute removed
                        ),
                    ],
                ),
                # -- second layer --
                html.Div(
                    dcc.Graph(id="pie-chart2"),  # Updated: figure attribute removed
                    style={"padding": "10px", "margin-bottom": "30px"},
                ),
                # -- third layer --
                html.Div(
                    dash_table.DataTable(
                        id="datatable-container",
                        columns=[],  # 初期状態ではカラムを空にしておく
                        style_table={
                            "overflowX": "visible",
                            "overflowY": "visible",
                            "width": "100%",
                            "minWidth": "100%",
                            "backgroundColor": color_theme["title-text"],
                        },
                        style_cell={
                            "backgroundColor": color_theme["light-background"],
                            "color": "white",
                        },
                        style_header={
                            "backgroundColor": color_theme["dark-background"],
                            "color": "white",
                        },
                        style_data={"border": "1px solid #183A54"},
                    ),
                ),
            ],
        ),
    ],
)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))
    app.run_server(debug=True, host="0.0.0.0", port=port)
