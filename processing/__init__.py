from .remove_negative_values import remove_negative_values
from .resample_uniform_times import resample_uniform_times
from .resample_equal_lengths import resample_equal_lengths

# from .apply_equal_lengths import apply_equal_lengths

PROCESSING_REGISTRY = {
    "remove_negative_values": remove_negative_values,
    "resample_uniform_times": resample_uniform_times,
    "resample_equal_lengths": resample_equal_lengths,
}
