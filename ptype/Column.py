from enum import Enum
import joblib
import numpy as np
from ptype.utils import project_root


def get_unique_vals(col, return_counts=False):
    """List of the unique values found in a column."""
    return np.unique([str(x) for x in col.tolist()], return_counts=return_counts)


# Use same names and values as the constants in Model.py. Could consolidate.
class Status(Enum):
    TYPE = 1
    MISSING = 2
    ANOMALOUS = 3


class Column:
    def __init__(self, series, counts, p_t, predicted_type, p_z, normal_values, missing_values, anomalous_values):
        self.series = series
        self.p_t = p_t
        self.p_t_canonical = {}
        self.predicted_type = predicted_type
        self.p_z = p_z
        self.normal_values = normal_values
        self.missing_values = missing_values
        self.anomalous_values = anomalous_values
        self.arff_type = None
        self.unique_vals = []
        self.unique_vals_counts = []
        self.cache_unique_vals()
        self.unique_vals_status = [
            Status.TYPE if i in self.normal_values else
            Status.MISSING if i in self.missing_values else
            Status.ANOMALOUS if i in self.anomalous_values else
            None  # only happens in the "all identical" case?
            for i, _ in enumerate(self.unique_vals)
        ]
        self.features = self.get_features(counts)
        self.arff_type = column2ARFF.get_arff(self.features)[0]

    def __repr__(self):
        ptype_pandas_mapping = {"integer": "Int64"}  # ouch
        props = {
            "type": self.predicted_type,
            "dtype": ptype_pandas_mapping[self.predicted_type],
            "arff_type": self.arff_type,
            "normal_values": self.get_normal_values(),
            "missing_values": self.get_missing_values(),
            "missingness_ratio": self.get_ratio(Status.MISSING),
            "anomalies": self.get_anomalous_values(),
            "anomalous_ratio": self.get_ratio(Status.ANOMALOUS),
        }
        if self.arff_type == "nominal":
            props["categorical_values"] = self.get_normal_values()
        return repr(props)

    def cache_unique_vals(self):
        """Call this to (re)initialise the cache of my unique values."""
        self.unique_vals, self.unique_vals_counts = get_unique_vals(
            self.series, return_counts=True
        )

    def has_missing(self):
        return self.get_missing_values() != []

    def has_anomalous(self):
        return self.get_anomalous_values() != []

    def show_results_for(self, status, desc):
        indices = [
            i
            for i, _ in enumerate(self.unique_vals)
            if self.unique_vals_status[i] == status
        ]
        if len(indices) == 0:
            return 0
        else:
            print("\t" + desc, [self.unique_vals[i] for i in indices][:20])
            print(
                "\ttheir counts: ", [self.unique_vals_counts[i] for i in indices][:20]
            )
            return sum(self.unique_vals_counts[indices])

    def show_results(self):
        print("col: " + str(self.series.name))
        print("\tpredicted type: " + self.predicted_type)
        print("\tposterior probs: ", self.p_t)

        normal = self.show_results_for(Status.TYPE, "some normal data values: ")
        missing = self.show_results_for(Status.MISSING, "missing values:")
        anomalies = self.show_results_for(Status.ANOMALOUS, "anomalies:")

        total = normal + missing + anomalies

        print("\tfraction of normal:", round(normal / total, 2), "\n")
        print("\tfraction of missing:", round(missing / total, 2), "\n")
        print("\tfraction of anomalies:", round(anomalies / total, 2), "\n")

    def get_ratio(self, status):
        indices = [
            i
            for i, _ in enumerate(self.unique_vals)
            if self.unique_vals_status[i] == status
        ]
        total = sum(self.unique_vals_counts)
        return round(sum(self.unique_vals_counts[indices]) / total, 2)

    def get_normal_values(self):
        """Values identified as 'normal'."""
        return [
            v
            for i, v in enumerate(self.unique_vals)
            if self.unique_vals_status[i] == Status.TYPE
        ]

    def get_missing_values(self):
        return [
            v
            for i, v in enumerate(self.unique_vals)
            if self.unique_vals_status[i] == Status.MISSING
        ]

    def get_anomalous_values(self):
        return [
            v
            for i, v in enumerate(self.unique_vals)
            if self.unique_vals_status[i] == Status.ANOMALOUS
        ]

    def reclassify_normal(self, vs):
        for i in [np.where(self.unique_vals == v)[0][0] for v in vs]:
            self.unique_vals_status[i] = Status.TYPE
            self.p_z[i, :] = [1.0, 0.0, 0.0]

    def replace_missing(self, v):
        for u in self.get_missing_values():
            self.series.replace(u, v, inplace=True)
        self.cache_unique_vals()

    def get_features(self, counts):
        posterior = self.p_t

        sorted_posterior = [
            posterior[3],
            posterior[4:].sum(),
            posterior[2],
            posterior[0],
            posterior[1],
        ]

        entries = [
            str(int_element) for int_element in self.series.tolist()
        ]
        U = len(np.unique(entries))
        U_clean = len(self.normal_values)

        N = len(entries)
        N_clean = sum([counts[index] for index in self.normal_values])

        u_ratio = U / N
        if U_clean == 0 and N_clean == 0:
            u_ratio_clean = 0.0
        else:
            u_ratio_clean = U_clean / N_clean

        return np.array(
            sorted_posterior + [u_ratio, u_ratio_clean, U, U_clean]
        )


class Column2ARFF:
    def __init__(self, model_folder="models"):
        self.normalizer = joblib.load(model_folder + "robust_scaler.pkl")
        self.clf = joblib.load(model_folder + "LR.sav")

    def get_arff(self, features):
        features[[7, 8]] = self.normalizer.transform(features[[7, 8]].reshape(1, -1))[0]
        arff_type = self.clf.predict(features.reshape(1, -1))[0]

        if arff_type == "categorical":
            arff_type = "nominal"
        # find normal values for categorical type

        arff_type_posterior = self.clf.predict_proba(features.reshape(1, -1))[0]

        return arff_type, arff_type_posterior


column2ARFF = Column2ARFF(project_root() + "/../models/")
