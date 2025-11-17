# Sistema de Gerenciamento de Salas de Aula

Este repositório contém um protótipo de API FastAPI para apoiar a operação diária do agendamento de salas de aula descrito no briefing. O objetivo é fornecer um backend simples com validações de disponibilidade, reserva, bloqueios e visualizações consolidadas para que a instituição possa evoluir o produto de forma iterativa.

## Principais recursos

- **Cadastro e manutenção de salas** com status (Disponível, Ocupada, Reservada ou Bloqueada) e capacidade.
- **Cadastro de turmas** com validação automática de disponibilidade (período, dias, datas e capacidade da sala) e sugestão de próxima janela quando não existe vaga.
- **Reserva e troca automática** de salas entre turmas, atualizando o status da sala desejada para *Reservada*.
- **Liberação pontual** de aulas para eventos/viagens registrando a data e o período liberados.
- **Pesquisa por salas** filtrando por tipo, status e capacidade, retornando a lista organizada por status.
- **Dashboard operacional** que consolida em formato simples quantas salas estão ocupadas ou disponíveis por período (manhã, tarde, noite), permitindo impressão rápida do panorama diário.

## Estrutura do projeto

```
app/
├── main.py          # Entrypoint FastAPI com rotas REST
├── models.py        # Schemas Pydantic compartilhados entre as camadas
├── services.py      # Regras de negócio (alocação, reservas, dashboard)
└── storage.py       # Persistência simples em JSON com seed automático das 21 salas
```

Os dados ficam em `data/store.json`. Ao iniciar o sistema pela primeira vez o arquivo é populado com as 21 salas do briefing.

## Pré-requisitos

- Python 3.11+
- Pip

## Instalação

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Execução

Execute o servidor uvicorn em modo de desenvolvimento:

```bash
uvicorn app.main:app --reload
```

A documentação interativa estará disponível em `http://localhost:8000/docs`.

## Próximos passos sugeridos

1. Implementar autenticação (incluindo múltiplo fator) com perfis de permissão de acordo com o briefing.
2. Persistir dados em banco relacional e criar histórico de movimentações.
3. Conectar dashboards a um gerador PDF para emissão automática das três folhas A4 por período.
4. Desenvolver interface web responsiva aplicando a paleta azul-marinho/prata e animações suaves descritas.

