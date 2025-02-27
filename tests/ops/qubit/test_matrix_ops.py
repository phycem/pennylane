# Copyright 2018-2021 Xanadu Quantum Technologies Inc.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Unit tests for the qubit matrix-based operations.
"""
# pylint: disable=import-outside-toplevel
import numpy as np
import pytest

from gate_data import H, I, S, T, X, Z

import pennylane as qml
from pennylane import numpy as pnp
from pennylane.operation import DecompositionUndefinedError
from pennylane.wires import Wires


class TestQubitUnitary:
    """Tests for the QubitUnitary class."""

    def test_qubit_unitary_noninteger_pow(self):
        """Test QubitUnitary raised to a non-integer power raises an error."""
        U = np.array(
            [[0.98877108 + 0.0j, 0.0 - 0.14943813j], [0.0 - 0.14943813j, 0.98877108 + 0.0j]]
        )

        op = qml.QubitUnitary(U, wires="a")

        with pytest.raises(qml.operation.PowUndefinedError):
            op.pow(0.123)

    def test_qubit_unitary_noninteger_pow_broadcasted(self):
        """Test broadcasted QubitUnitary raised to a non-integer power raises an error."""
        U = np.array(
            [
                [[0.98877108 + 0.0j, 0.0 - 0.14943813j], [0.0 - 0.14943813j, 0.98877108 + 0.0j]],
                [[0.98877108 + 0.0j, 0.0 - 0.14943813j], [0.0 - 0.14943813j, 0.98877108 + 0.0j]],
            ]
        )

        op = qml.QubitUnitary(U, wires="a")

        with pytest.raises(qml.operation.PowUndefinedError):
            op.pow(0.123)

    @pytest.mark.parametrize("n", (1, 3, -1, -3))
    def test_qubit_unitary_pow(self, n):
        """Test qubit unitary raised to an integer power."""
        U = np.array(
            [[0.98877108 + 0.0j, 0.0 - 0.14943813j], [0.0 - 0.14943813j, 0.98877108 + 0.0j]]
        )

        op = qml.QubitUnitary(U, wires="a")
        new_ops = op.pow(n)

        assert len(new_ops) == 1
        assert new_ops[0].wires == op.wires

        mat_to_pow = qml.math.linalg.matrix_power(qml.matrix(op), n)
        new_mat = qml.matrix(new_ops[0])

        assert qml.math.allclose(mat_to_pow, new_mat)

    @pytest.mark.parametrize("n", (1, 3, -1, -3))
    def test_qubit_unitary_pow_broadcasted(self, n):
        """Test broadcasted qubit unitary raised to an integer power."""
        U = np.array(
            [
                [[0.98877108 + 0.0j, 0.0 - 0.14943813j], [0.0 - 0.14943813j, 0.98877108 + 0.0j]],
                [[0.4125124 + 0.0j, 0.0 - 0.91095199j], [0.0 - 0.91095199j, 0.4125124 + 0.0j]],
            ]
        )

        op = qml.QubitUnitary(U, wires="a")
        new_ops = op.pow(n)

        assert len(new_ops) == 1
        assert new_ops[0].wires == op.wires

        mat_to_pow = qml.math.linalg.matrix_power(qml.matrix(op), n)
        new_mat = qml.matrix(new_ops[0])

        assert qml.math.allclose(mat_to_pow, new_mat)

    @pytest.mark.autograd
    @pytest.mark.parametrize(
        "U,num_wires", [(H, 1), (np.kron(H, H), 2), (np.tensordot([1j, -1, 1], H, axes=0), 1)]
    )
    def test_qubit_unitary_autograd(self, U, num_wires):
        """Test that the unitary operator produces the correct output and
        catches incorrect input with autograd."""

        out = qml.QubitUnitary(U, wires=range(num_wires)).matrix()

        # verify output type
        assert isinstance(out, np.ndarray)

        # verify equivalent to input state
        assert qml.math.allclose(out, U)

        # test non-square matrix
        with pytest.raises(ValueError, match="must be of shape"):
            qml.QubitUnitary(U[:, 1:], wires=range(num_wires)).matrix()

        # test non-unitary matrix
        U3 = U.copy()
        U3[0, 0] += 0.5
        with pytest.warns(UserWarning, match="may not be unitary"):
            qml.QubitUnitary(U3, wires=range(num_wires), unitary_check=True).matrix()

        # test an error is thrown when constructed with incorrect number of wires
        with pytest.raises(ValueError, match="must be of shape"):
            qml.QubitUnitary(U, wires=range(num_wires + 1)).matrix()

    @pytest.mark.torch
    @pytest.mark.parametrize(
        "U,num_wires", [(H, 1), (np.kron(H, H), 2), (np.tensordot([1j, -1, 1], H, axes=0), 1)]
    )
    def test_qubit_unitary_torch(self, U, num_wires):
        """Test that the unitary operator produces the correct output and
        catches incorrect input with torch."""
        import torch

        U = torch.tensor(U)
        out = qml.QubitUnitary(U, wires=range(num_wires)).matrix()

        # verify output type
        assert isinstance(out, torch.Tensor)

        # verify equivalent to input state
        assert qml.math.allclose(out, U)

        # test non-square matrix
        with pytest.raises(ValueError, match="must be of shape"):
            qml.QubitUnitary(U[:, 1:], wires=range(num_wires)).matrix()

        # test non-unitary matrix
        U3 = U.detach().clone()
        U3[0, 0] += 0.5
        with pytest.warns(UserWarning, match="may not be unitary"):
            qml.QubitUnitary(U3, wires=range(num_wires), unitary_check=True).matrix()

        # test an error is thrown when constructed with incorrect number of wires
        with pytest.raises(ValueError, match="must be of shape"):
            qml.QubitUnitary(U, wires=range(num_wires + 1)).matrix()

    @pytest.mark.tf
    @pytest.mark.parametrize(
        "U,num_wires", [(H, 1), (np.kron(H, H), 2), (np.tensordot([1j, -1, 1], H, axes=0), 1)]
    )
    def test_qubit_unitary_tf(self, U, num_wires):
        """Test that the unitary operator produces the correct output and
        catches incorrect input with tensorflow."""
        import tensorflow as tf

        U = tf.Variable(U)
        out = qml.QubitUnitary(U, wires=range(num_wires)).matrix()

        # verify output type
        assert isinstance(out, tf.Variable)

        # verify equivalent to input state
        assert qml.math.allclose(out, U)

        # test non-square matrix
        with pytest.raises(ValueError, match="must be of shape"):
            qml.QubitUnitary(U[:, 1:], wires=range(num_wires)).matrix()

        # test non-unitary matrix
        U3 = tf.Variable(U + 0.5)
        with pytest.warns(UserWarning, match="may not be unitary"):
            qml.QubitUnitary(U3, wires=range(num_wires), unitary_check=True).matrix()

        # test an error is thrown when constructed with incorrect number of wires
        with pytest.raises(ValueError, match="must be of shape"):
            qml.QubitUnitary(U, wires=range(num_wires + 1)).matrix()

    @pytest.mark.jax
    @pytest.mark.parametrize(
        "U,num_wires", [(H, 1), (np.kron(H, H), 2), (np.tensordot([1j, -1, 1], H, axes=0), 1)]
    )
    def test_qubit_unitary_jax(self, U, num_wires):
        """Test that the unitary operator produces the correct output and
        catches incorrect input with jax."""
        from jax import numpy as jnp

        U = jnp.array(U)
        out = qml.QubitUnitary(U, wires=range(num_wires)).matrix()

        # verify output type
        assert isinstance(out, jnp.ndarray)

        # verify equivalent to input state
        assert qml.math.allclose(out, U)

        # test non-square matrix
        with pytest.raises(ValueError, match="must be of shape"):
            qml.QubitUnitary(U[:, 1:], wires=range(num_wires)).matrix()

        # test non-unitary matrix
        U3 = U + 0.5
        with pytest.warns(UserWarning, match="may not be unitary"):
            qml.QubitUnitary(U3, wires=range(num_wires), unitary_check=True).matrix()

        # test an error is thrown when constructed with incorrect number of wires
        with pytest.raises(ValueError, match="must be of shape"):
            qml.QubitUnitary(U, wires=range(num_wires + 1)).matrix()

    @pytest.mark.jax
    @pytest.mark.parametrize(
        "U,num_wires", [(H, 1), (np.kron(H, H), 2), (np.tensordot([1j, -1, 1], H, axes=0), 1)]
    )
    def test_qubit_unitary_jax_jit(self, U, num_wires):
        """Tests that QubitUnitary works with jitting."""
        import jax
        from jax import numpy as jnp

        U = jnp.array(U)

        def mat_fn(m):
            return qml.QubitUnitary(m, wires=range(num_wires)).matrix()

        out = jax.jit(mat_fn)(U)
        assert qml.math.allclose(out, qml.QubitUnitary(U, wires=range(num_wires)).matrix())

    @pytest.mark.parametrize(
        "U,expected_gate,expected_params",
        [
            (I, qml.RZ, [0.0]),
            (Z, qml.RZ, [np.pi]),
            (S, qml.RZ, [np.pi / 2]),
            (T, qml.RZ, [np.pi / 4]),
            (qml.matrix(qml.RZ(0.3, wires=0)), qml.RZ, [0.3]),
            (qml.matrix(qml.RZ(-0.5, wires=0)), qml.RZ, [-0.5]),
            (
                np.array(
                    [
                        [0, -9.831019270939975e-01 + 0.1830590094588862j],
                        [9.831019270939975e-01 + 0.1830590094588862j, 0],
                    ]
                ),
                qml.Rot,
                [-0.18409714468526372, np.pi, 0.18409714468526372],
            ),
            (H, qml.Rot, [np.pi, np.pi / 2, 0.0]),
            (X, qml.Rot, [np.pi / 2, np.pi, -np.pi / 2]),
            (qml.matrix(qml.Rot(0.2, 0.5, -0.3, wires=0)), qml.Rot, [0.2, 0.5, -0.3]),
            (
                np.exp(1j * 0.02) * qml.matrix(qml.Rot(-1.0, 2.0, -3.0, wires=0)),
                qml.Rot,
                [-1.0, 2.0, -3.0],
            ),
            # An instance of a broadcast unitary
            (
                np.exp(1j * 0.02)
                * qml.Rot(
                    np.array([1.2, 2.3]), np.array([0.12, 0.5]), np.array([0.98, 0.567]), wires=0
                ).matrix(),
                qml.Rot,
                [[1.2, 2.3], [0.12, 0.5], [0.98, 0.567]],
            ),
        ],
    )
    def test_qubit_unitary_decomposition(self, U, expected_gate, expected_params):
        """Tests that single-qubit QubitUnitary decompositions are performed."""
        decomp = qml.QubitUnitary.compute_decomposition(U, wires=0)
        decomp2 = qml.QubitUnitary(U, wires=0).decomposition()

        assert len(decomp) == 1 == len(decomp2)
        assert isinstance(decomp[0], expected_gate)
        assert np.allclose(decomp[0].parameters, expected_params, atol=1e-7)
        assert isinstance(decomp2[0], expected_gate)
        assert np.allclose(decomp2[0].parameters, expected_params, atol=1e-7)

    def test_broadcasted_two_qubit_qubit_unitary_decomposition_raises_error(self):
        """Tests that broadcasted QubitUnitary decompositions are not supported."""
        U = qml.IsingYY.compute_matrix(np.array([1.2, 2.3, 3.4]))

        with pytest.raises(DecompositionUndefinedError, match="QubitUnitary does not support"):
            qml.QubitUnitary.compute_decomposition(U, wires=[0, 1])
        with pytest.raises(DecompositionUndefinedError, match="QubitUnitary does not support"):
            qml.QubitUnitary(U, wires=[0, 1]).decomposition()

    def test_qubit_unitary_decomposition_multiqubit_invalid(self):
        """Test that QubitUnitary is not decomposed for more than two qubits."""
        U = qml.Toffoli(wires=[0, 1, 2]).matrix()

        with pytest.raises(qml.operation.DecompositionUndefinedError):
            qml.QubitUnitary.compute_decomposition(U, wires=[0, 1, 2])

    def test_matrix_representation(self, tol):
        """Test that the matrix representation is defined correctly"""
        U = np.array(
            [[0.98877108 + 0.0j, 0.0 - 0.14943813j], [0.0 - 0.14943813j, 0.98877108 + 0.0j]]
        )
        res_static = qml.QubitUnitary.compute_matrix(U)
        res_dynamic = qml.QubitUnitary(U, wires=0).matrix()
        expected = U
        assert np.allclose(res_static, expected, atol=tol)
        assert np.allclose(res_dynamic, expected, atol=tol)

    def test_matrix_representation_broadcasted(self, tol):
        """Test that the matrix representation is defined correctly"""
        U = np.array(
            [[0.98877108 + 0.0j, 0.0 - 0.14943813j], [0.0 - 0.14943813j, 0.98877108 + 0.0j]]
        )
        U = np.tensordot([1j, -1.0, (1 + 1j) / np.sqrt(2)], U, axes=0)
        res_static = qml.QubitUnitary.compute_matrix(U)
        res_dynamic = qml.QubitUnitary(U, wires=0).matrix()
        expected = U
        assert np.allclose(res_static, expected, atol=tol)
        assert np.allclose(res_dynamic, expected, atol=tol)

    def test_controlled(self):
        """Test QubitUnitary's controlled method."""
        # pylint: disable=protected-access
        U = qml.PauliX.compute_matrix()
        base = qml.QubitUnitary(U, wires=0)

        expected = qml.ControlledQubitUnitary(U, control_wires="a", wires=0)

        out = base._controlled("a")
        assert qml.equal(out, expected)


