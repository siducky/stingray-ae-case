import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def header():
    import marimo as mo

    mo.md(
        """# Data Exploration

        ### Notebook for exploratory data analysis for the Stingray AE case"""
    )
    return


if __name__ == "__main__":
    app.run()
