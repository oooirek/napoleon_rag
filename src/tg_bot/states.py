from aiogram.fsm.state import State, StatesGroup


class IngestState(StatesGroup):
	waiting_for_file = State()


class QueryState(StatesGroup):
	waiting_for_query = State()