class TestDiagonalQubitUnitary:
    """Test the DiagonalQubitUnitary operation."""

    def test_decomposition(self):
        """Test that DiagonalQubitUnitary falls back to QubitUnitary."""
        D = np.array([1j, 1, 1, -1, -1j, 1j, 1, -1])

        decomp = qml.DiagonalQubitUnitary.compute_decomposition(D, [0, 1, 2])
        decomp2 = qml.DiagonalQubitUnitary(D, wires=[0, 1, 2]).decomposition()

        assert len(decomp) == 1 == len(decomp2)
        assert decomp[0].name == "QubitUnitary" == decomp2[0].name
        assert decomp[0].wires == Wires([0, 1, 2]) == decomp2[0].wires
        assert np.allclose(decomp[0].data[0], np.diag(D))
        assert np.allclose(decomp2[0].data[0], np.diag(D))

    def test_decomposition_broadcasted(self):
        """Test that the broadcasted DiagonalQubitUnitary falls back to QubitUnitary."""
        D = np.outer([1.0, -1.0], [1.0, -1.0, 1j, 1.0])

        decomp = qml.DiagonalQubitUnitary.compute_decomposition(D, [0, 1])
        decomp2 = qml.DiagonalQubitUnitary(D, wires=[0, 1]).decomposition()

        assert len(decomp) == 1 == len(decomp2)
        assert decomp[0].name == "QubitUnitary" == decomp2[0].name
        assert decomp[0].wires == Wires([0, 1]) == decomp2[0].wires

        expected = np.array([np.diag([1.0, -1.0, 1j, 1.0]), np.diag([-1.0, 1.0, -1j, -1.0])])
        assert np.allclose(decomp[0].data[0], expected)
        assert np.allclose(decomp2[0].data[0], expected)

    def test_controlled(self):
        """Test that the correct controlled operation is created when controlling a qml.DiagonalQubitUnitary."""
        # pylint: disable=protected-access
        D = np.array([1j, 1, 1, -1, -1j, 1j, 1, -1])
        op = qml.DiagonalQubitUnitary(D, wires=[1, 2, 3])
        with qml.queuing.AnnotatedQueue() as q:
            op._controlled(control=0)
        tape = qml.tape.QuantumScript.from_queue(q)
        mat = qml.matrix(tape)
        assert qml.math.allclose(
            mat, qml.math.diag(qml.math.append(qml.math.ones(8, dtype=complex), D))
        )

    def test_controlled_broadcasted(self):
        """Test that the correct controlled operation is created when
        controlling a qml.DiagonalQubitUnitary with a broadcasted diagonal."""
        # pylint: disable=protected-access
        D = np.array([[1j, 1, -1j, 1], [1, -1, 1j, -1]])
        op = qml.DiagonalQubitUnitary(D, wires=[1, 2])
        with qml.queuing.AnnotatedQueue() as q:
            op._controlled(control=0)
        tape = qml.tape.QuantumScript.from_queue(q)
        mat = qml.matrix(tape)
        expected = np.array(
            [np.diag([1, 1, 1, 1, 1j, 1, -1j, 1]), np.diag([1, 1, 1, 1, 1, -1, 1j, -1])]
        )
        assert qml.math.allclose(mat, expected)

    def test_matrix_representation(self, tol):
        """Test that the matrix representation is defined correctly"""
        diag = np.array([1, -1])
        res_static = qml.DiagonalQubitUnitary.compute_matrix(diag)
        res_dynamic = qml.DiagonalQubitUnitary(diag, wires=0).matrix()
        expected = np.array([[1, 0], [0, -1]])
        assert np.allclose(res_static, expected, atol=tol)
        assert np.allclose(res_dynamic, expected, atol=tol)

    def test_matrix_representation_broadcasted(self, tol):
        """Test that the matrix representation is defined correctly for a broadcasted diagonal."""
        diag = np.array([[1, -1], [1j, -1], [-1j, -1]])
        res_static = qml.DiagonalQubitUnitary.compute_matrix(diag)
        res_dynamic = qml.DiagonalQubitUnitary(diag, wires=0).matrix()
        expected = np.array([[[1, 0], [0, -1]], [[1j, 0], [0, -1]], [[-1j, 0], [0, -1]]])
        assert np.allclose(res_static, expected, atol=tol)
        assert np.allclose(res_dynamic, expected, atol=tol)

    @pytest.mark.parametrize("n", (2, -1, 0.12345))
    @pytest.mark.parametrize("diag", ([1.0, -1.0], np.array([1.0, -1.0])))
    def test_pow(self, n, diag):
        """Test pow method returns expected results."""
        op = qml.DiagonalQubitUnitary(diag, wires="b")
        pow_ops = op.pow(n)
        assert len(pow_ops) == 1

        for x_op, x_pow in zip(op.data[0], pow_ops[0].data[0]):
            assert (x_op + 0.0j) ** n == x_pow

    @pytest.mark.parametrize("n", (2, -1, 0.12345))
    @pytest.mark.parametrize(
        "diag", ([[1.0, -1.0]] * 5, np.array([[1.0, -1j], [1j, 1j], [-1j, 1]]))
    )
    def test_pow_broadcasted(self, n, diag):
        """Test pow method returns expected results for broadcasted diagonals."""
        op = qml.DiagonalQubitUnitary(diag, wires="b")
        pow_ops = op.pow(n)
        assert len(pow_ops) == 1

        qml.math.allclose(np.array(op.data[0], dtype=complex) ** n, pow_ops[0].data[0])

    @pytest.mark.parametrize("D", [[1, 2], [[0.2, 1.0, -1.0], [1.0, -1j, 1j]]])
    def test_error_matrix_not_unitary(self, D):
        """Tests that error is raised if diagonal by `compute_matrix` does not lead to a unitary"""
        with pytest.raises(ValueError, match="Operator must be unitary"):
            qml.DiagonalQubitUnitary.compute_matrix(np.array(D))
        with pytest.raises(ValueError, match="Operator must be unitary"):
            qml.DiagonalQubitUnitary(np.array(D), wires=1).matrix()

    @pytest.mark.parametrize("D", [[1, 2], [[0.2, 1.0, -1.0], [1.0, -1j, 1j]]])
    def test_error_eigvals_not_unitary(self, D):
        """Tests that error is raised if diagonal by `compute_matrix` does not lead to a unitary"""
        with pytest.raises(ValueError, match="Operator must be unitary"):
            qml.DiagonalQubitUnitary.compute_eigvals(np.array(D))
        with pytest.raises(ValueError, match="Operator must be unitary"):
            qml.DiagonalQubitUnitary(np.array(D), wires=0).eigvals()

    @pytest.mark.jax
    def test_jax_jit(self):
        """Test that the diagonal matrix unitary operation works
        within a QNode that uses the JAX JIT"""
        import jax

        jnp = jax.numpy

        dev = qml.device("default.qubit", wires=1, shots=None)

        @jax.jit
        @qml.qnode(dev)
        def circuit(x):
            diag = jnp.exp(1j * x * jnp.array([1, -1]) / 2)
            qml.Hadamard(wires=0)
            qml.DiagonalQubitUnitary(diag, wires=0)
            return qml.expval(qml.PauliX(0))

        x = 0.654
        grad = jax.grad(circuit)(x)
        expected = -jnp.sin(x)
        assert np.allclose(grad, expected)

    @pytest.mark.jax
    def test_jax_jit_broadcasted(self):
        """Test that the diagonal matrix unitary operation works
        within a QNode that uses the JAX JIT and broadcasting"""
        import jax

        jnp = jax.numpy

        dev = qml.device("default.qubit", wires=1, shots=None)

        @jax.jit
        @qml.qnode(dev)
        def circuit(x):
            diag = jnp.exp(1j * jnp.outer(x, jnp.array([1, -1])) / 2)
            qml.Hadamard(wires=0)
            qml.DiagonalQubitUnitary(diag, wires=0)
            return qml.expval(qml.PauliX(0))

        x = jnp.array([0.654, 0.321])
        jac = jax.jacobian(circuit)(x)
        expected = jnp.diag(-jnp.sin(x))
        assert np.allclose(jac, expected)

    @pytest.mark.tf
    @pytest.mark.slow  # test takes 12 seconds due to tf.function
    def test_tf_function(self):
        """Test that the diagonal matrix unitary operation works
        within a QNode that uses TensorFlow autograph"""
        import tensorflow as tf

        dev = qml.device("default.qubit", wires=1, shots=None)

        @tf.function
        @qml.qnode(dev)
        def circuit(x):
            x = tf.cast(x, tf.complex128)
            diag = tf.math.exp(1j * x * tf.constant([1.0 + 0j, -1.0 + 0j]) / 2)
            qml.Hadamard(wires=0)
            qml.DiagonalQubitUnitary(diag, wires=0)
            return qml.expval(qml.PauliX(0))

        x = tf.Variable(0.452)

        with tf.GradientTape() as tape:
            loss = circuit(x)

        grad = tape.gradient(loss, x)
        expected = -tf.math.sin(x)  # pylint: disable=invalid-unary-operand-type
        assert np.allclose(grad, expected)


