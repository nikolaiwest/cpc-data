# %%
from schema.experiment_data import ExperimentData

experiment_data = ExperimentData(upper_workpiece_id=17401)

experiment_data.screw_left.angle

# %% Next steps

# get cycle via txt file for injection molding class

# add screw run class using pos (left / right) from upper wp id

# add label info (from class_values.csv): screw_data, upper, lower to base data class (maybe better experiment?)
