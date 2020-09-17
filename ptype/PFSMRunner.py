import sys
import numpy as np

from ptype.Machine import (
    IntegersNewAuto,
    StringsNewAuto,
    AnomalyNew,
    FloatsNewAuto,
    MissingsNew,
    BooleansNew,
    Genders,
    ISO_8601NewAuto,
    Date_EUNewAuto,
    Nonstd_DateNewAuto,
    SubTypeNonstdDateNewAuto,
    IPAddress,
    EmailAddress,
)
from ptype.utils import contains_all
from ptype.Model import Model

sys.path.insert(0, "src/")
MACHINES = {
    "integer": IntegersNewAuto(),
    "string": StringsNewAuto(),
    "float": FloatsNewAuto(),
    "boolean": BooleansNew(),
    "gender": Genders(),
    "date-iso-8601": ISO_8601NewAuto(),
    "date-eu": Date_EUNewAuto(),
    "date-non-std-subtype": SubTypeNonstdDateNewAuto(),
    "date-non-std": Nonstd_DateNewAuto(),
    "IPAddress": IPAddress(),
    "EmailAddress": EmailAddress(),
}


class PFSMRunner:
    def __init__(self, types):
        self.machines = [MissingsNew(), AnomalyNew()] + [MACHINES[t] for t in types]
        self.normalize_params()

    def generate_machine_probabilities(self, data):
        """ generates automata probabilities for a given column of data

        :param data:
        :return params:
        """
        probs = {}
        for input_string in data:
            probs[str(input_string)] = [
                self.machines[j].calculate_probability(str(input_string))
                for j in range(len(self.machines))
            ]

        return probs

    def set_unique_values(self, unique_values):
        for i, machine in enumerate(self.machines):

            machine.supported_words = {}

            for unique_value in unique_values:
                if contains_all(unique_value, machine.alphabet):
                    machine.supported_words[unique_value] = 1
                else:
                    machine.supported_words[unique_value] = 0

            self.machines[i].supported_words = machine.supported_words

    def remove_unique_values(self,):
        for i, machine in enumerate(self.machines):
            self.machines[i].supported_words = {}

    def update_values(self, unique_values):
        self.remove_unique_values()
        self.set_unique_values(unique_values)

    def normalize_params(self):
        for i, machine in enumerate(self.machines):
            if i not in [0, 1]:
                self.machines[i].I = Model.normalize_initial(machine.I_z)
                self.machines[i].F, self.machines[i].T = Model.normalize_final(
                    machine.F_z, machine.T_z
                )

    def initialize_params_uniformly(self):
        LOG_EPS = -1e150

        # make uniform
        for i, machine in enumerate(self.machines):
            # discards missing and anomaly types
            if i >= 2:
                # make uniform
                machine.I = {
                    a: np.log(0.5) if machine.I[a] != LOG_EPS else LOG_EPS
                    for a in machine.I
                }
                machine.I_z = {
                    a: np.log(0.5) if machine.I[a] != LOG_EPS else LOG_EPS
                    for a in machine.I
                }

                for a in machine.T:
                    for b in machine.T[a]:
                        for c in machine.T[a][b]:
                            machine.T[a][b][c] = np.log(0.5)
                            machine.T_z[a][b][c] = np.log(0.5)

                machine.F = {
                    a: np.log(0.5) if machine.F[a] != LOG_EPS else LOG_EPS
                    for a in machine.F
                }
                machine.F_z = {
                    a: np.log(0.5) if machine.F[a] != LOG_EPS else LOG_EPS
                    for a in machine.F
                }