labels = [X, X, [1, 1]]
ops = [
    qml.QubitUnitary(X, wires=0),
    qml.ControlledQubitUnitary(X, control_wires=0, wires=1),
    qml.DiagonalQubitUnitary([1, 1], wires=0),
]


class TestUnitaryLabels:
    """Test the label of matrix operations."""

    @pytest.mark.parametrize("op", ops)
    def test_no_cache(self, op):
        """Test labels work without a provided cache."""
        assert op.label() == "U"

    @pytest.mark.parametrize("op", ops)
    def test_matrices_not_in_cache(self, op):
        """Test provided cache doesn't have a 'matrices' keyword."""
        assert op.label(cache={}) == "U"

    @pytest.mark.parametrize("op", ops)
    def test_cache_matrices_not_list(self, op):
        """Test 'matrices' key pair is not a list."""
        assert op.label(cache={"matrices": 0}) == "U"

    @pytest.mark.parametrize("mat, op", zip(labels, ops))
    def test_empty_cache_list(self, mat, op):
        """Test matrices list is provided, but empty. Operation should have `0` label and matrix
        should be added to cache."""
        cache = {"matrices": []}
        assert op.label(cache=cache) == "U(M0)"
        assert qml.math.allclose(cache["matrices"][0], mat)

    @pytest.mark.parametrize("mat, op", zip(labels, ops))
    def test_something_in_cache_list(self, mat, op):
        """If something exists in the matrix list, but parameter is not in the list, then parameter
        added to list and label given number of its position."""
        cache = {"matrices": [Z]}
        assert op.label(cache=cache) == "U(M1)"

        assert len(cache["matrices"]) == 2
        assert qml.math.allclose(cache["matrices"][1], mat)

    @pytest.mark.parametrize("mat, op", zip(labels, ops))
    def test_matrix_already_in_cache_list(self, mat, op):
        """If the parameter already exists in the matrix cache, then the label uses that index and the
        matrix cache is unchanged."""
        cache = {"matrices": [Z, mat, S]}
        assert op.label(cache=cache) == "U(M1)"

        assert len(cache["matrices"]) == 3


