# Copyright 2018-2020 Xanadu Quantum Technologies Inc.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
r"""
Subroutines are the most basic template, consisting of a collection of quantum operations, and not fulfilling
any of the characteristics of other templates (i.e. to prepare a specific state, to be repeated or to encode features).
"""

from .interferometer import Interferometer
from .arbitrary_unitary import ArbitraryUnitary
from .single_excitation_unitary import SingleExcitationUnitary
from .double_excitation_unitary import DoubleExcitationUnitary
