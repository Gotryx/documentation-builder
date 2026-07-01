"""
Testes unitários para as entidades e regras de domínio (entities.py).
"""

from docbuilder.core.domain.entities import Version, Project, Document, Volume


def test_version_parsing() -> None:
    # Caso ideal com 4 partes
    v = Version.from_string("2.3.4.12")
    assert v.major == 2
    assert v.minor == 3
    assert v.patch == 4
    assert v.build == 12

    # Caso com menos partes
    v2 = Version.from_string("1.5")
    assert v2.major == 1
    assert v2.minor == 5
    assert v2.patch == 0
    assert v2.build == 1

    # Caso string inválida (fallback para versão padrão)
    v_invalid = Version.from_string("versao-invalida")
    assert v_invalid.major == 1
    assert v_invalid.minor == 0
    assert v_invalid.patch == 0
    assert v_invalid.build == 1


def test_version_increments() -> None:
    v = Version(1, 0, 0, 1)
    
    v.increment_build()
    assert str(v) == "1.0.0.2"

    v.increment_patch()
    assert str(v) == "1.0.1.3"

    v.increment_minor()
    assert str(v) == "1.1.0.4"

    v.increment_major()
    assert str(v) == "2.0.0.5"


def test_project_validation() -> None:
    # Projeto válido
    p = Project(name="Engineering Handbook", author="GoTryx", language="pt-BR")
    assert len(p.validate()) == 0

    # Projeto inválido por falta de campos obrigatórios
    p_invalid = Project(name="", author="", language="")
    errors = p_invalid.validate()
    assert len(errors) == 3
    assert "nome" in errors[0]
    assert "autor" in errors[1]
    assert "idioma" in errors[2]


def test_project_volume_duplicate_validation() -> None:
    p = Project(name="Handbook", author="GoTryx", language="pt-BR")
    p.add_volume(Volume(title="Volume I"))
    p.add_volume(Volume(title="Volume I"))  # Duplicado
    
    errors = p.validate()
    assert len(errors) == 1
    assert "duplicados" in errors[0]


def test_document_validation() -> None:
    # Documento válido
    doc = Document(title="Visão", file_path="documents/visao.md")
    assert len(doc.validate()) == 0

    # Documento inválido
    doc_invalid = Document(title="", file_path="")
    errors = doc_invalid.validate()
    assert len(errors) == 2