class TestBlockEncode:
    """Test the BlockEncode operation."""

    @pytest.mark.parametrize(
        ("input_matrix", "wires", "expected_hyperparameters"),
        [
            (1, 1, {"norm": 1, "subspace": (1, 1, 2)}),
            ([1], 1, {"norm": 1, "subspace": (1, 1, 2)}),
            ([[1]], 1, {"norm": 1, "subspace": (1, 1, 2)}),
            (pnp.array(1), [1], {"norm": 1, "subspace": (1, 1, 2)}),
            (pnp.array([1]), 1, {"norm": 1, "subspace": (1, 1, 2)}),
            (pnp.array([[1]]), 1, {"norm": 1, "subspace": (1, 1, 2)}),
            ([[1, 0], [0, 1]], [0, 1], {"norm": 1.0, "subspace": (2, 2, 4)}),
            (pnp.array([[1, 0], [0, 1]]), range(2), {"norm": 1.0, "subspace": (2, 2, 4)}),
            (pnp.identity(3), ["a", "b", "c"], {"norm": 1.0, "subspace": (3, 3, 8)}),
        ],
    )
    def test_accepts_various_types(self, input_matrix, wires, expected_hyperparameters):
        """Test that BlockEncode outputs expected attributes for various input matrix types."""
        op = qml.BlockEncode(input_matrix, wires)
        assert np.allclose(op.parameters, input_matrix)
        assert op.hyperparameters["norm"] == expected_hyperparameters["norm"]
        assert op.hyperparameters["subspace"] == expected_hyperparameters["subspace"]

    @pytest.mark.parametrize(
        ("input_matrix", "wires"),
        [(1, 1), (1, 2), (1, [1]), (1, range(2)), (np.identity(2), ["a", "b"])],
    )
    def test_varied_wires(self, input_matrix, wires):
        """Test that BlockEncode wires are stored correctly for various wire input types."""
        assert qml.BlockEncode(input_matrix, wires).wires == Wires(wires)

    @pytest.mark.parametrize(
        ("input_matrix", "wires", "msg"),
        [
            (
                [[0, 1], [1, 0]],
                1,
                r"Block encoding a \(2 x 2\) matrix requires a Hilbert space of size"
                r" at least \(4 x 4\). Cannot be embedded in a 1 qubit system.",
            ),
        ],
    )
    def test_error_raised_invalid_hilbert_space(self, input_matrix, wires, msg):
        """Test the correct error is raised when inputting an invalid number of wires."""
        with pytest.raises(ValueError, match=msg):
            qml.BlockEncode(input_matrix, wires)

    @pytest.mark.parametrize(
        ("input_matrix", "wires", "output_matrix"),
        [
            (1, 0, [[1, 0], [0, -1]]),
            (0.3, 0, [[0.3, 0.9539392], [0.9539392, -0.3]]),
            (
                0.1,
                range(2),
                [[0.1, 0.99498744, 0, 0], [0.99498744, -0.1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]],
            ),
            (
                [[0.1, 0.2], [0.3, 0.4]],
                range(2),
                [
                    [0.1, 0.2, 0.97283788, -0.05988708],
                    [0.3, 0.4, -0.05988708, 0.86395228],
                    [0.94561648, -0.07621992, -0.1, -0.3],
                    [-0.07621992, 0.89117368, -0.2, -0.4],
                ],
            ),
            (
                [[0.1, 0.2, 0.3], [0.3, 0.4, 0.2], [0.1, 0.2, 0.3]],
                range(3),
                [
                    [
                        [0.1, 0.2, 0.3, 0.91808609, -0.1020198, -0.08191391, 0.0, 0.0],
                        [0.3, 0.4, 0.2, -0.1020198, 0.83017102, -0.1020198, 0.0, 0.0],
                        [0.1, 0.2, 0.3, -0.08191391, -0.1020198, 0.91808609, 0.0, 0.0],
                        [0.93589192, -0.09400608, -0.07258899, -0.1, -0.3, -0.1, 0.0, 0.0],
                        [-0.09400608, 0.85841586, -0.11952016, -0.2, -0.4, -0.2, 0.0, 0.0],
                        [-0.07258899, -0.11952016, 0.87203542, -0.3, -0.2, -0.3, 0.0, 0.0],
                        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
                        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
                    ],
                ],
            ),
        ],
    )
    def test_correct_output_matrix(self, input_matrix, wires, output_matrix):
        """Test that BlockEncode outputs the correct matrix."""
        assert np.allclose(qml.matrix(qml.BlockEncode)(input_matrix, wires), output_matrix)

    @pytest.mark.parametrize(
        ("input_matrix", "wires"),
        [
            (1, 0),
            (0.3, 0),
            (np.array([[0.1, 0.2], [0.3, 0.4]]), range(2)),
            (np.array([[0.1, 0.2, 0.3]]), range(2)),
            (np.array([[0.1], [0.2], [0.3]]), range(2)),
            (np.array([[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]]), range(3)),
            (np.array([[1, 2], [3, 4]]), range(2)),
        ],
    )
    def test_unitary(self, input_matrix, wires):
        """Test that BlockEncode matrices are unitary."""
        mat = qml.matrix(qml.BlockEncode(input_matrix, wires))
        assert np.allclose(np.eye(len(mat)), mat.dot(mat.T.conj()))

    @pytest.mark.tf
    @pytest.mark.parametrize(
        ("input_matrix", "wires", "output_matrix"),
        [
            (1.0, 0, [[1, 0], [0, -1]]),
            (0.3, 0, [[0.3, 0.9539392], [0.9539392, -0.3]]),
            (
                [[0.1, 0.2], [0.3, 0.4]],
                range(2),
                [
                    [0.1, 0.2, 0.97283788, -0.05988708],
                    [0.3, 0.4, -0.05988708, 0.86395228],
                    [0.94561648, -0.07621992, -0.1, -0.3],
                    [-0.07621992, 0.89117368, -0.2, -0.4],
                ],
            ),
            (
                0.1,
                range(2),
                [[0.1, 0.99498744, 0, 0], [0.99498744, -0.1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]],
            ),
        ],
    )
    def test_blockencode_tf(self, input_matrix, wires, output_matrix):
        """Test that the BlockEncode operator matrix is correct for tf."""
        import tensorflow as tf

        input_matrix = tf.Variable(input_matrix)

        op = qml.BlockEncode(input_matrix, wires)
        assert np.allclose(qml.matrix(op), output_matrix)
        assert qml.math.get_interface(qml.matrix(op)) == "tensorflow"

    @pytest.mark.torch
    @pytest.mark.parametrize(
        ("input_matrix", "wires", "output_matrix"),
        [
            (1, 0, [[1, 0], [0, -1]]),
            (0.3, 0, [[0.3, 0.9539392], [0.9539392, -0.3]]),
            (
                [[0.1, 0.2], [0.3, 0.4]],
                range(2),
                [
                    [0.1, 0.2, 0.97283788, -0.05988708],
                    [0.3, 0.4, -0.05988708, 0.86395228],
                    [0.94561648, -0.07621992, -0.1, -0.3],
                    [-0.07621992, 0.89117368, -0.2, -0.4],
                ],
            ),
            (
                0.1,
                range(2),
                [[0.1, 0.99498744, 0, 0], [0.99498744, -0.1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]],
            ),
        ],
    )
    def test_blockencode_torch(self, input_matrix, wires, output_matrix):
        """Test that the BlockEncode operator matrix is correct for torch."""
        import torch

        input_matrix = torch.tensor(input_matrix)
        op = qml.BlockEncode(input_matrix, wires)
        assert np.allclose(qml.matrix(op), output_matrix)
        assert qml.math.get_interface(qml.matrix(op)) == "torch"

    @pytest.mark.jax
    @pytest.mark.parametrize(
        ("input_matrix", "wires", "output_matrix"),
        [
            (1, 0, [[1, 0], [0, -1]]),
            (0.3, 0, [[0.3, 0.9539392], [0.9539392, -0.3]]),
            (
                [[0.1, 0.2], [0.3, 0.4]],
                range(2),
                [
                    [0.1, 0.2, 0.97283788, -0.05988708],
                    [0.3, 0.4, -0.05988708, 0.86395228],
                    [0.94561648, -0.07621992, -0.1, -0.3],
                    [-0.07621992, 0.89117368, -0.2, -0.4],
                ],
            ),
            (
                0.1,
                range(2),
                [[0.1, 0.99498744, 0, 0], [0.99498744, -0.1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]],
            ),
        ],
    )
    def test_blockencode_jax(self, input_matrix, wires, output_matrix):
        """Test that the BlockEncode operator matrix is correct for jax."""
        import jax.numpy as jnp

        input_matrix = jnp.array(input_matrix)
        op = qml.BlockEncode(input_matrix, wires)
        assert np.allclose(qml.matrix(op), output_matrix)
        assert qml.math.get_interface(qml.matrix(op)) == "jax"

    @pytest.mark.parametrize("method", ["backprop"])
    @pytest.mark.parametrize(
        (
            "wires",
            "input_matrix",
            "expected_result",
        ),  # expected_results calculated manually
        [
            (range(1), pnp.array(0.3), 4 * 0.3),
            (range(2), pnp.diag([0.2, 0.3]), 4 * pnp.diag([0.2, 0])),
        ],
    )
    def test_blockencode_grad(self, method, wires, input_matrix, expected_result):
        """Test that BlockEncode is differentiable."""
        dev = qml.device("default.qubit", wires=wires)

        @qml.qnode(dev, diff_method=method)
        def circuit(input_matrix):
            qml.BlockEncode(input_matrix, wires=wires)
            return qml.expval(qml.PauliZ(wires=0))

        assert np.allclose(qml.grad(circuit)(input_matrix), expected_result)

    @pytest.mark.jax
    @pytest.mark.parametrize(
        (
            "wires",
            "input_matrix",
            "expected_result",
        ),  # expected_results calculated manually
        [
            (range(1), pnp.array(0.3), 4 * 0.3),
            (range(2), pnp.diag([0.2, 0.3]), 4 * pnp.diag([0.2, 0])),
        ],
    )
    def test_blockencode_grad_jax(self, wires, input_matrix, expected_result):
        """Test that block encode is differentiable when using jax."""
        import jax
        import jax.numpy as jnp

        input_matrix = jnp.array(input_matrix)
        expected_result = jnp.array(expected_result)

        dev = qml.device("default.qubit", wires=wires)

        @qml.qnode(dev)
        def circuit(input_matrix):
            qml.BlockEncode(input_matrix, wires=wires)
            return qml.expval(qml.PauliZ(wires=0))

        grad = jax.grad(circuit, argnums=0)(input_matrix)
        assert np.allclose(grad, expected_result)

    @pytest.mark.tf
    @pytest.mark.parametrize(
        ("wires", "input_matrix", "expected_result"),  # expected_results calculated manually
        [
            (range(1), pnp.array(0.3), 4 * 0.3),
            (range(2), pnp.diag([0.2, 0.3]), 4 * pnp.diag([0.2, 0])),
        ],
    )
    def test_blockencode_grad_tf(self, wires, input_matrix, expected_result):
        """Test that block encode is differentiable when using tensorflow."""
        import tensorflow as tf

        input_matrix = tf.Variable(input_matrix)

        dev = qml.device("default.qubit", wires=wires)

        @qml.qnode(dev)
        def circuit(input_matrix):
            qml.BlockEncode(input_matrix, wires=wires)
            return qml.expval(qml.PauliZ(wires=0))

        with tf.GradientTape() as tape:
            result = circuit(input_matrix)

        computed_grad = tape.gradient(result, input_matrix)
        assert np.allclose(computed_grad, expected_result)

    @pytest.mark.parametrize(
        ("input_matrix", "wires"),
        [
            (1, 0),
            (0.3, 0),
            (0.1, range(2)),
            (
                [[0.1, 0.2], [0.3, 0.4]],
                range(2),
            ),
            ([[0.1, 0.2, 0.3], [0.3, 0.4, 0.2], [0.1, 0.2, 0.3]], range(3)),
        ],
    )
    def test_adjoint(self, input_matrix, wires):
        """Test that the adjoint of a BlockEncode operation is correctly computed."""
        mat = qml.matrix(qml.BlockEncode(input_matrix, wires))
        adj = qml.matrix(qml.adjoint(qml.BlockEncode(input_matrix, wires)))
        other_adj = qml.matrix(qml.BlockEncode(input_matrix, wires).adjoint())
        assert np.allclose(np.eye(len(mat)), mat @ adj)
        assert np.allclose(np.eye(len(mat)), mat @ other_adj)

    def test_label(self):
        """Test the label method for BlockEncode op"""
        op = qml.BlockEncode(0.5, wires=[0, 1])
        assert op.label() == "BlockEncode"

    @pytest.mark.parametrize(
        ("input_matrix", "wires", "output_value"),
        [
            (1, [0], 1),
            ([[0.1, 0.2], [0.3, 0.4]], range(2), -0.8),
            (
                0.1,
                range(2),
                1,
            ),
        ],
    )
    def test_blockencode_integration(self, input_matrix, wires, output_value):
        """Test that the BlockEncode gate applied to a circuit produces the correct final state."""
        dev = qml.device("default.qubit", wires=wires)

        @qml.qnode(dev)
        def circuit(input_matrix):
            qml.BlockEncode(input_matrix, wires=wires)
            return qml.expval(qml.PauliZ(wires=0))

        assert circuit(input_matrix) == output_value


