# %%

import pandas as pd
from tqdm import tqdm

import os

file_path = os.getcwd()  # + "/data/"

df_class_values_upper = pd.read_excel(
    f"{file_path}/class_values.xlsx",
    index_col=0,
    sheet_name="UPPER",
)
df_class_values_lower = pd.read_excel(
    f"{file_path}/class_values.xlsx",
    index_col=0,
    sheet_name="LOWER",
)
df_class_values_screw = (
    pd.read_excel(
        f"{file_path}/class_values.xlsx",
        sheet_name="SCREW",
    )
    .drop_duplicates()
    .set_index("upper_workpiece_id", drop=True)
)


df_merged = df_class_values_upper.join(
    df_class_values_lower,
    how="outer",
    lsuffix="_upper",
    rsuffix="_lower",
)


df_merged = df_merged.join(df_class_values_screw, how="outer")
df_merged = df_merged.reset_index()


# Add custom rules with apply
def resolve_lower_workpiece_id(row):

    upper_id = row.get("lower_workpiece_id_upper")
    lower_id = row.get("lower_workpiece_id_lower")

    if pd.notna(upper_id):

        if pd.notna(lower_id):  # Both exist
            assert upper_id == lower_id
            return upper_id
        else:
            return upper_id  # Only upper exists
    else:
        if pd.notna(lower_id):  # Only lower exists
            return lower_id

        return "workpiece_not_labeled"


df_merged["lower_workpiece_id"] = df_merged.apply(resolve_lower_workpiece_id, axis=1)

df_merged[
    [
        "upper_workpiece_id",
        "lower_workpiece_id",
        "class_value_upper_work_piece",
        "class_value_lower_work_piece",
        "class_value_tightening_process",
    ]
].to_csv("class_values.csv")
