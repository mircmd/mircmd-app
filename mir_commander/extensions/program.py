from mir_commander.extensions.extensions_manager import ExtensionsManager, ProgramExtension


class Program:
    def __init__(self, extensions_manager: ExtensionsManager):
        self._extensions_manager = extensions_manager

    def get_supported_programs(self, node_type: str) -> list[ProgramExtension]:
        programs: list[ProgramExtension] = []
        for program in self._extensions_manager.get_programs():
            if node_type in program.supported_node_types:
                programs.append(program)
        return programs

    def get_program(self, program_id: str) -> ProgramExtension:
        for program in self._extensions_manager.get_programs():
            if program.manifest.metadata.id == program_id:
                return program
        raise ValueError(f"Program with id {program_id} not found")
