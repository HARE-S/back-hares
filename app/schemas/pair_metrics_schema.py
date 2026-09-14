"""Esquemas de respuesta para métricas de par."""

from marshmallow import Schema, fields


class PairSchema(Schema):
    """Un par funcional/literario de una prueba."""

    test_letter = fields.Str()
    order = fields.Int()
    vef_functional = fields.Float(allow_none=True)
    vef_literary = fields.Float(allow_none=True)
    mean = fields.Float(allow_none=True)
    difference = fields.Float(allow_none=True)
    is_complete = fields.Bool()
    reading_level = fields.Str(allow_none=True)  # "bajo", "normal", "alto"


class PairSeriesResponseSchema(Schema):
    """Serie de pares ordenados por test_letter."""

    pairs = fields.List(fields.Nested(PairSchema))


class TransitionSchema(Schema):
    """Transición entre dos pruebas consecutivas."""

    transition = fields.Str()  # "I-A", "A-B", etc.
    value = fields.Float(allow_none=True)  # delta de media
    improved = fields.Bool(allow_none=True)


class ProgressResponseSchema(Schema):
    """Progresión individual."""

    transitions = fields.List(fields.Nested(TransitionSchema))
    global_progress = fields.Float(allow_none=True)
    measured_span = fields.Str(allow_none=True)  # "I-C"
    tests_with_data = fields.Int()


class GroupTransitionSchema(Schema):
    """Transición con estadísticas de grupo."""

    transition = fields.Str()
    improved = fields.Int()  # count de alumnos que mejoraron
    measurable = fields.Int()  # count de alumnos con datos en ambas pruebas
    percentage = fields.Float(allow_none=True)


class GroupGlobalSchema(Schema):
    """Resumen global de progreso del grupo."""

    improved = fields.Int()
    measurable = fields.Int()
    percentage = fields.Float(allow_none=True)


class ReadingLevelCountSchema(Schema):
    """Recuento de alumnos por banda de nivel lector."""

    bajo = fields.Int()
    normal = fields.Int()
    alto = fields.Int()


class GroupProgressResponseSchema(Schema):
    """Progresión agregada de un grupo."""

    transitions = fields.Dict(keys=fields.Str(), values=fields.Nested(GroupTransitionSchema))
    global_info = fields.Nested(GroupGlobalSchema, attribute="global")
    reading_level_counts = fields.Nested(ReadingLevelCountSchema)  # "NIVEL POR PRUEBAS"
    population = fields.Int()  # total de alumnos en la sección
    anomalous_excluded = fields.Int()  # count de resultados anómalos excluidos de agregados
