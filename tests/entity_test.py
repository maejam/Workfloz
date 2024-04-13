import pytest

from workfloz.cluster import Cluster
from workfloz.cluster import getcluster
from workfloz.cluster import Job
from workfloz.cluster import setcluster
from workfloz.cluster import Task
from workfloz.component import Component
from workfloz.entity import compiled
from workfloz.entity import Entity
from workfloz.entity import ExecutableMixin
from workfloz.entity import NamedMixin
from workfloz.entity import result
from workfloz.exceptions import WorkflowCompilationError
from workfloz.exceptions import WorkflowDefinitionError
from workfloz.exceptions import WorkflowExecutionError


class TestEntity:
    def test_name(self):
        e = Entity()
        assert len(e._name_) == 36  # uuid


class TestNamedEntity:
    E1: type[Entity]
    E2: type[Entity]
    E3: type[Entity]

    def setup_method(self, method):
        class E1(NamedMixin, Entity):
            pass

        class E2(NamedMixin, Entity):
            pass

        class E3(E2):
            pass

        type(self).E1 = E1
        type(self).E2 = E2
        type(self).E3 = E3

    def teardown_method(self, method):
        NamedMixin._instances_ = {}

    def test_name(self):
        e1 = self.E1("e1")
        e3 = self.E3("e3")
        assert e1._name_ == "e1"
        assert e3._name_ == "e3"

    def test_same_name_returns_same_object(self):
        e1 = self.E1("e1")
        assert self.E1("e1") is e1
        e3 = self.E3("e3")
        assert self.E3("e3") is e3

    def test_incompatible_type_raises(self):
        e1 = self.E1("e1")
        e2 = self.E2("e2")
        with pytest.raises(TypeError, match="is not compatible with type"):
            self.E2("e1")
        with pytest.raises(TypeError, match="is not compatible with type"):
            self.E3("e2")

    def test_compatible_type_returns_entity(self):
        e3 = self.E3("e3")
        assert self.E2("e3") is e3


class TestExecutableEntity(TestNamedEntity):
    E1: type[Entity]
    E3: type[Entity]

    def setup_method(self, method):
        class E1(NamedMixin, ExecutableMixin, Entity):
            def _compile_(self):
                return self

            def _run_(self):
                return self._compiled_

        class E3(self.E2, ExecutableMixin, Entity):
            value = 1

            def _compile_(self):
                return self.value + 3

            def _run_(self):
                return self._compiled_ * 4

        type(self).E1 = E1
        type(self).E3 = E3

    def test_abstract_methods(self):
        assert "_run_" in ExecutableMixin.__abstractmethods__
        assert "_compile_" in ExecutableMixin.__abstractmethods__

    def test_compiling_executable_entity(self):
        e3 = self.E3("e3")
        e3.compile()
        assert compiled(e3) == 4

    def test_running_executable_entity(self):
        e3 = self.E3("e3")
        e3.start()
        assert result(e3) == 16

    def test_running_uncompiled_entity_raises(self):
        with pytest.raises(
            WorkflowExecutionError, match="Run the 'compile' method on it first. "
        ):
            e3 = self.E3("e3")
            e3.run()

        class E4(ExecutableMixin, NamedMixin, Entity):
            def _compile_(self):
                return self

            def _run_(self):
                return self.notthere

        with pytest.raises(AttributeError, match="object has no attribute 'notthere'"):
            e4 = E4("e4")
            e4.run()

    def test_compiled_function_on_non_executable_entity_raises(self):
        with pytest.raises(TypeError, match="You can't call 'compiled' on it."):
            e2 = self.E2("e2")
            compiled(e2)

    def test_compiled_function_on_not_compiled_entity_raises(self):
        with pytest.raises(
            WorkflowCompilationError, match="has not been compiled yet."
        ):
            e3 = self.E3("e3")
            compiled(e3)

    def test_result_function_on_non_executable_entity_raises(self):
        with pytest.raises(TypeError, match="You can't call 'result' on it."):
            e2 = self.E2("e2")
            result(e2)

    def test_result_function_on_not_compiled_entity_raises(self):
        with pytest.raises(
            WorkflowExecutionError, match="Besides, it is not compiled either."
        ):
            e3 = self.E3("e3")
            result(e3)

    def test_result_function_on_not_run_entity_raises(self):
        with pytest.raises(
            WorkflowExecutionError,
            match="^((?!Besides, the entity is not compiled).)*$",
        ):
            e3 = self.E3("e3")
            e3.compile()
            result(e3)


