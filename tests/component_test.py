import pytest

from workfloz.cluster import Cluster
from workfloz.cluster import setcluster
from workfloz.component import _ActionCall
from workfloz.component import Abstract
from workfloz.component import Action
from workfloz.component import ActionContainer
from workfloz.entity import NamedMixin
from workfloz.entity import result
from workfloz.exceptions import WorkflowCompilationError
from workfloz.exceptions import WorkflowExecutionError
from workfloz.parameter import NumberValidator
from workfloz.parameter import Parameter
from workfloz.parameter import UND


class TestAction:
    a1: Action
    a2: Action

    def setup_method(self, method):
        def func1(x, y):
            return x + y

        def func2(x, y=2):
            return x * y

        a1 = Action("a1", func=func1)
        a2 = Action(func=func2)
        type(self).a1 = a1
        type(self).a2 = a2

    def teardown_method(self, method):
        NamedMixin._instances_ = {}

    def test_execute(self):
        assert self.a1._execute(2, 3) == 5
        assert self.a2._execute(3, 4) == 12
        assert self.a2._execute(3) == 6

    def test_bind_args(self):
        assert self.a1._bind_args().arguments == {}
        assert self.a1._bind_args(include_und=True).arguments == {"x": UND, "y": UND}

    def test_bind_args_default_values(self):
        assert self.a2._bind_args().arguments == {"y": 2}
        assert self.a2._bind_args(include_und=True).arguments == {"x": UND, "y": 2}

    def test_str(self):
        assert str(self.a1) == f"Action: {self.a1._name_}(x=<UNDEFINED>, y=<UNDEFINED>)"
        assert str(self.a2) == f"Action: {self.a2._name_}(x=<UNDEFINED>, y=2)"

    def test_call(self):
        with pytest.raises(TypeError, match="got an unexpected keyword argument 'z'"):
            self.a1(1, y=2, z=3)
        assert type(self.a1(1, 2)) is _ActionCall
        assert self.a1(1, 2) is not self.a1(1, 2)

    def test_ActionCall_str(self):
        call = self.a1(1, 2)
        assert (
            str(call)
            == f"_ActionCall: {call._name_} <{call._action_._name_}(x=1, y=2)>"
        )

    def test_run_ActionCall_no_cluster(self):
        call1 = self.a1(1, 2)
        call2 = self.a1(2, 5)
        call1.start()
        call2.start()
        assert result(call1) == 3
        assert result(call2) == 7

    def test_run_ActionCall_with_Undefined_raises(self):
        call = self.a1(y=1)
        with pytest.raises(WorkflowCompilationError, match="has undefined arguments"):
            call.compile()

    def test_run_ActionCall_inside_cluster(self):
        with Cluster("c") as c:
            call1 = self.a2(10)
            call2 = self.a1(9, 3)
        assert c._entities_ == [call1, call2]
        c.start()
        assert result(call1) == 20
        assert result(call2) == 12


class TestActionContainer(TestAction):
    a1: Action
    a2: Action
    ac: ActionContainer
    abstract: Abstract

    def setup_method(self, method):
        # NamedMixin._instances_ = {}
        class AC(ActionContainer):
            a = Parameter()
            b: int = Parameter(default=42)
            c = Parameter(default=43, validators=[NumberValidator(min_value=42)])

            def meth1(self, x, y):
                return x + y

            def meth2(self, x, y=2):
                return x * y

            def meth3(self, a, b, c=44):
                return a - b

        ac = AC("ac")
        type(self).ac = ac
        type(self).a1 = ac.meth1
        type(self).a2 = ac.meth2
        type(self).abstract = Abstract("abstract")
        setcluster(None)

    def test_bind_args_ActionContainer_attributes(self):
        self.ac.x = 1
        assert self.a1._bind_args().arguments == {"x": 1}
        assert self.a1._bind_args(include_und=True).arguments == {"x": 1, "y": UND}
        assert self.a2._bind_args().arguments == {"x": 1, "y": 2}
        assert self.a2._bind_args(include_und=True).arguments == {"x": 1, "y": 2}

    def test_call_with_descriptors_on_AC(self):
        with pytest.raises(TypeError, match="should be of type"):
            self.ac.meth3(b="test")
        with pytest.raises(ValueError, match="should be between"):
            self.ac.meth3(c=40)
        self.ac.c = 55
        r = self.ac.meth3(10.5, 5, 44)
        r.start()
        assert (result(r)) == 5.5
        # Check parameters back to previous values
        assert self.ac.a == UND
        assert self.ac.b == 42
        assert self.ac.c == 55

    def test_bind_args_with_Parameters_on_AC(self):
        assert self.ac.meth3._bind_args().arguments == {"b": 42, "c": 43}
        assert self.ac.meth3._bind_args(include_und=True).arguments == {
            "a": UND,
            "b": 42,
            "c": 43,
        }

    def test_set_AC_attribute_inside_cluster(self):
        with Cluster("cluster") as c:
            self.ac.x = 12
            call1 = self.ac.meth2()
            self.ac.x = 10
            call2 = self.ac.meth2()
            self.ac.x = 6

        assert c._entities_ == [call1, call2]
        c.start()
        assert result(call1) == 24
        assert result(call2) == 20

    def test_abtract_action(self):
        with Cluster("c") as c:
            a1 = self.abstract.notthere1(1, 2, a=1, z=6)
            a2 = self.abstract.notthere2()
        assert c._entities_ == [a1, a2]
        c.compile()
        with pytest.raises(WorkflowExecutionError, match="is abstract"):
            c.run()