class TestInterfaceMatricesLabel:
    """Test different interface matrices with qubit."""

    def check_interface(self, mat):
        """Interface independent helper method."""

        op = qml.QubitUnitary(mat, wires=0)

        cache = {"matrices": []}
        assert op.label(cache=cache) == "U(M0)"
        assert qml.math.allclose(cache["matrices"][0], mat)

        cache = {"matrices": [0, mat, 0]}
        assert op.label(cache=cache) == "U(M1)"
        assert len(cache["matrices"]) == 3

    @pytest.mark.torch
    def test_labelling_torch_tensor(self):
        """Test matrix cache labelling with torch interface."""

        import torch

        mat = torch.tensor([[1, 0], [0, -1]])
        self.check_interface(mat)

    @pytest.mark.tf
    def test_labelling_tf_variable(self):
        """Test matrix cache labelling with tf interface."""

        import tensorflow as tf

        mat = tf.Variable([[1, 0], [0, -1]])

        self.check_interface(mat)

    @pytest.mark.jax
    def test_labelling_jax_variable(self):
        """Test matrix cache labelling with jax interface."""

        import jax.numpy as jnp

        mat = jnp.array([[1, 0], [0, -1]])

        self.check_interface(mat)


control_data = [
    (qml.QubitUnitary(X, wires=0), Wires([])),
    (qml.DiagonalQubitUnitary([1, 1], wires=1), Wires([])),
    (qml.ControlledQubitUnitary(X, control_wires=0, wires=1), Wires([0])),
]


@pytest.mark.parametrize("op, control_wires", control_data)
def test_control_wires(op, control_wires):
    """Test ``control_wires`` attribute for matrix operations."""
    assert op.control_wires == control_wires