class TestCluster(TestExecutableEntity):
    E1: type[Cluster]
    C: type[Component]

    def setup_method(self, method):
        class E1(Cluster):
            pass

        class E3(self.E3, Cluster):
            pass

        class C(Component):
            def _compile_(self):
                return self

            def _run_(self):
                return self._compiled_

        type(self).E1 = E1
        type(self).E3 = E3
        type(self).C = C

    def test_setcluster_only_accepts_cluster_or_None(self):
        with pytest.raises(
            WorkflowDefinitionError, match="Only a Cluster object or 'None'"
        ):
            setcluster(self.E2("e2"))
        with pytest.raises(
            WorkflowDefinitionError, match="Only a Cluster object or 'None'"
        ):
            setcluster(3)

    def test_cluster_with_cm_sets_contextvar_correctly(self):
        e1 = self.E1("e1")
        assert getcluster() is None
        with e1:
            assert getcluster() is e1
        assert getcluster() is None

    def test_cluster_with_decorator_sets_contextvar_correctly(self):
        assert getcluster() is None

        @self.E1("e1")
        def func():
            assert getcluster() is self.E1("e1")

        func()
        assert getcluster() is None

    def test_cluster_hierarchy_with_cm_sets_contextvar_correctly(self):
        assert getcluster() is None
        with self.E1("e1"):
            assert getcluster() is self.E1("e1")
            with self.E3("e3"):
                assert getcluster() is self.E3("e3")
            assert getcluster() is self.E1("e1")
        assert getcluster() is None

    def test_cluster_hierarchy_with_decorators_sets_contextvar_correctly(self):
        assert getcluster() is None

        @self.E1("e1")
        def func1():
            assert getcluster() is self.E1("e1")

        @self.E1("e1")
        @self.E3("e3")
        def func2():
            assert getcluster() is self.E3("e3")

        assert getcluster() is None
        func1()
        func2()

    def test_defining_cluster_inside_itself_raises_exception(self):
        with pytest.raises(
            WorkflowDefinitionError, match="set a cluster inside itself."
        ):
            with self.E1("e1"):
                with self.E3("e3"):
                    with self.E1("e1"):
                        pass

    def test_clusters_and_entities_attributes_are_correct(self):
        assert self.E1("e1")._entities_ == []
        with self.E1("e1"):
            a = self.C("a")
            b = self.C("b")
        assert self.E1("e1")._entities_ == [a, b]

    def test_running_empty_cluster(self):
        with self.E1("e1"):
            pass
        assert len(self.E1("e1")._entities_) == 0
        assert not hasattr(self.E1("e1"), "_compiled_")
        self.E1("e1").start()
        assert self.E1("e1")._compiled_ == self.E1("e1")
        assert self.E1("e1")._result_ == self.E1("e1")

    def test_running_non_empty_cluster(self):
        with self.E1("e1"):
            a = self.C("a")
            b = self.C("b")
        assert len(self.E1("e1")._entities_) == 2
        assert not hasattr(self.E1("e1"), "_compiled_")
        self.E1("e1").start()
        assert self.E1("e1")._compiled_ == self.E1("e1")
        assert compiled(a) == a
        assert compiled(b) == b
        assert result(a) == a
        assert result(b) == b

    def test_3_level_hierarchy_running(self):
        class E4(Cluster):
            pass

        class C2(Component):
            def __init__(self, name, value: str):
                super().__init__(name, value)
                self.value = value

            def _compile_(self):
                return self.value.upper()

            def _run_(self):
                return self._compiled_.split(".")[3]

        with self.E1("e1") as e1:
            with E4("e4") as e4:
                a = self.C("a")
                b = C2("b", "This.is.a.test.string.")

        e1.start()
        assert result(e1) == e1
        assert result(e4) == e4
        assert result(a) == a
        assert result(b) == "TEST"


class TestJobTaskComponent:
    def setup_method(self):
        setcluster(None)

        class C(Component):
            def _compile_(self):
                return 1

            def _run_(self):
                return 2

        self.C = C

    def teardown_method(self, method):
        NamedMixin._instances_ = {}

    def test_str(self):
        job = Job("job")
        task = Task("task")
        assert str(job) == "Job: job"
        assert str(task) == "Task: task"

    def test_job_and_task(self):
        with Job("job") as j:
            with Task("task1") as t1:
                with Task("task2") as t2:
                    """"""
        assert j._entities_ == [t1]
        assert t1._entities_ == [t2]
        assert t2._entities_ == []

    def test_creating_job_inside_another_cluster_raises_exception(self):
        with pytest.raises(
            WorkflowDefinitionError,
            match="A Job cannot be created inside another cluster.",
        ):
            with Cluster("c"):
                with Job("job"):
                    """"""

    def test_creating_top_level_task_raises_exception(self):
        with pytest.raises(
            WorkflowDefinitionError, match="A Task can only be created inside"
        ):
            with Task("task"):
                """"""

    def test_component_outside_cluster(self):
        c = self.C("c")
        c.start()
        assert result(c) == 2
