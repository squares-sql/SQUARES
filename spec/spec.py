from typing import List, Dict, Optional
from .type import Type, EnumType, ValueType
from .production import EnumProduction, ParamProduction, FunctionProduction, Production


class TypeSpec:
    _types: Dict[str, Type]

    def __init__(self):
        self._types = dict()

    def get_type(self, name: str) -> Optional[Type]:
        '''
        Return the type associated with `name`, if it is defined.
        If the type has not been defined, return `None`
        '''
        return self._types.get(name)

    def get_type_or_raise(self, name: str) -> Type:
        '''
        Return the type associated with `name`, if it is defined.
        If the type has not been defined, raise `KeyError`
        '''
        return self._types[name]

    def define_type(self, ty: Type) -> None:
        '''
        Add the type `ty` to this spec.
        Raise `ValueError` if another type with duplicated name is found.
        '''
        name = ty.name
        if name in self._types:
            raise ValueError(
                'The type has already been defined in the Tyrell spec: {}'
                .format(ty))
        else:
            self._types[name] = ty

    def types(self):
        '''Return an iterator for all defined types'''
        return iter(self._types.values())

    def num_types(self) -> int:
        '''Return the total number of defined types'''
        return len(self._types)

    def __repr(self) -> str:
        return 'TypeSpec({})'.format([str(x) for x in self._types.values()])


class ProductionSpec:
    _productions: List[Production]

    def __init__(self):
        self._productions = list()

    def get_production(self, id: int) -> Optional[Production]:
        '''
        Return the production associated with `id`.
        If the id does not correspond to any production, return `None`
        '''
        return self._productions[id] if id < len(self._productions) else None

    def get_production_or_raise(self, id: int) -> Production:
        '''
        Return the production associated with `id`.
        If the id does not correspond to any production, return `KeyError`
        '''
        try:
            return self._productions[id]
        except IndexError:
            msg = 'Cannot find production with given id: {}'.format(id)
            raise KeyError(msg)

    def add_enum_production(self, lhs: EnumType, rhs: int) -> EnumProduction:
        '''
        Create new enum production.
        This method guarantee that the newly created production will be different from every existing productions.
        Return the created production.
        '''
        id = len(self._productions)
        prod = EnumProduction(id, lhs, rhs)
        self._productions.append(prod)
        return prod

    def add_param_production(self, lhs: EnumType, rhs: int) -> ParamProduction:
        '''
        Create new param production.
        This method guarantee that the newly created production will be different from every existing productions.
        Return the created production.
        '''
        id = len(self._productions)
        prod = ParamProduction(id, lhs, rhs)
        self._productions.append(prod)
        return prod

    def add_func_production(self, name: str, lhs: ValueType, rhs: List[Type]) -> FunctionProduction:
        '''
        Create a new function production with the given `name`, `lhs`, and `rhs`.
        This method guarantee that the newly created production will be different from every existing productions.
        Return the created production.
        '''
        id = len(self._productions)
        prod = FunctionProduction(id, name, lhs, rhs)
        self._productions.append(prod)
        return prod

    def productions(self):
        '''Return an iterator for all productions'''
        return iter(self._productions)

    def num_productions(self) -> int:
        '''Return the number of defined productions'''
        return len(self._productions)

    def __repr__(self):
        return 'ProductionSpec({})'.format([str(x) for x in self._productions])


class ProgramSpec:
    _name: str
    _input: List[Type]
    _output: Type

    @staticmethod
    def check_value_type(ty):
        if not isinstance(ty, ValueType):
            raise ValueError(
                'Non-value type cannot be used as program input/output: {}'.format(
                    ty))

    def __init__(self, name: str, in_types: List[Type], out_type: Type):
        for ty in in_types:
            self.check_value_type(ty)
        self.check_value_type(out_type)

        self._name = name
        self._input = in_types
        self._output = out_type

    @property
    def name(self):
        return self._name

    @property
    def input(self):
        return self._input

    def num_input(self):
        return len(self._input)

    @property
    def output(self):
        return self._output


class TyrellSpec:
    _type_spec: TypeSpec
    _prog_spec: ProgramSpec
    _prod_spec: ProductionSpec

    def __init__(self, type_spec, prog_spec, prod_spec):
        # Generate all enum productions
        self._add_enum_productions(
            prod_spec,
            filter(lambda ty: isinstance(ty, EnumType),
                   type_spec.types()))
        # Generate all param productions
        self._add_param_productions(prod_spec, prog_spec.input)

        self._type_spec = type_spec
        self._prog_spec = prog_spec
        self._prod_spec = prod_spec

    @staticmethod
    def _add_enum_productions(prod_spec, enum_tys):
        for ty in enum_tys:
            for i in range(len(ty.domain)):
                prod_spec.add_enum_production(ty, i)

    @staticmethod
    def _add_param_productions(prod_spec, input_tys):
        for i, ty in enumerate(input_tys):
            prod_spec.add_param_production(ty, i)

    # Delegate methods for TypeSpec
    def get_type(self, name: str) -> Optional[Type]:
        return self._type_spec.get_type(name)

    def get_type_or_raise(self, name: str) -> Type:
        return self._type_spec.get_type_or_raise(name)

    def types(self):
        return self._type_spec.types()

    def num_types(self) -> int:
        return self._type_spec.num_types()

    # Delegate methods for ProductionSpec
    def get_production(self, id: int) -> Optional[Production]:
        return self._prod_spec.get_production(id)

    def get_production_or_raise(self, id: int) -> Production:
        return self._prod_spec.get_production_or_raise(id)

    def productions(self):
        return self._prod_spec.productions()

    def num_productions(self) -> int:
        return self._prod_spec.num_productions()

    # Delegate methods for ProgramSpec
    @property
    def name(self):
        return self._prog_spec.name

    @property
    def input(self):
        return self._prog_spec.input

    def num_input(self):
        return self._prog_spec.num_input

    @property
    def output(self):
        return self._prog_spec.output
