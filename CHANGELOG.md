# CHANGELOG



## v0.1.0 (2024-04-17)

### Build

* build: add development environment

Packaging: Flit
Via pre-commit: ruff / commitlint / pre-commit.ci
Via tox: pytest (py310~py312) / coverage / mypy / pre-commit ([`eaa31b0`](https://github.com/maejam/workfloz/commit/eaa31b0cd6bcdf50a75d7518b7a0ff8f6fb4203d))

### Chore

* chore: examples/, README, __init__.py

Add examples/loader.py and iris.csv
Update README.md
Add imports in src/workfloz/__init__.py ([`78f0fc7`](https://github.com/maejam/workfloz/commit/78f0fc7251b5813a30010c5da9bbdfe7236e751c))

* chore(tests): ignore ruff rules for tests ([`1beb444`](https://github.com/maejam/workfloz/commit/1beb4445df906e71d22d8e1979f8f4313fa67d3e))

* chore(repo): set up repository ([`4b59078`](https://github.com/maejam/workfloz/commit/4b5907881ce1626032162c5e169121d558c54698))

### Ci

* ci(github): update GH actions

Add PyPI and GH publishing to _release.yaml.
Remove Python3.8 and 3.9 from _tests.yaml.
Workflow push.yaml can be run manually.
Fix Flit command. ([`2eb669b`](https://github.com/maejam/workfloz/commit/2eb669bf307191783db7a7b5e1ff90476cb5070d))

* ci(github): add Github actions

When pushing on main: tests+precommit+Python Semantic Release.
When PR on any branch: tests+precommit+commitlint. ([`0e8c169`](https://github.com/maejam/workfloz/commit/0e8c1695d69a6f98c92c5a0c1ffda2b0ee8f04fa))

### Feature

* feat(action): add Action mechanism

Action wraps functions, enabling postponed function calls.
_ActionCall represents these function calls, encapsulating the Action
object and the arguments.
ActionContainer enables turning any class bound-methods into Actions.
AbstractContainer gives the possibility to defer the choice of concrete Container implementation. ([`2e5441f`](https://github.com/maejam/workfloz/commit/2e5441fad8c8e52244bd26b86b0865067ceeeb40))

* feat(parameter): add Parameter and validators

The descriptor Parameter class validates and documents attributes.
A default value can be set. It will be returned on get if no other value
is set. The default default value is UND (&#34;&lt;UNDEFINED&gt;&#34;).
Validators implemented:
    - dtype_validator is added automatically and validates values based
      on type annotations.
    - NumberValidator validates numbers lower and upper bounds.
    - StringValidator validates string min length and max length. ([`0fa2d41`](https://github.com/maejam/workfloz/commit/0fa2d413c9e86ea9bab78210a006563047e71d82))

* feat(entity): add entities

Entities have names and are retrieved from registry on instantiation.
Executable entities can be compiled and run.
Clusters can contain other entities (concrete: Job and Task).
Components can be inside or outside clusters. ([`5e65723`](https://github.com/maejam/workfloz/commit/5e65723468565410cc6852c5fde292bd7a9c70af))

### Fix

* fix(component): can set kwargs on AC from __init__ ([`c652570`](https://github.com/maejam/workfloz/commit/c65257057e69a4f88069b2924224edb42224c5f5))

### Refactor

* refactor(entity): entity subclasses as Mixins

NamedMixin and ExecutableMixin replace _NamedEntity and
_ExecutableEntity classes.
NamedMixin Entities have a name attributed by the user upon
instantiation and can be retrieved from the registry.
Other Entities are attributed a uuid name. ([`f96f57d`](https://github.com/maejam/workfloz/commit/f96f57deba18a028e16e860fd9483166e91716d4))
