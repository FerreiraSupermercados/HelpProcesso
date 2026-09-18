# Central de Processos e Riscos

Aplicação interna da Ferreira Supermercados para consulta e gestão do repositório corporativo de processos, além do registro, análise e acompanhamento de auditorias operacionais.

O projeto é uma aplicação [Streamlit](https://streamlit.io/) conectada ao Supabase. Os POPs e demais documentos são acessados pelos links cadastrados no Google Drive.

## Objetivos

- Centralizar os processos e documentos operacionais da empresa.
- Permitir consulta, filtros e visualização dos POPs cadastrados.
- Registrar auditorias por loja, frente e data.
- Importar checklists preenchidos pela equipe de processos.
- Confrontar os itens críticos com o POP selecionado e legível.
- Registrar não conformidades, responsáveis, prazos, ações corretivas e status.
- Consolidar indicadores de rede, rankings, mapa de risco e histórico.
- Exportar os dados operacionais para análise no Excel.

## Stack

- Python
- Streamlit
- Pandas
- NumPy
- Requests
- Supabase REST API
- PyPDF2 — leitura inicial do relatório/checklist importado
- pdfplumber — leitura página a página do POP
- Google Drive — armazenamento dos PDFs por link público

## Estrutura do projeto

```text
.
├── app.py                    # Interface Streamlit e regras da aplicação
├── db.py                     # Conector Supabase e operações de persistência
├── sheets_reader.py          # Leitor auxiliar da API do Google Sheets
├── requirements.txt          # Dependências Python
├── LOGO.png                 # Logo do cabeçalho
├── LOGO2.png                # Logo da barra lateral
├── .streamlit/
│   └── secrets.toml          # Segredos locais — não versionar
└── README.md
```

### `app.py`

Contém o login, aceite de LGPD, navegação, componentes visuais, filtros, telas de processos e todo o fluxo da aba Auditoria.

### `db.py`

Centraliza o acesso ao Supabase, incluindo:

- leitura, criação, edição e exclusão de processos;
- leitura, criação, atualização e exclusão de auditorias;
- normalização das não conformidades antigas e novas;
- conversão dos links do Google Drive para visualização e acesso direto;
- registro do aceite de LGPD;
- associação padrão entre frente de auditoria e POP-base.

### `sheets_reader.py`

Módulo auxiliar para leitura de uma planilha do Google Sheets, incluindo hiperlinks. Ele não é o caminho principal de persistência da aplicação atual; o fluxo principal usa o Supabase.

## Instalação local

Recomenda-se Python 3.10 ou superior.

### 1. Criar o ambiente virtual

No PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

No macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Instalar as dependências

```bash
python -m pip install -r requirements.txt
```

### 3. Configurar os segredos

Crie ou preencha `.streamlit/secrets.toml` localmente. Nunca publique esse arquivo nem coloque senhas ou chaves reais no README.

Estrutura mínima esperada:

```toml
SUPABASE_URL = "https://seu-projeto.supabase.co"
SUPABASE_ANON_KEY = "sua-chave-anon"
session_secret = "um-segredo-longo-e-aleatorio"

admins = ["controladoria"]

[users]
controladoria = "senha-do-usuario"
```

Os nomes das chaves precisam ser exatamente `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `admins` e `users`.

### 4. Executar

```bash
streamlit run app.py
```

Por padrão, o Streamlit abrirá a aplicação em `http://localhost:8501`.

## Configuração de documentos

Os PDFs são cadastrados no campo de link do processo e devem estar disponíveis para leitura pelo servidor.

Para arquivos do Google Drive:

1. Abra o arquivo no Drive.
2. Configure o compartilhamento como **Qualquer pessoa com o link — leitor**.
3. Cadastre o link na coluna/campo **Link Documento** do processo.
4. Teste o botão de abrir PDF na aplicação.

A aplicação não depende de uma sessão pessoal do Google Drive. O download e a leitura funcionam somente se o link estiver acessível conforme a permissão configurada.

## Acesso e LGPD

O fluxo de entrada possui:

1. autenticação por usuário e senha configurados nos secrets;
2. identificação de administradores pela lista `admins`;
3. token de sessão para preservar o login após atualização da página;
4. termo de ciência e aceite da LGPD;
5. registro do aceite na tabela `aceites_lgpd`.

As informações são de uso interno. As credenciais são individuais e não devem ser compartilhadas.

## Navegação principal

### Processos

Consulta o catálogo de processos vindo do Supabase. Possui filtros laterais, busca livre, tabela e visualização online dos documentos vinculados.

### Novo Processo

Disponível para administradores. Permite cadastrar um processo, código, macroprocesso, status, criticidade, revisão, observações e link do documento.

### Gerenciar

Disponível para administradores. Permite editar ou remover processos cadastrados.

### Auditoria

A aba Auditoria possui as subabas descritas abaixo.

## Aba Auditoria

### Painel geral

Apresenta os indicadores consolidados das auditorias registradas:

- nota média da rede;
- lojas auditadas;
- não conformidades em aberto;
- não conformidades sem rastreio ao POP;
- ranking das lojas;
- score por frente;
- score por bloco do checklist;
- gaps recorrentes.

### Rankings

Classifica as lojas pela auditoria mais recente e apresenta a cobertura por frente. Também mostra os blocos do checklist com menor média na rede.

### Mapa de risco

Permite consultar a distribuição das notas por loja e frente, com a mesma régua de classificação usada no restante da Auditoria.

### Análise por loja

Consolida a unidade selecionada e compara seus resultados com a média da rede na mesma base de cálculo. A tela apresenta:

- nota geral da loja;
- frentes auditadas e frentes ainda sem auditoria;
- score por bloco;
- maior fortaleza;
- prioridade de ação;
- comparação com a média da rede;
- resumo limitado das não conformidades;
- evolução entre ciclos;
- botão para abrir o detalhamento completo das NCs.

O resumo da lista de NCs é intencionalmente limitado para evitar uma página extensa. O detalhamento completo fica na subaba **Não conformidades**.

### Não conformidades

Exibe as divergências em cards e permite filtrar por:

- status;
- loja;
- frente;
- bloco;
- criticidade;
- rastreio ao POP.

Cada NC pode conter item do checklist, descrição, POP, ponto divergente, evidência, criticidade, impacto, responsável, prazo, ação corretiva e status.

Os status disponíveis são:

- `Aberta`
- `Em andamento`
- `Concluída`
- `Cancelada`

A alteração de status é feita em modal, dentro do fluxo da própria NC, sem abrir um editor gigante abaixo do card.

### Histórico

Mostra as auditorias salvas, com filtros por loja e frente. Exibe data, loja, frente, auditor, notas por bloco, nota total, nível, quantidade de NCs e NCs sem POP vinculado.

Também permite exportar o recorte exibido em CSV.

### Importar PDF

É o fluxo de auditoria automática a partir de um checklist preenchido.

#### Fluxo

1. O usuário envia o PDF do checklist.
2. O sistema extrai loja, data, nota total, blocos e itens usando `PyPDF2`.
3. A frente é identificada pelo conteúdo do relatório ou informada manualmente.
4. O usuário confere os dados extraídos.
5. O POP correspondente é selecionado explicitamente.
6. O sistema baixa e lê o POP página a página com `pdfplumber`.
7. O sistema confronta os itens com o texto extraído do POP.
8. Somente os itens elegíveis pela régua do checklist são apresentados como pontos críticos.
9. A auditoria só pode ser salva depois que o POP tiver sido selecionado e lido.

#### Regra de elegibilidade dos itens

O fluxo usa a régua do checklist, e não uma regra genérica de percentual.

- padrão: gerar NC para itens com nível até `3`;
- opções disponíveis: nível até `2`, `3` ou `4`;
- nível `0` a `2`: criticidade alta;
- nível `3`: criticidade média;
- níveis acima do limite selecionado: não viram NC automática.

#### Confronto com o POP

O sistema trabalha com rastreabilidade explícita:

- aceita pergunta inteira, referência explícita ou trecho literal contínuo encontrado no PDF;
- registra página e seção quando identificadas;
- não usa similaridade semântica, palavras soltas ou aproximação automática;
- não usa o nome do arquivo para vincular um POP;
- se o checklist foi montado manualmente e a pergunta não se repete literalmente, o vínculo explícito do POP fica registrado e a evidência textual fica para revisão;
- sem POP selecionado, sem link acessível ou sem texto extraído, o salvamento permanece bloqueado.

#### Frentes e POPs

As frentes conhecidas possuem uma sugestão de POP-base quando o código está configurado e o documento existe no catálogo. O usuário pode selecionar outro POP cadastrado com PDF legível quando necessário.

Frentes novas ou setores adicionais são aceitos sem uma lista fixa. O sistema pode:

- identificar o nome da frente no cabeçalho do checklist;
- solicitar o nome da frente quando não conseguir identificá-lo;
- criar um identificador técnico `EXT-AUD-*` somente dentro do contexto da Auditoria;
- permitir a seleção manual de qualquer POP legível cadastrado.

O sistema nunca seleciona automaticamente o primeiro POP disponível para uma frente nova.

### Lançar manual

Permite registrar uma auditoria sem importar um checklist PDF. O fluxo manual também exige um POP selecionado e legível antes de salvar.

É possível informar notas por bloco e cadastrar NCs com descrição, item, criticidade, status, responsável, prazo, ponto do POP e ação corretiva.

Também existe a opção de informar uma nova frente/setor, mantendo o mesmo vínculo explícito com o POP selecionado.

### Dados e exportação

Exportações disponíveis em CSV:

- auditorias;
- não conformidades;
- histórico;
- mapa de risco;
- NCs filtradas.

Os CSVs usam separador `;` e codificação adequada para abertura no Excel brasileiro.

A área de importação aceita JSON apenas para consolidação técnica ou restauração de backup entre painéis. O formato operacional destinado aos usuários para análise é CSV.

## POP-base das frentes conhecidas

O mapa abaixo fica em `db.py` e funciona como sugestão estrita de documento padrão:

| Código da frente | Frente | POP-base configurado |
|---|---|---|
| `AÇO-AUD-01` | Açougue | Nenhum configurado atualmente |
| `FRE-AUD-02` | Frente de Loja | `POP-3-OPL-3.25` |
| `REC-AUD-03` | Recebimento | `POP-2-LGE-2.1` |
| `ATA-AUD-04` | Atacado | Nenhum configurado atualmente |

Essa configuração não impede uma seleção manual de outro POP legível. Ela apenas define qual documento deve aparecer como sugestão quando o cadastro possuir o código e o link acessível.

## Persistência e dados

### Tabela `processos`

O conector trabalha com os nomes internos abaixo, mapeados para os nomes reais das colunas no Supabase:

- tipo de documento;
- nível atual;
- macroprocesso;
- código;
- processo;
- código do processo;
- sigla;
- status;
- criticidade;
- tipo de critério;
- última revisão;
- link do documento;
- tipo de atividade;
- revisado pelo gestor;
- observações;
- objetivo estratégico.

### Tabela `auditorias`

O fluxo utiliza, no mínimo, os campos:

- `id`;
- `loja`;
- `data`;
- `tipo`;
- `avaliador`;
- `topicos`;
- `total`;
- `criticas`.

`topicos` guarda os blocos, pesos, percentuais e informações do POP utilizado. `criticas` é persistido como uma coleção de strings JSON para manter compatibilidade com registros antigos e permitir a normalização no carregamento.

### Tabela `aceites_lgpd`

Registra o usuário que aceitou o termo de ciência da aplicação.

### Atualização dos dados

Depois de salvar, editar ou excluir registros, a aplicação limpa o cache correspondente e recarrega os dados. O catálogo de processos possui cache curto para evitar consultas excessivas ao Supabase.

## Testes e validação local

Com o ambiente virtual ativado:

```bash
python -m py_compile app.py
python -m pip check
```

Para um smoke test da interface, abra a aplicação e valide:

1. login e aceite de LGPD;
2. acesso de usuário comum e administrador;
3. carregamento das abas principais;
4. carregamento das nove subabas de Auditoria;
5. abertura de um POP pelo catálogo;
6. importação de checklist com POP válido;
7. bloqueio de checklist sem POP legível;
8. seleção de POP alternativo;
9. lançamento manual;
10. alteração de status de uma NC;
11. exportação CSV;
12. troca de subabas durante um fluxo em andamento.

## Deploy no Streamlit Cloud

1. Conecte o repositório ao Streamlit Cloud.
2. Configure `app.py` como arquivo principal.
3. Configure os valores de `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `users`, `admins` e `session_secret` em **Manage app → Settings → Secrets**.
4. Confirme que `requirements.txt` está na raiz do projeto.
5. Publique ou reinicie a aplicação.
6. Teste a leitura de um PDF do Google Drive com link público.

O arquivo `.streamlit/secrets.toml` local não deve ser enviado ao repositório. Em caso de exposição de uma chave, senha ou token, faça a rotação imediatamente no serviço correspondente.

## Solução de problemas

### `ModuleNotFoundError: pdfplumber`

Instale as dependências novamente:

```bash
python -m pip install -r requirements.txt
```

### `Biblioteca PyPDF2 não instalada`

Confirme que `PyPDF2>=3.0.1` está no ambiente usado pelo Streamlit Cloud ou pelo ambiente local e reinicie a aplicação.

### POP não pode ser auditado

Verifique:

- se o processo possui link em **Link Documento**;
- se o arquivo está compartilhado como leitor para qualquer pessoa com o link;
- se o link aponta para um PDF;
- se o PDF possui texto selecionável;
- se o POP correto foi escolhido manualmente.

### Frente sem POP

Isso é um bloqueio intencional. Cadastre o POP correspondente com link legível ou selecione explicitamente outro POP correto. O sistema não cria vínculo por aproximação.

### Dados antigos não aparecem imediatamente

Use o botão de atualização disponível na aplicação ou recarregue a página. Após operações de gravação, o próprio sistema limpa o cache e recarrega os dados.

## Escopo de alterações

Processos, Novo Processo e Gerenciar compartilham o catálogo de processos e os links dos POPs com a Auditoria, mas o fluxo de auditoria mantém suas próprias regras de análise, vínculo, persistência e exportação. Alterações específicas da Auditoria devem evitar mudanças visuais ou funcionais desnecessárias nas outras áreas do sistema.
