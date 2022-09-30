# This code is part of Qiskit.
#
# (C) Copyright IBM 2021.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Tests for estimator class."""

import json
from unittest.mock import patch, ANY

from qiskit.circuit.library import RealAmplitudes
from qiskit.quantum_info import SparsePauliOp

from qiskit_ibm_runtime.utils.json import RuntimeEncoder
from qiskit_ibm_runtime.utils.utils import _hash
from qiskit_ibm_runtime.qiskit.primitives.utils import _circuit_key

from qiskit_ibm_runtime import Estimator, Session
from ..ibm_test_case import IBMTestCase

from .mock.fake_runtime_service import FakeRuntimeService


class TestEstimator(IBMTestCase):
    """Class for testing the Estimator class."""

    def test_estimator_circuit_caching(self):
        """Test circuit caching in Estimator class"""
        psi1 = RealAmplitudes(num_qubits=2, reps=2)
        psi2 = RealAmplitudes(num_qubits=2, reps=3)
        psi1_id = _hash(json.dumps(_circuit_key(psi1), cls=RuntimeEncoder))
        psi2_id = _hash(json.dumps(_circuit_key(psi2), cls=RuntimeEncoder))

        # pylint: disable=invalid-name
        H1 = SparsePauliOp.from_list([("II", 1), ("IZ", 2), ("XI", 3)])
        H2 = SparsePauliOp.from_list([("IZ", 1)])

        with Session(
            service=FakeRuntimeService(channel="ibm_quantum", token="abc"),
            backend="ibmq_qasm_simulator",
        ) as session:
            estimator = Estimator(session=session)

            # calculate [ <psi1(theta1)|H1|psi1(theta1)> ]
            with patch.object(estimator._session, "run") as mock_run:
                estimator.run([psi1, psi2], [H1, H2], [[ANY]*6, [ANY]*8])
                _, kwargs = mock_run.call_args
                inputs = kwargs["inputs"]
                self.assertDictEqual(inputs["circuits"],{psi1_id: psi1, psi2_id: psi2})
                self.assertEqual(inputs["circuit_ids"],[psi1_id, psi2_id])

            # calculate [ <psi2(theta2)|H2|psi2(theta2)> ]
            with patch.object(estimator._session, "run") as mock_run:
                estimator.run([psi2], [H1], [[ANY]*8])
                _, kwargs = mock_run.call_args
                inputs = kwargs["inputs"]
                self.assertDictEqual(inputs["circuits"],{})
                self.assertEqual(inputs["circuit_ids"],[psi2_id])
