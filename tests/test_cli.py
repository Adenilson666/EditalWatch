from editalwatch.cli import main

def test_main_starts_application(capsys) -> None:
    
    main()

    captured = capsys.readouterr()

    assert "EditalWatch iniciado com sucesso!" in captured.out