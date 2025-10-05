from flask import Flask, render_template, jsonify
import pandas as pd
import os

app = Flask(__name__)

# Helper to load multiple CSVs
def load_multiple_csv(files):
    dfs = []
    for f in files:
        if os.path.exists(f):
            df = pd.read_csv(f)
            # Strip spaces from column names and values
            df.columns = df.columns.str.strip()
            df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
            dfs.append(df)
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

# Datasets and their respective files
DATASETS = {
    "virus": load_multiple_csv(["viruses_shared_behaviors_100_plus_complete.csv"]),
    "bacteria": load_multiple_csv(["bacteria_shared_behaviors_120.csv"]),
    "fungi": load_multiple_csv(["fungi_shared_behaviors_120.csv"]),
    "others": load_multiple_csv(["others_shared_behaviors_120_plus.csv"])
}

# Mapping category → main organism column name
COLUMN_MAP = {
    "virus": "Virus",
    "bacteria": "Bacterium",
    "fungi": "Fungus",
    "others": "Pathogen"
}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/get_pathogens/<category>")
def get_pathogens(category):
    """Return pathogen names for a selected category."""
    if category not in DATASETS:
        return jsonify({"error": "Invalid category"}), 400

    df = DATASETS[category]
    col = COLUMN_MAP.get(category)

    if col not in df.columns:
        return jsonify({"error": f"Column '{col}' not found in dataset"}), 400

    pathogens = sorted(df[col].dropna().unique().tolist())
    return jsonify({"pathogens": pathogens})

@app.route("/get_details/<category>/<pathogen>")
def get_details(category, pathogen):
    """Return full details for a selected pathogen."""
    if category not in DATASETS:
        return jsonify({"error": "Invalid category"}), 400

    df = DATASETS[category]
    col = COLUMN_MAP.get(category)

    if col not in df.columns:
        return jsonify({"error": f"Column '{col}' not found in dataset"}), 400

    # Normalize both for comparison
    df[col] = df[col].astype(str).str.strip().str.lower()
    pathogen_clean = pathogen.strip().lower()

    row = df[df[col] == pathogen_clean]

    if row.empty:
        return jsonify({"error": f"No match found for '{pathogen}' in {category} dataset."}), 404

    # Clean up record and replace missing or blank fields
    details = row.iloc[0].to_dict()
    clean_details = {}
    for key, value in details.items():
        if pd.isna(value) or str(value).strip() == "":
            clean_details[key] = "N/A"
        else:
            clean_details[key] = str(value).strip()

    return jsonify(clean_details)

if __name__ == "__main__":
    app.run(debug=True)
